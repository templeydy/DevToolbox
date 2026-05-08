#!/bin/bash
echo "=== 开发工具集 - iOS 编译 ==="
echo ""

# 检查系统
if [[ "$(uname)" != "Darwin" ]]; then
    echo "[错误] iOS 编译只能在 macOS 上进行"
    exit 1
fi

# 检查 Flutter
if ! command -v flutter &> /dev/null; then
    echo "[错误] 未找到 Flutter SDK"
    echo "请先安装: https://docs.flutter.dev/get-started/install/macos"
    exit 1
fi

# 检查 Xcode
if ! command -v xcodebuild &> /dev/null; then
    echo "[错误] 未找到 Xcode"
    echo "请从 App Store 安装 Xcode"
    exit 1
fi

echo "[1/4] 获取依赖..."
flutter pub get

echo "[2/4] 安装 CocoaPods 依赖..."
cd ios && pod install && cd ..

echo "[3/4] 编译 iOS Release..."
flutter build ios --release --no-codesign

echo "[4/4] 完成"
echo ""
echo "=== 编译完成 ==="
echo "下一步："
echo "  1. 用 Xcode 打开 ios/Runner.xcworkspace"
echo "  2. 配置签名（Team + Bundle ID）"
echo "  3. Product → Archive → Distribute App"
echo ""
echo "或使用命令行打包 IPA："
echo "  flutter build ipa --release"
