# MS SQL Server Migration Instructions
# ===================================

## Prerequisites:
# 1. Install Docker Desktop: https://www.docker.com/products/docker-desktop
# 2. Install ODBC Driver 17 for SQL Server (if not already installed)
# 3. Run the SQL Server Docker setup

## Quick Start with Docker:

### Step 1: Start SQL Server
```powershell
# Run the PowerShell setup script
.\setup_sqlserver.ps1
```

Or manually:
```powershell
# Pull and run SQL Server in Docker
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourPassword123!" -p 1433:1433 --name sqlserver -d mcr.microsoft.com/mssql/server:2022-latest
```

### Step 2: Test Connection
```bash
python test_sqlserver.py
```

### Step 3: Run Migration
```bash
python migrate_to_mssql.py
```

### Step 4: Switch to MS SQL
Edit `database_config.py`:
```python
DATABASE_TYPE = 'mssql'
```

### Step 5: Test Application
```bash
python app.py
```

### Step 1: Backup Your Current Data
# Your SQLite database (payroll.db) contains all your current data.
# The migration script will create a backup automatically.

### Step 2: Configure MS SQL Server Connection
# Edit database_config.py and update MSSQL_CONFIG with your server details:
#
# MSSQL_CONFIG = {
#     'server': 'localhost',          # Your SQL Server instance
#     'database': 'payroll_db',       # Database name (will be created)
#     'username': 'sa',               # SQL Server username
#     'password': 'YourPassword123!', # SQL Server password
#     'driver': '{ODBC Driver 17 for SQL Server}'
# }

### Step 3: Run the Migration
# python migrate_to_mssql.py
#
# This will:
# - Create the MS SQL database if it doesn't exist
# - Export all data from SQLite
# - Import data into MS SQL Server
# - Update app.py configuration
# - Create a backup file (sqlite_backup.json)

### Step 4: Switch to MS SQL Server
# After successful migration, edit database_config.py:
# DATABASE_TYPE = 'mssql'  # Change from 'sqlite' to 'mssql'

### Step 5: Test the Application
# python app.py
#
# Verify that all functionality works with MS SQL Server.

### Step 6: Clean Up (Optional)
# Once you're satisfied with the MS SQL setup:
# - Delete payroll.db (SQLite database)
# - Keep sqlite_backup.json as a backup

## Troubleshooting:

### Connection Issues:
# - Verify SQL Server is running
# - Check server name and instance
# - Ensure ODBC Driver 17 is installed
# - Test connection with SQL Server Management Studio

### Permission Issues:
# - Ensure the SQL Server user has CREATE DATABASE permission
# - Grant necessary permissions on the target database

### Driver Issues:
# - Install Microsoft ODBC Driver 17 for SQL Server
# - Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### Rollback:
# If migration fails, your original SQLite database remains unchanged.
# You can restore from sqlite_backup.json if needed.