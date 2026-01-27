#!/usr/bin/env python3
"""
MS SQL Server Migration Script for Payroll Management System
Migrates data from SQLite to MS SQL Server
"""

import pyodbc
import sqlite3
import json
from datetime import datetime, date
import os
from database_config import MSSQL_CONFIG

def get_sqlite_connection():
    """Connect to SQLite database"""
    return sqlite3.connect('payroll.db')

def get_mssql_connection():
    """Connect to MS SQL Server"""
    conn_str = (
        f"DRIVER={MSSQL_CONFIG['driver']};"
        f"SERVER={MSSQL_CONFIG['server']};"
        f"DATABASE={MSSQL_CONFIG['database']};"
        f"UID={MSSQL_CONFIG['username']};"
        f"PWD={MSSQL_CONFIG['password']};"
    )
    return pyodbc.connect(conn_str)

def create_mssql_database():
    """Create the MS SQL database if it doesn't exist"""
    print("Creating MS SQL database...")

    # Connect to master database first with autocommit
    conn_str = (
        f"DRIVER={MSSQL_CONFIG['driver']};"
        f"SERVER={MSSQL_CONFIG['server']};"
        f"DATABASE=master;"
        f"UID={MSSQL_CONFIG['username']};"
        f"PWD={MSSQL_CONFIG['password']};"
    )

    conn = pyodbc.connect(conn_str, autocommit=True)  # Enable autocommit
    cursor = conn.cursor()

    # Create database if it doesn't exist
    cursor.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{MSSQL_CONFIG['database']}') CREATE DATABASE [{MSSQL_CONFIG['database']}]")

    conn.close()
    print(f"Database '{MSSQL_CONFIG['database']}' created or already exists.")

