#!/bin/sh
set -eu

# Prepare the root-owned named volume before dropping privileges.
mkdir -p /data
chown -R writespace:writespace /data
exec su -s /bin/sh writespace -c 'exec uvicorn app.main:app --host 0.0.0.0 --port 8000'
