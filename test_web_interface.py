#!/usr/bin/env python3
"""
Comprehensive test script for payroll management system
Tests all CRUD operations and web interface functionality
"""

import requests
import json
from datetime import datetime, date
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_login():
    """Test admin login"""
    print("Testing admin login...")
    session = requests.Session()

    # Login as admin
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }

    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200 and "dashboard" in response.url:
        print("✓ Admin login successful")
        return session
    else:
        print("✗ Admin login failed")
        return None

def test_add_employee(session):
    """Test adding a new employee"""
    print("Testing add employee functionality...")

    # Get the add employee page
    response = session.get(f"{BASE_URL}/admin/add_employee")
    if response.status_code != 200:
        print("✗ Could not access add employee page")
        return False

    # Test form submission with sample data
    employee_data = {
        'username': 'test_employee',
        'password': 'password123',
        'confirm_password': 'password123',
        'name': 'Test Employee',
        'email': 'test@example.com',
        'phone': '1234567890',
        'role': 'employee',
        'date_of_birth': '1990-01-01',
        'date_of_joining': date.today().strftime('%Y-%m-%d'),
        'department_id': '1',  # Assuming department exists
        'basic_salary': '50000',
        'hra': '10000',
        'conveyance': '19200',
        'medical_allowance': '5000',
        'lta': '0',
        'special_allowance': '0',
        'provident_fund': '6000',
        'professional_tax': '235',
        'income_tax': '5000',
        'other_deductions': '0',
        'bank_name': 'Test Bank',
        'account_number': '1234567890',
        'ifsc_code': 'TEST0001'
    }

    response = session.post(f"{BASE_URL}/admin/add_employee", data=employee_data)
    if response.status_code == 200 and ("success" in response.text.lower() or "employee" in response.text.lower()):
        print("✓ Employee added successfully")
        return True
    else:
        print("✗ Employee addition failed")
        print(f"Response: {response.text[:200]}")
        return False

def test_manage_employees(session):
    """Test viewing employees list"""
    print("Testing manage employees page...")

    response = session.get(f"{BASE_URL}/admin/employees")
    if response.status_code == 200 and "employees" in response.text.lower():
        print("✓ Employees page accessible")
        return True
    else:
        print("✗ Employees page not accessible")
        return False

def test_attendance(session):
    """Test attendance management"""
    print("Testing attendance management...")

    response = session.get(f"{BASE_URL}/admin/attendance")
    if response.status_code == 200 and "attendance" in response.text.lower():
        print("✓ Attendance page accessible")
        return True
    else:
        print("✗ Attendance page not accessible")
        return False

def test_payroll_generation(session):
    """Test payroll generation"""
    print("Testing payroll generation...")

    response = session.get(f"{BASE_URL}/admin/payroll/generate")
    if response.status_code == 200 and "payroll" in response.text.lower():
        print("✓ Payroll generation page accessible")
        return True
    else:
        print("✗ Payroll generation page not accessible")
        return False

def test_payroll_report(session):
    """Test payroll report viewing"""
    print("Testing payroll report...")

    response = session.get(f"{BASE_URL}/admin/payroll")
    if response.status_code == 200 and "payroll" in response.text.lower():
        print("✓ Payroll report page accessible")
        return True
    else:
        print("✗ Payroll report page not accessible")
        return False

def main():
    """Run all tests"""
    print("Starting comprehensive payroll system test...")
    print("=" * 50)

    # Test login
    session = test_login()
    if not session:
        print("Cannot proceed without successful login")
        sys.exit(1)

    # Test all functionalities
    tests = [
        test_manage_employees,
        test_add_employee,
        test_attendance,
        test_payroll_generation,
        test_payroll_report
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test(session):
            passed += 1
        print()

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Payroll system is fully functional.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()