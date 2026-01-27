# Database Configuration
# Choose your database type: 'sqlite' or 'mssql'
DATABASE_TYPE = 'sqlite'  # Default to SQLite for simple deployment

# SQLite Configuration
SQLITE_URI = 'sqlite:///payroll.db'

# MS SQL Server Configuration (for Docker setup)
MSSQL_CONFIG = {
    'server': 'localhost',  # Docker container runs on localhost
    'database': 'payroll_db',  # Database name (will be created)
    'username': 'SA',  # SQL Server system administrator
    'password': 'YourPassword123!',  # Same password as in Docker setup
    'driver': 'SQL Server'  # Using the available SQL Server driver
}

import urllib.parse

def get_database_uri():
    """Get the appropriate database URI based on configuration"""
    if DATABASE_TYPE == 'mssql':
        # MS SQL Server connection string
        conn_str = (
            f"DRIVER={MSSQL_CONFIG['driver']};"
            f"SERVER={MSSQL_CONFIG['server']};"
            f"DATABASE={MSSQL_CONFIG['database']};"
            f"UID={MSSQL_CONFIG['username']};"
            f"PWD={MSSQL_CONFIG['password']};"
        )
        return f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"
    else:
        # SQLite (default)
        return SQLITE_URI