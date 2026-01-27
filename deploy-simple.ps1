# Simple Payroll Deployment Script
# This script deploys the payroll system with SQLite for demo purposes

Write-Host "🚀 Payroll Management System - Simple Deployment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Check if Python is installed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check if pip is installed
if (!(Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Host "pip is not installed. Please install pip first." -ForegroundColor Red
    exit 1
}

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Setting up database..." -ForegroundColor Cyan
# Create a simple SQLite database for demo
$env:FLASK_ENV = "development"
$env:SECRET_KEY = "demo-secret-key-change-in-production"

python -c "
from app import app, db, User
with app.app_context():
    db.create_all()
    # Create admin user
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', name='Administrator', email='admin@example.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created')
    else:
        print('Admin user already exists')
print('Database setup complete')
"

Write-Host "Starting application..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Application will be available at: http://localhost:5000" -ForegroundColor White
Write-Host "Admin Login:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

python app.py