def export_sqlite_data():
    """Export all data from SQLite database"""
    print("Exporting data from SQLite database...")

    sqlite_conn = get_sqlite_connection()
    sqlite_cursor = sqlite_conn.cursor()

    data = {}

    # Get all table names
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    print(f"Found tables: {tables}")

    # Export each table
    for table in tables:
        try:
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            columns = [col[0] for col in sqlite_cursor.description]
            rows = sqlite_cursor.fetchall()

            # Convert to dict format
            table_data = []
            for row in rows:
                table_data.append(dict(zip(columns, row)))

            data[table] = table_data
            print(f"Exported {len(table_data)} records from {table}")

        except Exception as e:
            print(f"Error exporting {table}: {e}")

    sqlite_conn.close()

    # Save to JSON file as backup
    with open('sqlite_backup.json', 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Exported {sum(len(v) for v in data.values())} records from SQLite")
    return data

def import_to_mssql(data):
    """Import data into MS SQL Server"""
    print("Importing data to MS SQL Server...")

    # First, create tables using SQLAlchemy
    print("Creating tables in MS SQL Server...")
    from app import app, db
    with app.app_context():
        db.create_all()
    print("Tables created successfully")

    mssql_conn = get_mssql_connection()
    mssql_cursor = mssql_conn.cursor()

    try:
        # Import data for each table
        for table_name, records in data.items():
            if not records:  # Skip empty tables
                continue

            print(f"Importing {len(records)} records to {table_name}...")

            # Get column names from first record
            columns = list(records[0].keys())
            column_list = ', '.join(columns)
            placeholders = ', '.join(['?' for _ in columns])

            # Handle special table mappings
            if table_name == 'user':
                target_table = 'user'  # Keep as 'user', not 'users'
                # Map hire_date to hire_date (no change needed)
                for record in records:
                    if 'date_of_joining' in record and 'hire_date' not in record:
                        record['hire_date'] = record.pop('date_of_joining')
            elif table_name == 'payroll_record':
                target_table = 'payroll_record'  # Keep as is
            else:
                target_table = table_name

            # Insert records
            for record in records:
                try:
                    # Enable IDENTITY_INSERT for tables with identity columns
                    identity_tables = ['department', 'user', 'employee_details', 'attendance', 'leave', 'payroll_record', 'audit_log']
                    if target_table in identity_tables:
                        mssql_cursor.execute(f"SET IDENTITY_INSERT [{target_table}] ON")

                    # Process values, handling datetime columns specially
                    values = []
                    insert_columns = []
                    placeholders_list = []

                    for col in columns:
                        val = record.get(col)

                        # Skip datetime columns that might cause issues, let them use defaults
                        if 'created_at' in col.lower() or 'updated_at' in col.lower():
                            continue

                        # Convert datetime strings if needed
                        if isinstance(val, str) and len(val) > 10 and ('-' in val or '/' in val):
                            # Try to convert to proper datetime format
                            try:
                                from datetime import datetime
                                # Handle various datetime formats
                                if 'T' in val:
                                    val = val.split('T')[0] + ' ' + val.split('T')[1].split('.')[0]
                                elif len(val.split(' ')) == 1:
                                    val = val + ' 00:00:00'
                                # val should now be in 'YYYY-MM-DD HH:MM:SS' format
                            except:
                                val = None  # Use NULL for problematic dates

                        insert_columns.append(col)
                        placeholders_list.append('?')
                        values.append(val)

                    if insert_columns:  # Only insert if we have columns
                        column_list = ', '.join(insert_columns)
                        placeholders = ', '.join(placeholders_list)
                        sql = f"INSERT INTO [{target_table}] ({column_list}) VALUES ({placeholders})"
                        mssql_cursor.execute(sql, values)

                    # Disable IDENTITY_INSERT
                    if target_table in identity_tables:
                        mssql_cursor.execute(f"SET IDENTITY_INSERT [{target_table}] OFF")

                except Exception as e:
                    print(f"Error inserting into {target_table}: {e}")
                    print(f"Record: {record}")
                    raise

        mssql_conn.commit()
        print(f"Successfully imported {sum(len(v) for v in data.values())} records to MS SQL Server")

    except Exception as e:
        print(f"Error during import: {e}")
        mssql_conn.rollback()
        raise
    finally:
        mssql_conn.close()

def update_app_config():
    """Update the Flask app configuration to use MS SQL Server"""
    print("Updating app.py configuration...")

    # Read current app.py
    with open('app.py', 'r') as f:
        content = f.read()

    # Update the database URI
    old_uri = "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payroll.db'"
    new_uri = f"app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect=' + urllib.parse.quote_plus('DRIVER={{{MSSQL_CONFIG['driver']}}};SERVER={MSSQL_CONFIG['server']};DATABASE={MSSQL_CONFIG['database']};UID={MSSQL_CONFIG['username']};PWD={MSSQL_CONFIG['password']}')"

    if old_uri in content:
        content = content.replace(old_uri, new_uri)

        # Add urllib import if not present
        if 'import urllib' not in content:
            content = content.replace('import calendar\nimport json', 'import calendar\nimport json\nimport urllib.parse')

        # Write back
        with open('app.py', 'w') as f:
            f.write(content)

        print("Updated app.py to use MS SQL Server")
    else:
        print("Could not find database URI in app.py")

def main():
    """Main migration function"""
    print("=== PAYROLL SYSTEM MS SQL MIGRATION ===")
    print("This script will migrate your data from SQLite to MS SQL Server")
    print()

    # Check if SQLite database exists
    if not os.path.exists('payroll.db'):
        print("❌ SQLite database 'payroll.db' not found!")
        return

    try:
        # Step 1: Create MS SQL database
        create_mssql_database()

        # Step 2: Export data from SQLite
        data = export_sqlite_data()

        # Step 3: Import data to MS SQL
        import_to_mssql(data)

        # Step 4: Update app configuration
        update_app_config()

        print("\n✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Update the MSSQL_CONFIG in this script with your actual server details")
        print("2. Test the application: python app.py")
        print("3. If everything works, you can delete the old 'payroll.db' file")
        print("4. A backup of your SQLite data is saved in 'sqlite_backup.json'")

    except Exception as e:
        print(f"\n❌ MIGRATION FAILED: {e}")
        print("Your original SQLite database is unchanged.")
        print("Check the error message above and fix any configuration issues.")

if __name__ == "__main__":
    main()