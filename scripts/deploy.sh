#!/bin/bash
# deploy.sh

# Exit on errors
set -e

# Navigate to the directory of the script to ensure consistent paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env located one level up from the script directory
source "$SCRIPT_DIR/../.env"

# Generate the final SQL script by substituting placeholders
sed -e "s/{{ADMIN_USER_PASS}}/$ADMIN_USER_PASS/g" \
    -e "s/{{MANAGER_USER_PASS}}/$MANAGER_USER_PASS/g" \
    -e "s/{{REGULAR_USER_PASS}}/$REGULAR_USER_PASS/g" \
    "$SCRIPT_DIR/lol_schema_setup_template.sql" > "$SCRIPT_DIR/lol_schema_setup.sql"

# Connect as SYSDBA to the PDB and run the script
sqlplus sys/$SYS_PASS@$ORA_HOST:$ORA_PORT/$ORA_SERVICE as sysdba @"$SCRIPT_DIR/lol_schema_setup.sql"

echo "Deployment script completed. The schema is now set up in $ORA_SERVICE."