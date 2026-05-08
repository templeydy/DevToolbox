@echo off
chcp 65001 >nul
echo === 安装打包依赖 ===
pip install pyinstaller pymysql psycopg2-binary openpyxl

echo === 开始打包 ===
pyinstaller --noconfirm --onefile --windowed --name "DevToolbox" main.py

echo === 创建自签名证书并签名 ===

:: 检查证书是否已存在，避免重复创建
certutil -store My "DevToolbox Code Signing" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在创建自签名代码签名证书...
    powershell -Command "New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=DevToolbox Code Signing' -CertStoreLocation 'Cert:\CurrentUser\My' -NotAfter (Get-Date).AddYears(3)"
    echo 证书创建完成
) else (
    echo 证书已存在，跳过创建
)

:: 获取证书指纹
for /f "tokens=*" %%i in ('powershell -Command "(Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -eq 'CN=DevToolbox Code Signing' } | Select-Object -First 1).Thumbprint"') do set THUMBPRINT=%%i

if "%THUMBPRINT%"=="" (
    echo 错误：未找到证书指纹
    pause
    exit /b 1
)

echo 证书指纹: %THUMBPRINT%

:: 使用 signtool 签名（Windows SDK 自带）
where signtool >nul 2>&1
if %errorlevel% equ 0 (
    echo 正在使用 signtool 签名...
    signtool sign /sha1 %THUMBPRINT% /fd SHA256 /t http://timestamp.digicert.com "dist\DevToolbox.exe"
) else (
    echo signtool 未找到，尝试使用 PowerShell 签名...
    powershell -Command "$cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert | Where-Object { $_.Subject -eq 'CN=DevToolbox Code Signing' } | Select-Object -First 1; Set-AuthenticodeSignature -FilePath 'dist\DevToolbox.exe' -Certificate $cert -TimestampServer 'http://timestamp.digicert.com' -HashAlgorithm SHA256"
)

echo === 验证签名 ===
powershell -Command "Get-AuthenticodeSignature 'dist\DevToolbox.exe' | Format-List"

echo === 完成 ===
echo 已签名的可执行文件在 dist\ 目录下
pause
