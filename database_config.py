# Database Configuration
import os

def get_database_uri():
    """Get the database URI from environment or default to SQLite"""
    return os.environ.get('DATABASE_URL', 'sqlite:///payroll.db')