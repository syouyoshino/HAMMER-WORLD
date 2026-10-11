#!/bin/sh
set -eu
stamp=$(date -u +%Y%m%dT%H%M%SZ)
exec /opt/hammer-world/.venv/bin/python -m app.cli backup "/var/lib/hammer-world/backups/campaign-${stamp}.dump"
