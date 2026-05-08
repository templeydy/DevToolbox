@echo off
chcp 65001 >nul
echo === 开发工具集 - Android 编译 ===
echo.

:: 检查 Flutter
where flutter >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Flutter SDK
    echo 请先安装 Flutter: https://docs.flutter.dev/get-started/install/windows
    pause
    exit /b 1
)

echo [1/4] 检查环境...
flutter doctor --android-licenses 2>nul

echo [2/4] 获取依赖...
call flutter pub get

echo [3/4] 编译 Release APK...
call flutter build apk --release

echo [4/4] 编译分架构 APK...
call flutter build apk --split-per-abi --release

echo.
echo === 编译完成 ===
echo APK 文件位置:
echo   build\app\outputs\flutter-apk\app-release.apk
echo   build\app\outputs\flutter-apk\app-arm64-v8a-release.apk
echo   build\app\outputs\flutter-apk\app-armeabi-v7a-release.apk
echo   build\app\outputs\flutter-apk\app-x86_64-release.apk
pause
