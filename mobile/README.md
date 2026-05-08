# DevToolbox Mobile

开发工具集移动端（Flutter），支持 iOS 和 Android。

## 功能

- 📝 AI 笔记 - 创建、编辑、删除笔记
- 🔐 账号密码管理 - 安全存储账号密码，一键复制
- ☁️ 云同步 - 支持 WebDAV / S3 兼容存储，与桌面端数据互通
- 🌙 深色模式 - 跟随系统主题

## 开发环境

- Flutter 3.16+
- Dart 3.2+

## 运行

```bash
cd mobile
flutter pub get
flutter run
```

## 构建

```bash
# Android
flutter build apk --release

# iOS
flutter build ios --release
```

## 数据格式

移动端与桌面端共用相同的 JSON 数据格式，通过云同步实现多端数据互通：

- `notes.json` - 笔记数据
- `passwords.json` - 密码数据（加密存储）

## 云同步配置

支持两种云存储方式：

1. **WebDAV** - 坚果云、NextCloud 等
2. **S3 兼容** - 阿里云 OSS、腾讯 COS、MinIO 等

未配置云同步时，数据仅保存在本地，不影响正常使用。
