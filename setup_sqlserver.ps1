# SQL Server Docker Setup for Windows PowerShell
# Run this to start SQL Server in a Docker container

# Set password (change this to a strong password)
$SQL_PASSWORD = "YourPassword123!"

# Pull SQL Server image
Write-Host "Pulling SQL Server Docker image..."
docker pull mcr.microsoft.com/mssql/server:2022-latest

# Run SQL Server container
Write-Host "Starting SQL Server container..."
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=$SQL_PASSWORD" `
   -p 1433:1433 --name sqlserver --hostname sqlserver `
   -d mcr.microsoft.com/mssql/server:2022-latest

# Wait for SQL Server to start
Write-Host "Waiting for SQL Server to start (this may take 30-60 seconds)..."
Start-Sleep -Seconds 30

# Test connection
Write-Host "Testing SQL Server connection..."
docker exec sqlserver /opt/mssql-tools/bin/sqlcmd `
   -S localhost -U SA -P "$SQL_PASSWORD" `
   -Q "SELECT @@VERSION"

Write-Host "SQL Server is now running on localhost:1433"
Write-Host "Username: SA"
Write-Host "Password: $SQL_PASSWORD"
Write-Host ""
Write-Host "To stop SQL Server: docker stop sqlserver"
Write-Host "To start again: docker start sqlserver"
Write-Host "To remove container: docker rm sqlserver"