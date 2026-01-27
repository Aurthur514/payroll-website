from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, FloatField, IntegerField, SubmitField, TextAreaField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time, timedelta
import calendar
import json
import urllib.parse

# Import models
from models import db, User, EmployeeDetails, Attendance, Department, Leave, PayrollRecord, AuditLog, Advance
from database_config import get_database_uri

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.context_processor
def inject_current_user():
    if 'user_id' in session:
        return {'current_user': User.query.get(session['user_id'])}
    return {'current_user': None}
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class EmployeeForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    hire_date = DateField('Hire Date', validators=[Optional()])
    role = SelectField('Role', choices=[('employee', 'Employee'), ('manager', 'Manager'), ('admin', 'Admin')],
                      validators=[DataRequired()])
    basic_salary = FloatField('Basic Salary', validators=[DataRequired()])
    is_hourly = BooleanField('Hourly Employee')
    hourly_rate = FloatField('Hourly Rate (if applicable)')
    overtime_rate = FloatField('Overtime Rate')
    bank_account = StringField('Bank Account Number')
    bank_name = StringField('Bank Name')
    submit = SubmitField('Add Employee')

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Add Department')

class AttendanceForm(FlaskForm):
    present = BooleanField('Present Today')
    hours_worked = FloatField('Hours Worked (if hourly)')
    check_in_time = StringField('Check-in Time (HH:MM)')
    check_out_time = StringField('Check-out Time (HH:MM)')
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit Attendance')

