# 移动端编译指南

## 一、环境准备

### 1. 安装 Flutter SDK

下载地址：https://docs.flutter.dev/get-started/install/windows

```powershell
# 或使用 chocolatey 安装
choco install flutter
```

安装后运行：
```bash
flutter doctor
```

### 2. 安装 Android Studio

下载地址：https://developer.android.com/studio

安装后：
1. 打开 Android Studio → Settings → SDK Manager
2. 安装 Android SDK 34+
3. 安装 Android SDK Build-Tools
4. 安装 Android SDK Command-line Tools

### 3. 配置环境变量

确保以下命令可用：
```bash
flutter --version
java --version
```

## 二、编译 Android APK

```bash
cd mobile
flutter pub get
flutter build apk --release
```

生成文件：`mobile/build/app/outputs/flutter-apk/app-release.apk`

### 分架构编译（体积更小）：
```bash
flutter build apk --split-per-abi --release
```

## 三、编译 iOS（需要 Mac）

### 前置条件
- macOS 系统
- Xcode 15+
- Apple Developer 账号
- CocoaPods (`sudo gem install cocoapods`)

### 编译步骤

```bash
cd mobile
flutter pub get
cd ios && pod install && cd ..
flutter build ios --release
```

### 打包 IPA
在 Xcode 中打开 `mobile/ios/Runner.xcworkspace`：
1. 设置 Team（Apple Developer 账号）
2. 设置 Bundle Identifier
3. Product → Archive → Distribute App

## 四、快速测试（模拟器）

### Android 模拟器
```bash
flutter emulators --launch <emulator_id>
flutter run
```

### iOS 模拟器（仅 Mac）
```bash
open -a Simulator
flutter run
```

## 五、注意事项

- Android 编译可在 Windows/Mac/Linux 完成
- iOS 编译**只能在 Mac** 上完成
- 首次 `flutter pub get` 需要网络下载依赖
- 如果网络慢，可配置 Flutter 中国镜像：
  ```bash
  export PUB_HOSTED_URL=https://pub.flutter-io.cn
  export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn
  ```
