# SQL Server Docker Setup
# Run this to start SQL Server in a Docker container

# Pull SQL Server image
docker pull mcr.microsoft.com/mssql/server:2022-latest

# Run SQL Server container
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=YourPassword123!" \
   -p 1433:1433 --name sqlserver --hostname sqlserver \
   -d mcr.microsoft.com/mssql/server:2022-latest

# Wait for SQL Server to start (about 30 seconds)
# Then test connection
docker exec -it sqlserver /opt/mssql-tools/bin/sqlcmd \
   -S localhost -U SA -P "YourPassword123!" \
   -Q "SELECT @@VERSION"