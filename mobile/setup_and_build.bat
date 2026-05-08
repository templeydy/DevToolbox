@echo off
chcp 65001 >nul
echo === DevToolbox 移动端 - 初始化并编译 Android ===
echo.

:: 检查 Flutter
where flutter >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Flutter SDK
    echo.
    echo 请先安装 Flutter:
    echo   1. 下载: https://docs.flutter.dev/get-started/install/windows
    echo   2. 解压到如 C:\flutter
    echo   3. 添加 C:\flutter\bin 到 PATH 环境变量
    echo   4. 重新打开终端运行此脚本
    pause
    exit /b 1
)

echo [1/5] Flutter 版本信息:
call flutter --version
echo.

echo [2/5] 初始化 Flutter 项目结构...
call flutter create --project-name devtoolbox_mobile --org com.devtoolbox --platforms android,ios .
:: 恢复我们的源码（flutter create 会覆盖 lib/main.dart）
git checkout -- lib/ pubspec.yaml 2>nul

echo [3/5] 获取依赖...
call flutter pub get

echo [4/5] 检查环境...
call flutter doctor

echo [5/5] 编译 Android APK...
call flutter build apk --release

echo.
echo === 编译完成 ===
if exist "build\app\outputs\flutter-apk\app-release.apk" (
    echo APK 位置: build\app\outputs\flutter-apk\app-release.apk
) else (
    echo [警告] APK 未找到，请检查上方错误信息
)
pause
