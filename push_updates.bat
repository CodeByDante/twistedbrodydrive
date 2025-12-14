@echo off
color 0A
echo ==========================================
echo      PREPARANDO SUBIDA A GITHUB
echo ==========================================
echo.

echo [1/6] Limpiando configuracion git antigua...
if exist .git rmdir /s /q .git

echo [2/6] Iniciando nuevo repositorio...
git init
git branch -M main

echo [3/6] Agregando archivos (Ignorando secretos)...
git add .

echo [4/6] Creando commit...
git commit -m "Update from Bot (Firebase Edition)"

echo [5/6] Conectando con GitHub...
git remote add origin https://github.com/CodeByDante/twistedbrodydrive.git

echo.
echo ==========================================
echo [6/6] SUBIENDO ARCHIVOS...
echo IMPORTANTE: Si te pide usuario/pass, usalos.
echo Si tienes activada la verificacion en 2 pasos,
echo usa un PERSONAL ACCESS TOKEN en vez de la pass.
echo ==========================================
echo.
git push -u origin main --force

echo.
echo ==========================================
if %errorlevel% equ 0 (
    echo      EXITO: CODIGO SUBIDO CORRECTAMENTE
) else (
    echo      ERROR: ALGO FALLO EN LA SUBIDA
)
echo ==========================================
pause
