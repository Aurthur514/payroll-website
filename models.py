from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import calendar

db = SQLAlchemy()

# CRUD Operations Classes
class CRUDMixin:
    """Mixin class providing basic CRUD operations"""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record"""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def get_by_id(cls, id):
        """Get record by ID"""
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """Get all records"""
        return cls.query.all()

    @classmethod
    def filter_by(cls, **kwargs):
        """Filter records by given criteria"""
        return cls.query.filter_by(**kwargs).all()

    def update(self, **kwargs):
        """Update record with given values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def delete(self):
        """Delete the record"""
        db.session.delete(self)
        db.session.commit()

    def save(self):
        """Save the record"""
        db.session.add(self)
        db.session.commit()
        return self

# Association table for many-to-many relationship between users and departments
user_departments = db.Table('user_departments',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('department_id', db.Integer, db.ForeignKey('department.id'), primary_key=True)
)

class Department(db.Model, CRUDMixin):
    """Department model for organizing employees"""
    __tablename__ = 'department'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    employees = db.relationship('User', secondary=user_departments, backref=db.backref('departments', lazy='dynamic'))

    def __repr__(self):
        return f'<Department {self.name}>'

class User(db.Model, CRUDMixin):
    """User model for authentication and basic user information"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # 'admin', 'manager', 'employee'
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    hire_date = db.Column(db.Date, default=date.today)
    daily_rate = db.Column(db.Float, nullable=True, default=0.0)  # Daily rate for salary calculation
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships

    attendances = db.relationship('Attendance', backref='user', lazy=True, foreign_keys='Attendance.user_id')
    payroll_records = db.relationship('MonthlyPayout', backref='user', lazy=True, foreign_keys='MonthlyPayout.user_id')
    leaves = db.relationship('Leave', backref='user', lazy=True, foreign_keys='Leave.user_id')
    advances = db.relationship('Advance', lazy=True, foreign_keys='Advance.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_manager(self):
        return self.role in ['admin', 'manager']

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class EmployeeDetails(db.Model, CRUDMixin):
    """Employee salary and work details"""
    __tablename__ = 'employee_details'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    basic_salary = db.Column(db.Float, nullable=False, default=0.0)
    is_hourly = db.Column(db.Boolean, default=False)
    hourly_rate = db.Column(db.Float, nullable=True, default=0.0)
    overtime_rate = db.Column(db.Float, nullable=True, default=0.0)  # 1.5x regular rate
    bank_account = db.Column(db.String(50), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_monthly_salary(self, days_present, total_days, hours_worked=0):
        """Calculate salary for the month"""
        if self.is_hourly:
            regular_pay = hours_worked * self.hourly_rate
            # Assume 8 hours/day for overtime calculation
            standard_hours = days_present * 8
            overtime_hours = max(0, hours_worked - standard_hours)
            overtime_pay = overtime_hours * self.overtime_rate
            gross_salary = regular_pay + overtime_pay
        else:
            gross_salary = self.basic_salary * (days_present / total_days)

        # Return basic calculation - advance deductions will be applied separately
        return {
            'gross_salary': round(gross_salary, 2),
            'deductions': 0.0,  # Advance deductions handled separately
            'net_salary': round(gross_salary, 2)
        }

    def __repr__(self):
        return f'<EmployeeDetails user_id={self.user_id} salary={self.basic_salary}>'

class Attendance(db.Model, CRUDMixin):
    """Daily attendance records"""
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    present = db.Column(db.Boolean, default=False)
    hours_worked = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='unique_user_date'),)

    def __repr__(self):
        return f'<Attendance user_id={self.user_id} date={self.date} present={self.present}>'

class Leave(db.Model, CRUDMixin):
    """Leave requests and records"""
    __tablename__ = 'leave'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    leave_type = db.Column(db.String(50), nullable=False)  # 'sick', 'vacation', 'personal', 'maternity', etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Self-referential relationship for approver
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_leaves')

    def __repr__(self):
        return f'<Leave user_id={self.user_id} type={self.leave_type} status={self.status}>'

class MonthlyPayout(db.Model, CRUDMixin):
    """Monthly payout records"""
    __tablename__ = 'monthly_payout'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end = db.Column(db.Date, nullable=False)
    days_worked = db.Column(db.Integer, default=0)
    gross_earnings = db.Column(db.Float, nullable=False)
    advance_deduction = db.Column(db.Float, default=0.0)
    final_payout = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='calculated')  # 'calculated', 'paid'
    payment_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'pay_period_start', 'pay_period_end', name='unique_user_pay_period'),)

    def __repr__(self):
        return f'<MonthlyPayout user_id={self.user_id} {self.pay_period_start}-{self.pay_period_end} net={self.net_salary}>'

class AuditLog(db.Model, CRUDMixin):
    """Audit log for tracking changes"""
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who made the change
    action = db.Column(db.String(100), nullable=False)  # 'create', 'update', 'delete'
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    old_values = db.Column(db.Text, nullable=True)  # JSON string of old values
    new_values = db.Column(db.Text, nullable=True)  # JSON string of new values
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id}>'

class Advance(db.Model, CRUDMixin):
    """Employee advances tracking"""
    __tablename__ = 'advance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)  # Principal amount
    monthly_deduction = db.Column(db.Float, nullable=False)  # Fixed monthly deduction
    remaining_balance = db.Column(db.Float, nullable=False)  # Amount still to be deducted
    description = db.Column(db.String(200), nullable=True)
    advance_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', overlaps="advances")

    def apply_monthly_deduction(self):
        """Apply monthly deduction"""
        if self.remaining_balance > 0:
            deduction = min(self.monthly_deduction, self.remaining_balance)
            self.remaining_balance -= deduction
            if self.remaining_balance <= 0:
                self.status = 'completed'
            self.save()
            return deduction
        return 0.0

    def __repr__(self):
        return f'<Advance user_id={self.user_id} amount={self.amount} remaining={self.remaining_balance}>'

# CRUD Operations Classes
class CRUDMixin:
    """Mixin class providing basic CRUD operations"""

    @classmethod
    def create(cls, **kwargs):
        """Create a new record"""
        instance = cls(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    @classmethod
    def get_by_id(cls, id):
        """Get record by ID"""
        return cls.query.get(id)

    @classmethod
    def get_all(cls):
        """Get all records"""
        return cls.query.all()

    @classmethod
    def filter_by(cls, **kwargs):
        """Filter records by given criteria"""
        return cls.query.filter_by(**kwargs)

    def update(self, **kwargs):
        """Update record with given values"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return self

    def delete(self):
        """Delete the record"""
        db.session.delete(self)
        db.session.commit()
        return True

    def save(self):
        """Save the record"""
        db.session.add(self)
        db.session.commit()
        return self

