#!/usr/bin/env pwsh

Write-Host "🚀 Starting AstraForge Space Mission Simulator..." -ForegroundColor Cyan
Write-Host ""
Write-Host "📡 Backend will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "🌐 Frontend will be available at: http://localhost:5173" -ForegroundColor Green  
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host ""

# Start the application
npm start