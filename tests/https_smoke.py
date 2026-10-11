"""Optional local HTTPS/auth smoke: Playwright is not needed.

Requires WOLD_TEST_DATABASE_URL and Caddy on PATH (or WOLD_CADDY_EXECUTABLE).
Uses a temporary PostgreSQL schema and a temporary, explicitly trusted local CA.
"""
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import httpx
import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.store import Store


def port():
    with socket.socket() as connection:
        connection.bind(('127.0.0.1', 0))
        return connection.getsockname()[1]


def main():
    executable = os.environ.get('WOLD_CADDY_EXECUTABLE') or shutil.which('caddy')
    if not executable:
        raise RuntimeError('Caddy is required for the HTTPS smoke check')
    dsn = os.environ['WOLD_TEST_DATABASE_URL']
    schema = 'https_' + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    processes = []
    try:
        database = Store(dsn, schema=schema)
        database.create_demo()
        database.create_demo('restricted', seed=22)
        gm, player = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with tempfile.TemporaryDirectory() as scratch:
            directory = Path(scratch)
            environment = os.environ.copy()
            environment.update(WOLD_DATABASE_URL=dsn, WOLD_DB_SCHEMA=schema,
                               WOLD_ACCESS_MODE='private', WOLD_GM_TOKEN=gm,
                               WOLD_PLAYER_TOKEN=player, WOLD_PLAYER_CAMPAIGNS='demo',
                               XDG_DATA_HOME=str(directory / 'data'),
                               XDG_CONFIG_HOME=str(directory / 'config'))
            backend, secure = port(), port()
            configuration = directory / 'Caddyfile'
            configuration.write_text(
                '{\n admin off\n skip_install_trust\n auto_https disable_redirects\n}\n'
                f'https://localhost:{secure} {{\n bind 127.0.0.1\n tls internal\n'
                f' reverse_proxy 127.0.0.1:{backend}\n}}\n')
            with (directory / 'services.log').open('w') as log:
                processes.append(subprocess.Popen(
                    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                     '--port', str(backend), '--no-access-log'],
                    env=environment, stdout=log, stderr=log))
                processes.append(subprocess.Popen(
                    [executable, 'run', '--config', str(configuration)],
                    env=environment, stdout=log, stderr=log))
                certificate = directory / 'data/caddy/pki/authorities/local/root.crt'
                for _ in range(100):
                    if certificate.exists():
                        try:
                            with httpx.Client(verify=str(certificate)) as client:
                                if client.get(f'https://localhost:{secure}/').status_code == 200:
                                    break
                        except (httpx.ConnectError, httpx.HTTPError):
                            pass
                    time.sleep(.1)
                else:
                    raise RuntimeError('Local HTTPS startup failed; inspect service diagnostics')
                with httpx.Client(base_url=f'https://localhost:{secure}', verify=str(certificate)) as client:
                    assert client.get('/api/player/campaigns').status_code == 401
                    headers = {'Authorization': 'Bearer ' + player}
                    campaigns = client.get('/api/player/campaigns', headers=headers).json()
                    assert [item['id'] for item in campaigns] == ['demo']
                    assert client.get('/api/player/campaigns/restricted', headers=headers).status_code == 404
                    assert client.get('/api/admin/campaigns', headers=headers).status_code == 401
                    content = client.get('/api/player/campaigns/demo', headers=headers).text
                    assert '_private' not in content and 'seeded_marker' not in content
                    assert client.get('/api/admin/campaigns', headers={'Authorization': 'Bearer ' + gm}).status_code == 200
                print('PASS: trusted local HTTPS, private login boundary, campaign isolation and GM authorization')
                for process in reversed(processes):
                    process.terminate()
                    process.wait(timeout=10)
                processes.clear()
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=10)
        with psycopg.connect(dsn, autocommit=True) as connection:
            connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


if __name__ == '__main__':
    main()
