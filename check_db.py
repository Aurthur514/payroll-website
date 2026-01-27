import sqlite3
import os

if os.path.exists('payroll.db'):
    conn = sqlite3.connect('payroll.db')
    cursor = conn.cursor()

    # Check user table schema
    cursor.execute("PRAGMA table_info(user)")
    user_columns = cursor.fetchall()
    print('User table columns:')
    for col in user_columns:
        print(f"  {col[1]} ({col[2]})")

    # Check employee_details table schema
    cursor.execute("PRAGMA table_info(employee_details)")
    emp_columns = cursor.fetchall()
    print('\nEmployee_details table columns:')
    for col in emp_columns:
        print(f"  {col[1]} ({col[2]})")

    conn.close()
else:
    print('payroll.db does not exist')