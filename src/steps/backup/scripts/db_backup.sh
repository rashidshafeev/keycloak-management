#!/bin/bash
# This script creates a backup of the Keycloak database using pg_dump.

# Load environment variables if you store credentials in a file (optional)
# source /opt/fawz/keycloak/config/.env

# Adjust the following variables as needed or read them from environment:
DB_NAME="keycloak"
DB_USER="keycloak"
# You might want to obtain the password in a secure manner. Here, we assume it's provided as an env variable.
# For example: export POSTGRES_PASSWORD=yourpassword
DB_PASSWORD="${POSTGRES_PASSWORD}"

BACKUP_DIR="/opt/fawz/backups/db"
mkdir -p "${BACKUP_DIR}"

TIMESTAMP=$(date +'%Y%m%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/keycloak_${TIMESTAMP}.sql"

# Run pg_dump: you may need to adjust host or add additional options.
PGPASSWORD="${DB_PASSWORD}" pg_dump -U "${DB_USER}" -h localhost "${DB_NAME}" > "${BACKUP_FILE}"

# Optionally, add retention logic here to remove old backups.

exit 0