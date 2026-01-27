# Payroll System Deployment Script for Windows
# This script helps deploy the payroll management system on Windows

Write-Host "Payroll Management System Deployment" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if Docker is installed
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is installed
if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (!(Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.payroll .env
    Write-Host "Please edit .env file with your actual configuration values!" -ForegroundColor Yellow
    Write-Host "Especially update SECRET_KEY and database credentials." -ForegroundColor Yellow
    Read-Host "Press Enter after updating .env file"
}

# Create init-db directory for database initialization
if (!(Test-Path init-db)) {
    New-Item -ItemType Directory -Path init-db | Out-Null
}

Write-Host "Building and starting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.payroll.yml up --build -d

Write-Host "Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if services are running
$services = docker-compose -f docker-compose.payroll.yml ps
if ($services -match "Up") {
    Write-Host "Services are running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Application URLs:" -ForegroundColor Cyan
    Write-Host "   - Payroll App: http://localhost:8000" -ForegroundColor White
    Write-Host "   - MS SQL Server: localhost:1433" -ForegroundColor White
    Write-Host ""
    Write-Host "Default Admin Credentials:" -ForegroundColor Cyan
    Write-Host "   - Username: admin" -ForegroundColor White
    Write-Host "   - Password: admin123" -ForegroundColor White
    Write-Host ""
    Write-Host "To view logs: docker-compose -f docker-compose.payroll.yml logs -f" -ForegroundColor Yellow
    Write-Host "To stop: docker-compose -f docker-compose.payroll.yml down" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Deployment failed. Check logs:" -ForegroundColor Red
    docker-compose -f docker-compose.payroll.yml logs
    exit 1
}