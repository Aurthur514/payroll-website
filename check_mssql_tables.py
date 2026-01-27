from app import app, db
from database_config import get_database_uri
from sqlalchemy import text

print('Database URI:', get_database_uri())

with app.app_context():
    try:
        # Check what tables exist
        result = db.session.execute(text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"))
        tables = [row[0] for row in result]
        print('MS SQL tables:', tables)

        # Check table schemas
        for table in tables:
            print(f"\n{table} columns:")
            try:
                result = db.session.execute(text(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}' ORDER BY ORDINAL_POSITION"))
                for row in result:
                    print(f"  {row[0]} ({row[1]})")
            except Exception as e:
                print(f"  Error getting columns: {e}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()