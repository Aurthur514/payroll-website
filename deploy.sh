#!/bin/bash

# Payroll System Deployment Script
# This script helps deploy the payroll management system

set -e

echo "🚀 Payroll Management System Deployment"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.payroll .env
    echo "⚠️  Please edit .env file with your actual configuration values!"
    echo "   Especially update SECRET_KEY and database credentials."
    read -p "Press Enter after updating .env file..."
fi

# Create init-db directory for database initialization
mkdir -p init-db

echo "🏗️  Building and starting services..."
docker-compose -f docker-compose.payroll.yml up --build -d

echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check if services are running
if docker-compose -f docker-compose.payroll.yml ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   - Payroll App: http://localhost:8000"
    echo "   - MS SQL Server: localhost:1433"
    echo ""
    echo "👤 Default Admin Credentials:"
    echo "   - Username: admin"
    echo "   - Password: admin123"
    echo ""
    echo "📊 To view logs: docker-compose -f docker-compose.payroll.yml logs -f"
    echo "🛑 To stop: docker-compose -f docker-compose.payroll.yml down"
    echo ""
    echo "🎉 Deployment completed successfully!"
else
    echo "❌ Deployment failed. Check logs:"
    docker-compose -f docker-compose.payroll.yml logs
    exit 1
fi