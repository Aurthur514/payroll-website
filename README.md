# Payroll Management System

A web-based payroll management system built with Flask that handles employee attendance tracking and automatic salary calculations.

## Features

### Admin Features
- **User Management**: Add, edit, and manage employee accounts
- **Salary Configuration**: Set basic salaries and hourly rates for employees
- **Payroll Reports**: View monthly payroll calculations for all employees
- **Employee Types**: Support for both monthly salaried and hourly employees

### Employee Features
- **Daily Attendance**: Mark daily attendance with a simple checkbox
- **Hour Tracking**: Enter worked hours for hourly employees
- **Dashboard**: View personal attendance status
- **Privacy**: No access to salary information or other employees' data

### Automatic Calculations
- **Monthly Salary**: Basic salary × (days present / total days in month)
- **Hourly Salary**: Hourly rate × total hours worked in the month
- **Real-time Updates**: Calculations update automatically based on attendance

## Installation

1. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Open your browser and go to `http://localhost:5000`

## Default Admin Account

- **Username**: admin
- **Password**: admin123

## Usage

### For Admins
1. Login with admin credentials
2. Add employees with their salary details
3. Monitor attendance and view payroll reports

### For Employees
1. Login with provided credentials
2. Mark daily attendance using the checkbox
3. Enter hours worked (if hourly employee)
4. View attendance status

## Security Features

- Password hashing for secure authentication
- Role-based access control (Admin vs Employee)
- Session management for user authentication
- Input validation and CSRF protection

## Database

The application uses SQLite database (`payroll.db`) for data storage. The database is automatically created when the application runs for the first time.

## Technologies Used

- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite
- **Frontend**: Bootstrap 5, HTML, CSS
- **Forms**: WTForms for form handling and validation
- **Authentication**: Werkzeug for password hashing

## Project Structure

```
payroll-system/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── admin_dashboard.html
│   ├── add_employee.html
│   ├── edit_employee.html
│   ├── payroll_report.html
│   ├── employee_dashboard.html
│   └── mark_attendance.html
├── static/               # Static files (CSS, JS)
│   └── style.css
└── payroll.db           # SQLite database (created automatically)
```

## API Endpoints

- `/` - Home (redirects to login or dashboard)
- `/login` - User login
- `/logout` - User logout
- `/admin` - Admin dashboard
- `/admin/add_employee` - Add new employee
- `/admin/edit_employee/<id>` - Edit employee details
- `/admin/payroll_report` - View payroll report
- `/employee` - Employee dashboard
- `/employee/attendance` - Mark attendance

## Future Enhancements

- Email notifications for attendance reminders
- Export payroll reports to PDF/Excel
- Multi-month payroll history
- Leave management system
- Integration with payment gateways