@echo off
REM Docker management scripts for Blog Post Manager (Windows)

setlocal enabledelayedexpansion

if "%1"=="" goto usage

REM Development commands
if "%1"=="dev:start" goto dev_start
if "%1"=="dev:stop" goto dev_stop
if "%1"=="dev:restart" goto dev_restart
if "%1"=="dev:logs" goto dev_logs
if "%1"=="dev:build" goto dev_build

REM Production commands
if "%1"=="prod:start" goto prod_start
if "%1"=="prod:stop" goto prod_stop
if "%1"=="prod:logs" goto prod_logs
if "%1"=="prod:build" goto prod_build

REM Database commands
if "%1"=="db:migrate" goto db_migrate
if "%1"=="db:shell" goto db_shell
if "%1"=="db:backup" goto db_backup

REM Utility commands
if "%1"=="health" goto health_check
if "%1"=="cleanup" goto cleanup

goto usage

:dev_start
echo [INFO] Starting development environment...
docker-compose up -d
echo [INFO] Services started. Frontend: http://localhost:3000, Backend: http://localhost:8000
goto end

:dev_stop
echo [INFO] Stopping development environment...
docker-compose down
goto end

:dev_restart
echo [INFO] Restarting development environment...
docker-compose restart
goto end

:dev_logs
docker-compose logs -f
goto end

:dev_build
echo [INFO] Building development images...
docker-compose build --no-cache
goto end

:prod_start
if not exist .env (
    echo [ERROR] .env file not found. Please copy .env.example to .env and configure it.
    exit /b 1
)
echo [INFO] Starting production environment...
docker-compose -f docker-compose.prod.yml up -d
echo [INFO] Production services started. Access via http://localhost
goto end

:prod_stop
echo [INFO] Stopping production environment...
docker-compose -f docker-compose.prod.yml down
goto end

:prod_logs
docker-compose -f docker-compose.prod.yml logs -f
goto end

:prod_build
echo [INFO] Building production images...
docker-compose -f docker-compose.prod.yml build --no-cache
goto end

:db_migrate
echo [INFO] Running database migrations...
docker-compose exec backend python manage.py migrate
goto end

:db_shell
echo [INFO] Opening database shell...
docker-compose exec db psql -U postgres -d fintalk_dev
goto end

:db_backup
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "backup_file=backup_%YYYY%%MM%%DD%_%HH%%Min%%Sec%.sql"
echo [INFO] Creating database backup: %backup_file%
docker-compose exec db pg_dump -U postgres fintalk_dev > %backup_file%
echo [INFO] Backup created: %backup_file%
goto end

:health_check
echo [INFO] Checking service health...

REM Check database
docker-compose exec db pg_isready -U postgres >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] ✓ Database is healthy
) else (
    echo [ERROR] ✗ Database is not healthy
)

REM Check backend
docker-compose exec backend python manage.py check >nul 2>&1
if %errorlevel%==0 (
    echo [INFO] ✓ Backend is healthy
) else (
    echo [ERROR] ✗ Backend is not healthy
)

echo [INFO] Running containers:
docker-compose ps
goto end

:cleanup
echo [WARNING] This will remove all containers, images, and volumes. Are you sure? (y/N)
set /p response=
if /i "%response%"=="y" (
    echo [INFO] Cleaning up Docker resources...
    docker-compose down -v
    docker system prune -a -f
    echo [INFO] Cleanup completed
) else (
    echo [INFO] Cleanup cancelled
)
goto end

:usage
echo FinTalk Docker Management Script (Windows)
echo.
echo Usage: %0 ^<command^>
echo.
echo Development Commands:
echo   dev:start    - Start development environment
echo   dev:stop     - Stop development environment
echo   dev:restart  - Restart development environment
echo   dev:logs     - View development logs
echo   dev:build    - Build development images
echo.
echo Production Commands:
echo   prod:start   - Start production environment
echo   prod:stop    - Stop production environment
echo   prod:logs    - View production logs
echo   prod:build   - Build production images
echo.
echo Database Commands:
echo   db:migrate   - Run database migrations
echo   db:shell     - Open database shell
echo   db:backup    - Create database backup
echo.
echo Utility Commands:
echo   health       - Check service health
echo   cleanup      - Clean up Docker resources
echo.
echo Examples:
echo   %0 dev:start
echo   %0 prod:start
echo   %0 health

:end
endlocal