class LeaveForm(FlaskForm):
    leave_type = SelectField('Leave Type', choices=[
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation'),
        ('personal', 'Personal'),
        ('maternity', 'Maternity'),
        ('paternity', 'Paternity')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    reason = TextAreaField('Reason', validators=[Optional()])
    submit = SubmitField('Submit Leave Request')

class PayrollForm(FlaskForm):
    pay_period_start = DateField('Pay Period Start', validators=[DataRequired()])
    pay_period_end = DateField('Pay Period End', validators=[DataRequired()])
    submit = SubmitField('Generate Payroll')

class AdvanceForm(FlaskForm):
    amount = FloatField('Advance Amount', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    advance_date = DateField('Advance Date', validators=[Optional()])
    deduction_type = SelectField('Deduction Type', choices=[
        ('installments', 'Monthly Installments'),
        ('single', 'Single Deduction')
    ], validators=[DataRequired()])
    installment_amount = FloatField('Monthly Installment Amount', validators=[Optional()])
    submit = SubmitField('Grant Advance')

# Routes
@app.route('/health')
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {'status': 'healthy', 'database': 'not_tested'}, 200

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('employee_dashboard'))

    employees = User.query.filter_by(role='employee').all()
    return render_template('admin_dashboard.html', employees=employees)

@app.route('/admin/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('employee_dashboard'))

    form = EmployeeForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'error')
            return render_template('add_employee.html', form=form)

        new_user = User(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            role='employee'
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()

        # Add employee details
        details = EmployeeDetails(
            user_id=new_user.id,
            basic_salary=form.basic_salary.data,
            is_hourly=form.is_hourly.data,
            hourly_rate=form.hourly_rate.data if form.is_hourly.data else None
        )
        db.session.add(details)
        db.session.commit()

        flash('Employee added successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_employee.html', form=form)

@app.route('/admin/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('employee_dashboard'))

    employee = User.query.get_or_404(employee_id)
    details = employee.details[0] if employee.details else None

    if request.method == 'POST':
        employee.name = request.form['name']
        employee.email = request.form['email']
        details.basic_salary = float(request.form['basic_salary'])
        details.is_hourly = 'is_hourly' in request.form
        details.hourly_rate = float(request.form.get('hourly_rate', 0)) if details.is_hourly else None

        db.session.commit()
        flash('Employee updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_employee.html', employee=employee, details=details)

@app.route('/admin/payroll_report')
def payroll_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        return redirect(url_for('employee_dashboard'))

    current_month = datetime.now().month
    current_year = datetime.now().year
    _, last_day = calendar.monthrange(current_year, current_month)

    employees = User.query.filter_by(role='employee').all()
    report = []

    for emp in employees:
        details = emp.details[0] if emp.details else None
        if not details:
            continue

        # Get attendance for current month
        attendance_records = Attendance.query.filter(
            Attendance.user_id == emp.id,
            Attendance.date >= date(current_year, current_month, 1),
            Attendance.date <= date(current_year, current_month, last_day)
        ).all()

        days_present = sum(1 for a in attendance_records if a.present)
        total_hours = sum(a.hours_worked for a in attendance_records)

        if details.is_hourly:
            salary = total_hours * details.hourly_rate
        else:
            salary = details.basic_salary * (days_present / last_day)

        report.append({
            'employee': emp,
            'days_present': days_present,
            'total_days': last_day,
            'total_hours': total_hours,
            'salary': round(salary, 2)
        })

    return render_template('payroll_report.html', report=report, month=current_month, year=current_year)

@app.route('/employee')
def employee_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    today = date.today()
    attendance = Attendance.query.filter_by(user_id=user.id, date=today).first()

    return render_template('employee_dashboard.html', user=user, attendance=attendance, today=today)

@app.route('/employee/attendance', methods=['GET', 'POST'])
def mark_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))

    today = date.today()
    attendance = Attendance.query.filter_by(user_id=user.id, date=today).first()

    if attendance:
        flash('Attendance already marked for today.', 'info')
        return redirect(url_for('employee_dashboard'))

    form = AttendanceForm()
    details = user.details[0] if user.details else None

    if form.validate_on_submit():
        new_attendance = Attendance(
            user_id=user.id,
            date=today,
            present=form.present.data,
            hours_worked=form.hours_worked.data if details and details.is_hourly else 0.0
        )
        db.session.add(new_attendance)
        db.session.commit()
        flash('Attendance marked successfully.', 'success')
        return redirect(url_for('employee_dashboard'))

    return render_template('mark_attendance.html', form=form, details=details)

# CRUD Routes for Departments
@app.route('/admin/departments')
def manage_departments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/admin/departments/add', methods=['GET', 'POST'])
def add_department():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    form = DepartmentForm()
    if form.validate_on_submit():
        department = Department.create(
            name=form.name.data,
            description=form.description.data
        )
        flash('Department added successfully.', 'success')
        return redirect(url_for('manage_departments'))

    return render_template('add_department.html', form=form)

@app.route('/admin/departments/edit/<int:dept_id>', methods=['GET', 'POST'])
def edit_department(dept_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    department = Department.query.get_or_404(dept_id)

    if request.method == 'POST':
        department.update(
            name=request.form['name'],
            description=request.form.get('description', '')
        )
        flash('Department updated successfully.', 'success')
        return redirect(url_for('manage_departments'))

    return render_template('edit_department.html', department=department)

@app.route('/admin/departments/delete/<int:dept_id>', methods=['POST'])
def delete_department(dept_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    department = Department.query.get_or_404(dept_id)
    department.delete()
    flash('Department deleted successfully.', 'success')
    return redirect(url_for('manage_departments'))

# Enhanced Employee CRUD
@app.route('/admin/employees')
def manage_employees():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_manager():
        return redirect(url_for('employee_dashboard'))

    employees = User.query.filter_by(role='employee').all()
    return render_template('employees.html', employees=employees)

@app.route('/admin/employees/add', methods=['GET', 'POST'])
def add_employee_new():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    form = EmployeeForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'error')
            return render_template('add_employee.html', form=form)

        new_user = User(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            date_of_birth=form.date_of_birth.data,
            hire_date=form.hire_date.data or date.today(),
            role=form.role.data
        )
        new_user.set_password(form.password.data)
        new_user.save()

        # Add employee details
        details = EmployeeDetails(
            user_id=new_user.id,
            basic_salary=form.basic_salary.data,
            is_hourly=form.is_hourly.data,
            hourly_rate=form.hourly_rate.data if form.is_hourly.data else None,
            overtime_rate=form.overtime_rate.data or (form.hourly_rate.data * 1.5 if form.is_hourly.data else 0),
            tax_rate=form.tax_rate.data or 0,
            insurance_deduction=form.insurance_deduction.data or 0,
            other_deductions=form.other_deductions.data or 0,
            bank_account=form.bank_account.data,
            bank_name=form.bank_name.data
        )
        details.save()

        flash('Employee added successfully.', 'success')
        return redirect(url_for('manage_employees'))

    return render_template('add_employee.html', form=form)

@app.route('/admin/employees/edit/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee_new(emp_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    employee = User.query.get_or_404(emp_id)
    details = employee.employee_details

    if request.method == 'POST':
        employee.update(
            name=request.form['name'],
            email=request.form['email'],
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            role=request.form['role']
        )

        if details:
            details.update(
                basic_salary=float(request.form['basic_salary']),
                is_hourly='is_hourly' in request.form,
                hourly_rate=float(request.form.get('hourly_rate', 0)) if 'is_hourly' in request.form else None,
                tax_rate=float(request.form.get('tax_rate', 0)),
                insurance_deduction=float(request.form.get('insurance_deduction', 0)),
                other_deductions=float(request.form.get('other_deductions', 0)),
                bank_account=request.form.get('bank_account'),
                bank_name=request.form.get('bank_name')
            )

        flash('Employee updated successfully.', 'success')
        return redirect(url_for('manage_employees'))

    return render_template('edit_employee.html', employee=employee, details=details)

@app.route('/admin/employees/delete/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    employee = User.query.get_or_404(emp_id)
    employee.delete()
    flash('Employee deleted successfully.', 'success')
    return redirect(url_for('manage_employees'))

# Attendance Management
@app.route('/admin/attendance')
def manage_attendance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_manager():
        return redirect(url_for('employee_dashboard'))

    today = date.today()
    attendances = Attendance.query.filter_by(date=today).all()
    employees = User.query.filter_by(role='employee').all()

    # Create a dict of employee_id -> attendance
    attendance_dict = {a.user_id: a for a in attendances}

    return render_template('attendance.html', employees=employees, attendance_dict=attendance_dict, today=today)

@app.route('/admin/attendance/<int:emp_id>', methods=['POST'])
def update_attendance(emp_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_manager():
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    attendance_date = date.fromisoformat(data['date'])

    attendance = Attendance.query.filter_by(user_id=emp_id, date=attendance_date).first()
    if attendance:
        attendance.update(
            present=data['present'],
            hours_worked=float(data.get('hours_worked', 0)),
            notes=data.get('notes', '')
        )
    else:
        Attendance.create(
            user_id=emp_id,
            date=attendance_date,
            present=data['present'],
            hours_worked=float(data.get('hours_worked', 0)),
            notes=data.get('notes', '')
        )

    return jsonify({'success': True})

# Leave Management
@app.route('/admin/leaves')
def manage_leaves():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_manager():
        return redirect(url_for('employee_dashboard'))

    leaves = Leave.query.order_by(Leave.created_at.desc()).all()
    return render_template('leaves.html', leaves=leaves)

@app.route('/admin/leaves/approve/<int:leave_id>', methods=['POST'])
def approve_leave(leave_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_manager():
        return jsonify({'error': 'Unauthorized'}), 403

    leave = Leave.query.get_or_404(leave_id)
    leave.update(
        status='approved',
        approved_by=user.id,
        approved_at=datetime.utcnow()
    )

    return jsonify({'success': True})

@app.route('/admin/leaves/reject/<int:leave_id>', methods=['POST'])
def reject_leave(leave_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_manager():
        return jsonify({'error': 'Unauthorized'}), 403

    leave = Leave.query.get_or_404(leave_id)
    leave.update(status='rejected')

    return jsonify({'success': True})

# Payroll Management
@app.route('/admin/payroll/generate', methods=['GET', 'POST'])
def generate_payroll():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    form = PayrollForm()
    if form.validate_on_submit():
        pay_period_start = form.pay_period_start.data
        pay_period_end = form.pay_period_end.data

        # Check if payroll already exists for this period
        existing_payroll = PayrollRecord.query.filter_by(
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end
        ).first()
        if existing_payroll:
            flash('Payroll already generated for this period.', 'warning')
            return redirect(url_for('payroll_report_new'))

        employees = User.query.filter_by(role='employee').all()

        for emp in employees:
            details = emp.employee_details
            if not details:
                continue

            # Get attendance for the pay period
            attendances = Attendance.query.filter(
                Attendance.user_id == emp.id,
                Attendance.date >= pay_period_start,
                Attendance.date <= pay_period_end
            ).all()

            days_present = sum(1 for a in attendances if a.present)
            total_hours = sum(a.hours_worked for a in attendances)

            # Calculate total working days in the period
            from datetime import timedelta
            total_days = (pay_period_end - pay_period_start).days + 1

            salary_calc = details.calculate_monthly_salary(days_present, total_days, total_hours)

            # Apply advance deductions
            advance_deductions = 0.0
            for advance in emp.advances:
                if advance.status == 'active':
                    deduction = advance.calculate_monthly_deduction()
                    if deduction > 0:
                        advance.apply_deduction(deduction)
                        advance_deductions += deduction

            # Recalculate net salary after applying advance deductions
            net_salary = salary_calc['gross_salary'] - advance_deductions

            PayrollRecord.create(
                user_id=emp.id,
                pay_period_start=pay_period_start,
                pay_period_end=pay_period_end,
                days_present=days_present,
                total_days=total_days,
                hours_worked=total_hours,
                gross_salary=salary_calc['gross_salary'],
                deductions=advance_deductions,
                net_salary=net_salary
            )

        flash('Payroll generated successfully.', 'success')
        return redirect(url_for('payroll_report'))

    return render_template('generate_payroll.html', form=form)

@app.route('/admin/payroll')
def payroll_report_new():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    payroll_records = PayrollRecord.query.order_by(PayrollRecord.created_at.desc()).all()
    return render_template('payroll.html', payrolls=payroll_records)

@app.route('/admin/payroll/view/<int:payroll_id>')
def view_payroll(payroll_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    payroll = PayrollRecord.query.get_or_404(payroll_id)
    return render_template('view_payroll.html', payroll=payroll)

@app.route('/admin/payroll/mark_paid/<int:payroll_id>', methods=['POST'])
def mark_payroll_paid(payroll_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    payroll = PayrollRecord.query.get_or_404(payroll_id)
    payroll.status = 'paid'
    payroll.payment_date = date.today()
    payroll.save()

    return jsonify({'success': True})

# Advance Management Routes
@app.route('/admin/advances')
def manage_advances():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    advances = Advance.query.order_by(Advance.advance_date.desc()).all()
    return render_template('manage_advances.html', advances=advances)

@app.route('/admin/advance/create/<int:employee_id>', methods=['GET', 'POST'])
def create_advance(employee_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    employee = User.query.get_or_404(employee_id)
    form = AdvanceForm()

    if form.validate_on_submit():
        advance = Advance(
            employee_id=employee_id,
            amount=form.amount.data,
            description=form.description.data,
            advance_date=form.advance_date.data or date.today(),
            deduction_type=form.deduction_type.data,
            installment_amount=form.installment_amount.data if form.deduction_type.data == 'installments' else None,
            remaining_balance=form.amount.data
        )
        db.session.add(advance)
        db.session.commit()

        flash('Advance granted successfully.', 'success')
        return redirect(url_for('manage_advances'))

    return render_template('create_advance.html', form=form, employee=employee)

@app.route('/admin/advance/view/<int:advance_id>')
def view_advance(advance_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    advance = Advance.query.get_or_404(advance_id)
    return render_template('view_advance.html', advance=advance)

@app.route('/admin/advance/delete/<int:advance_id>', methods=['POST'])
def delete_advance(advance_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return redirect(url_for('employee_dashboard'))

    advance = Advance.query.get_or_404(advance_id)
    db.session.delete(advance)
    db.session.commit()

    flash('Advance deleted successfully.', 'success')
    return redirect(url_for('manage_advances'))

# Employee Routes
@app.route('/employee/leave', methods=['GET', 'POST'])
def request_leave():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.is_admin():
        return redirect(url_for('admin_dashboard'))

    form = LeaveForm()
    if form.validate_on_submit():
        # Calculate days requested
        start_date = form.start_date.data
        end_date = form.end_date.data
        days_requested = (end_date - start_date).days + 1

        leave = Leave.create(
            user_id=user.id,
            leave_type=form.leave_type.data,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=form.reason.data
        )

        flash('Leave request submitted successfully.', 'success')
        return redirect(url_for('employee_dashboard'))

    return render_template('request_leave.html', form=form)

@app.route('/employee/leaves')
def my_leaves():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.is_admin():
        return redirect(url_for('admin_dashboard'))

    leaves = Leave.query.filter_by(user_id=user.id).order_by(Leave.created_at.desc()).all()
    return render_template('my_leaves.html', leaves=leaves)

# API Endpoints
@app.route('/api/attendance/<int:emp_id>', methods=['GET'])
def get_employee_attendance(emp_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(session['user_id'])
    if not user.is_manager() and user.id != emp_id:
        return jsonify({'error': 'Unauthorized'}), 403

    month = int(request.args.get('month', datetime.now().month))
    year = int(request.args.get('year', datetime.now().year))

    _, last_day = calendar.monthrange(year, month)
    attendances = Attendance.query.filter(
        Attendance.user_id == emp_id,
        Attendance.date >= date(year, month, 1),
        Attendance.date <= date(year, month, last_day)
    ).all()

    attendance_data = {}
    for attendance in attendances:
        attendance_data[attendance.date.isoformat()] = {
            'present': attendance.present,
            'hours_worked': attendance.hours_worked,
            'notes': attendance.notes
        }

    return jsonify(attendance_data)

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.get(session['user_id'])
    if not user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403

    total_employees = User.query.filter_by(role='employee').count()
    present_today = Attendance.query.filter_by(date=date.today(), present=True).count()
    pending_leaves = Leave.query.filter_by(status='pending').count()
    # Count payroll records generated this month
    current_month = datetime.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    current_month_payroll = PayrollRecord.query.filter(
        PayrollRecord.created_at >= current_month,
        PayrollRecord.created_at < next_month
    ).count()

    return jsonify({
        'total_employees': total_employees,
        'present_today': present_today,
        'pending_leaves': pending_leaves,
        'payroll_generated': current_month_payroll > 0
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', name='Administrator', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=False)