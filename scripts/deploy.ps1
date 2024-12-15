# deploy.ps1

# Exit on errors
$ErrorActionPreference = "Stop"

# Set script directory
$SCRIPT_DIR = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition

# Load environment variables from .env file
$ENV_FILE = Join-Path $SCRIPT_DIR "..\.env"
if (Test-Path $ENV_FILE) {
    Get-Content $ENV_FILE | ForEach-Object {
        if ($_ -match "^(.*?)=(.*)$") {
            Set-Item -Path "env:$($matches[1])" -Value $matches[2]
        }
    }
}

# Replace placeholders in the SQL script
$TEMPLATE_FILE = Join-Path $SCRIPT_DIR "lol_schema_setup_template.sql"
$OUTPUT_FILE = Join-Path $SCRIPT_DIR "lol_schema_setup.sql"

(Get-Content $TEMPLATE_FILE) -replace "{{ADMIN_USER_PASS}}", $env:ADMIN_USER_PASS `
                             -replace "{{MANAGER_USER_PASS}}", $env:MANAGER_USER_PASS `
                             -replace "{{REGULAR_USER_PASS}}", $env:REGULAR_USER_PASS `
                             | Set-Content $OUTPUT_FILE


# Set NLS_LANG to English for consistent output
$env:NLS_LANG = "AMERICAN_AMERICA.UTF8"

# Run the SQL script
$SQLPLUS_CMD = "sqlplus sys/$env:SYS_PASS@${env:ORA_HOST}:${env:ORA_PORT}/${env:ORA_SERVICE} as sysdba @$OUTPUT_FILE"
Invoke-Expression $SQLPLUS_CMD

Write-Host "Deployment script completed. The schema is now set up in $env:ORA_SERVICE."