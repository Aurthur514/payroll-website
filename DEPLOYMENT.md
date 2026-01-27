# Payroll Management System - Deployment Guide

## 🚀 Quick Deployment

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 8000 and 1433 available

### 1. Environment Setup
```bash
# Copy environment template
cp .env.payroll .env

# Edit with your values
nano .env
```

### 2. Deploy with Docker Compose
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 3. Access the Application
- **Payroll App**: http://localhost:8000
- **Default Admin Login**:
  - Username: `admin`
  - Password: `admin123`

## 🏗️ Manual Deployment

### Using Docker Compose
```bash
# Build and start services
docker-compose -f docker-compose.payroll.yml up --build -d

# View logs
docker-compose -f docker-compose.payroll.yml logs -f

# Stop services
docker-compose -f docker-compose.payroll.yml down
```

### Direct Python Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secret-key

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

## 📊 Production Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key (change in production)
- `SQL_SERVER`: MS SQL Server hostname
- `SQL_DATABASE`: Database name
- `SQL_USER`: Database username
- `SQL_PASSWORD`: Database password

### Database
The application uses MS SQL Server. In production, consider:
- Using Azure SQL Database or AWS RDS
- Enabling database backups
- Setting up connection pooling

### Security
- Change default admin password
- Use HTTPS in production
- Implement rate limiting
- Regular security updates

## 🔧 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process or change port in docker-compose.yml
   ```

2. **Database connection failed**
   - Check SQL Server is running
   - Verify connection string in .env
   - Check firewall settings

3. **Container won't start**
   ```bash
   # View detailed logs
   docker-compose -f docker-compose.payroll.yml logs payroll-app
   ```

### Health Checks
- Application health: http://localhost:8000/health
- Database connectivity is tested automatically

## 📈 Scaling

### Horizontal Scaling
```yaml
# In docker-compose.payroll.yml, increase replicas
services:
  payroll-app:
    deploy:
      replicas: 3
```

### Load Balancing
Consider using nginx or Traefik as a reverse proxy for multiple instances.

## 🔄 Updates

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.payroll.yml up --build -d
```

## 📝 Backup Strategy

### Database Backups
```bash
# Create backup
docker exec mssql /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourPassword123!' \
  -Q "BACKUP DATABASE payroll_db TO DISK = '/var/opt/mssql/backup/payroll.bak'"
```

### Application Data
- Templates and static files are in the container
- Consider volume mounting for persistent data

## 📞 Support

For issues or questions:
1. Check the logs: `docker-compose -f docker-compose.payroll.yml logs`
2. Verify environment variables in `.env`
3. Ensure all prerequisites are installed