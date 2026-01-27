#!/usr/bin/env python3
"""
Test MS SQL Server connection
"""

import pyodbc
from database_config import MSSQL_CONFIG

def test_sqlserver_connection():
    """Test connection to SQL Server"""
    print("Testing MS SQL Server connection...")

    try:
        # Connection string
        conn_str = (
            f"DRIVER={MSSQL_CONFIG['driver']};"
            f"SERVER={MSSQL_CONFIG['server']};"
            f"DATABASE=master;"  # Connect to master database first
            f"UID={MSSQL_CONFIG['username']};"
            f"PWD={MSSQL_CONFIG['password']};"
        )

        print(f"Connecting to: {MSSQL_CONFIG['server']}:1433")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Test query
        cursor.execute("SELECT @@VERSION as version")
        row = cursor.fetchone()
        print("✅ SQL Server connection successful!")
        print(f"Version: {row.version[:50]}...")

        # Check if our database exists
        cursor.execute("SELECT name FROM sys.databases WHERE name = ?", MSSQL_CONFIG['database'])
        db_exists = cursor.fetchone()

        if db_exists:
            print(f"✅ Database '{MSSQL_CONFIG['database']}' exists")
        else:
            print(f"⚠️  Database '{MSSQL_CONFIG['database']}' does not exist yet")

        conn.close()
        return True

    except pyodbc.Error as e:
        print(f"❌ SQL Server connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure SQL Server is running: docker ps")
        print("2. Check if port 1433 is accessible")
        print("3. Verify password matches Docker setup")
        print("4. Install ODBC Driver 17 if missing")
        return False

if __name__ == "__main__":
    test_sqlserver_connection()