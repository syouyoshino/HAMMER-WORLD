# Local development and private deployment

PostgreSQL is the authoritative record. No domain or Drive connection is needed to run locally. Configure `WOLD_DATABASE_URL` with a PostgreSQL connection string; do not put credentials in source control. There is no SQLite write fallback.

## Local PostgreSQL

Use an existing PostgreSQL 17 server, or start the optional local container:

```sh
export HAMMER_DB_PASSWORD='a locally generated random password'
docker compose -f deploy/compose.yaml up -d
```

The database port binds only to loopback. Set `WOLD_DATABASE_URL` for that database in your shell or protected environment file. Install the Python requirements in a virtual environment, initialize the demo through the CLI, then start Uvicorn on `127.0.0.1:8000`. An SSH tunnel makes a remote Linux development instance available to a macOS browser without exposing its port publicly.

Do not run `docker compose down -v` against campaign data: that deletes the volume. Back up first. Database passwords are deployment inputs, never frontend configuration.

## Private HTTPS deployment

The templates in `deploy/` are preparation, not a live deployment. Choose a Linux host and domain when ready. Install PostgreSQL client tools, Python 3.12+, and Caddy. Use a dedicated `hammer-world` service account and place the application under `/opt/hammer-world` with a virtual environment.

Store runtime configuration in `/etc/hammer-world/hammer-world.env`, readable only by root and the service account. Configure:

- `WOLD_DATABASE_URL`: authoritative PostgreSQL connection; require TLS for a remote database.
- `WOLD_GM_TOKEN`: random GM credential, required in private mode.
- `WOLD_ACCESS_MODE=private`.
- Optional distinct `WOLD_PLAYER_TOKEN` and explicit `WOLD_PLAYER_CAMPAIGNS` allowlist.
- Optional Drive settings from `.env.example`; server-side only.

Set the Caddy service's `HAMMER_DOMAIN` variable, install `deploy/Caddyfile`, and use `hammer-world.service`. Uvicorn remains on loopback; Caddy handles HTTPS. Open only the intended HTTPS endpoint externally. The login shell contains no campaign state; player data requires authorization. Keep browser credentials in memory and reenter them after a reload.

Install the backup unit and timer after creating `/var/lib/hammer-world/backups` for the service account. The script writes dated custom-format backups; configure retention and a separate encrypted off-host copy for your host. Rehearse recovery into a separate empty PostgreSQL database before switching production to it. Never overwrite the running campaign to test restoration.

## Drive archives

Proposed real archive folder: **Wold — Campaign Archives**. Folder creation, credentials and upload verification remain deployment inputs. Existing Campaign Memory, State Ledger and Chronicle remain unchanged reference records. Demo uploads require a different folder and must never be mixed with the real campaign archive.

Database commits do not wait for Drive. Run the CLI archive sync job on demand; pending jobs retry without duplicating files. An archive becomes verified only after remote content and parent-folder checks pass. Configure credentials on the Linux server, not in chat or browser files.

After a successful authenticated upload, optionally install `hammer-world-archive.service` and its timer. Each pass claims at most 20 jobs; concurrent passes use database leases and stable Drive file IDs. The timer retries pending work without blocking turn commits. The first adapter accepts a server-managed access token; arrange its renewal on the server before relying on unattended archiving. Missing or expired credentials never count as successful synchronization.

## Verification before external access

Run the PostgreSQL integration suite, authorized/unauthorized player tests, historical reconstruction, backup recovery and browser workflows. Then verify the actual HTTPS endpoint and authenticated Drive uploads. Local and fake-adapter results do not establish live synchronization or deployed availability.
