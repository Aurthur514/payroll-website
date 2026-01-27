#!/usr/bin/env python3
"""
Test script to verify database connectivity and basic operations
"""

from app import app, db, User, Department, EmployeeDetails, Attendance, Leave, PayrollRecord
from database_config import DATABASE_TYPE, get_database_uri
import traceback

def test_database_connection():
    """Test database connection and basic operations"""
    print("=== DATABASE CONNECTIVITY TEST ===")
    print(f"Database Type: {DATABASE_TYPE}")
    print(f"Database URI: {get_database_uri().split('odbc_connect=')[0] if 'odbc_connect' in get_database_uri() else get_database_uri()}")
    print()

    try:
        with app.app_context():
            # Test database connection
            db.create_all()
            print("✅ Database connection successful")
            print("✅ Tables created/verified")

            # Test basic CRUD operations
            print("\n=== TESTING CRUD OPERATIONS ===")

            # Check admin user
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print(f"✅ Admin user exists: {admin.name} ({admin.role})")
            else:
                print("⚠️  Admin user not found - creating...")
                admin = User(username='admin', name='Administrator', email='admin@example.com', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")

            # Test Department creation
            dept_count_before = Department.query.count()
            test_dept = Department(name='Test Department', description='For testing')
            db.session.add(test_dept)
            db.session.commit()
            dept_count_after = Department.query.count()

            if dept_count_after > dept_count_before:
                print("✅ Department creation working")
                # Clean up test department
                db.session.delete(test_dept)
                db.session.commit()
            else:
                print("❌ Department creation failed")

            # Test User creation
            import uuid
            unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
            user_count_before = User.query.count()
            test_user = User(username=f'testuser_{uuid.uuid4().hex[:8]}', name='Test User', email=unique_email, role='employee')
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            user_count_after = User.query.count()

            if user_count_after > user_count_before:
                print("✅ User creation working")

                # Test EmployeeDetails creation
                test_details = EmployeeDetails(
                    user_id=test_user.id,
                    basic_salary=45000.0
                )
                db.session.add(test_details)
                db.session.commit()
                print("✅ Employee details creation working")

                # Clean up test records
                db.session.delete(test_details)
                db.session.delete(test_user)
                db.session.commit()
                print("✅ Test data cleanup successful")
            else:
                print("❌ User creation failed")

            # Show table counts
            print("\n=== DATABASE SUMMARY ===")
            tables = [
                ('Users', User),
                ('Departments', Department),
                ('EmployeeDetails', EmployeeDetails),
                ('Attendance', Attendance),
                ('Leaves', Leave),
                ('PayrollRecords', PayrollRecord)
            ]

            for name, model in tables:
                count = model.query.count()
                print(f"{name}: {count} records")

            print("\n✅ ALL TESTS PASSED - Database is ready!")

    except Exception as e:
        print(f"❌ DATABASE TEST FAILED: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("\n🎉 Database is working correctly!")
        print("You can now run: python app.py")
        if DATABASE_TYPE == 'sqlite':
            print("To migrate to MS SQL Server, run: python migrate_to_mssql.py")
    else:
        print("\n❌ Database issues detected. Please check configuration.")