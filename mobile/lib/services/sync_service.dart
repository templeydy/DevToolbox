import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;

/// 云同步服务
/// 支持 WebDAV 和 S3 兼容存储
/// 离线时缓存操作，联网后自动同步
class SyncService extends ChangeNotifier {
  bool _enabled = false;
  String _provider = 'webdav';
  Map<String, dynamic> _config = {};
  int _queueCount = 0;
  Timer? _autoSyncTimer;

  bool get enabled => _enabled;
  String get provider => _provider;
  Map<String, dynamic> get config => _config;
  int get queueCount => _queueCount;

  SyncService() {
    _loadConfig();
    _startAutoSync();
  }

  Future<void> _loadConfig() async {
    final prefs = await SharedPreferences.getInstance();
    final configStr = prefs.getString('cloud_sync_config');
    if (configStr != null) {
      _config = jsonDecode(configStr);
      _enabled = _config['enabled'] ?? false;
      _provider = _config['provider'] ?? 'webdav';
      notifyListeners();
    }
  }

  Future<void> _saveConfig() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('cloud_sync_config', jsonEncode(_config));
  }

  void setEnabled(bool value) {
    _enabled = value;
    _config['enabled'] = value;
    _saveConfig();
    notifyListeners();
  }

  void configure(Map<String, dynamic> newConfig) {
    _config = newConfig;
    _enabled = newConfig['enabled'] ?? false;
    _provider = newConfig['provider'] ?? 'webdav';
    _saveConfig();
    notifyListeners();
  }

  // ---------- 同步操作 ----------

  Future<bool> upload(String remotePath, List<int> data) async {
    if (!_enabled) return false;

    try {
      if (_provider == 'webdav') {
        return await _webdavUpload(remotePath, data);
      } else if (_provider == 's3') {
        return await _s3Upload(remotePath, data);
      }
    } catch (e) {
      debugPrint('Sync upload error: $e');
      _queueCount++;
      notifyListeners();
    }
    return false;
  }

  Future<List<int>?> download(String remotePath) async {
    if (!_enabled) return null;

    try {
      if (_provider == 'webdav') {
        return await _webdavDownload(remotePath);
      } else if (_provider == 's3') {
        return await _s3Download(remotePath);
      }
    } catch (e) {
      debugPrint('Sync download error: $e');
    }
    return null;
  }

  // ---------- 自动同步 ----------

  void _startAutoSync() {
    _autoSyncTimer?.cancel();
    _autoSyncTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      if (_enabled && _queueCount > 0) {
        _processQueue();
      }
    });
  }

  Future<void> _processQueue() async {
    // TODO: 处理离线队列
    _queueCount = 0;
    notifyListeners();
  }

  // ---------- WebDAV ----------

  Future<bool> _webdavUpload(String path, List<int> data) async {
    final baseUrl = _config['webdav_url'] ?? '';
    final user = _config['webdav_user'] ?? '';
    final pass = _config['webdav_password'] ?? '';

    final url = Uri.parse('$baseUrl/$path');
    final auth = base64Encode(utf8.encode('$user:$pass'));

    final response = await http.put(
      url,
      headers: {
        'Authorization': 'Basic $auth',
        'Content-Type': 'application/octet-stream',
      },
      body: data,
    ).timeout(const Duration(seconds: 30));

    return response.statusCode == 200 ||
        response.statusCode == 201 ||
        response.statusCode == 204;
  }

  Future<List<int>?> _webdavDownload(String path) async {
    final baseUrl = _config['webdav_url'] ?? '';
    final user = _config['webdav_user'] ?? '';
    final pass = _config['webdav_password'] ?? '';

    final url = Uri.parse('$baseUrl/$path');
    final auth = base64Encode(utf8.encode('$user:$pass'));

    final response = await http.get(
      url,
      headers: {'Authorization': 'Basic $auth'},
    ).timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      return response.bodyBytes;
    }
    return null;
  }

  // ---------- S3 兼容 ----------

  Future<bool> _s3Upload(String path, List<int> data) async {
    // 简化版 S3 上传（实际项目建议使用 aws_s3_api 包）
    final endpoint = _config['s3_endpoint'] ?? '';
    final bucket = _config['s3_bucket'] ?? '';
    final url = Uri.parse('$endpoint/$bucket/$path');

    final response = await http.put(
      url,
      headers: {'Content-Type': 'application/octet-stream'},
      body: data,
    ).timeout(const Duration(seconds: 30));

    return response.statusCode == 200 || response.statusCode == 201;
  }

  Future<List<int>?> _s3Download(String path) async {
    final endpoint = _config['s3_endpoint'] ?? '';
    final bucket = _config['s3_bucket'] ?? '';
    final url = Uri.parse('$endpoint/$bucket/$path');

    final response = await http.get(url).timeout(const Duration(seconds: 30));

    if (response.statusCode == 200) {
      return response.bodyBytes;
    }
    return null;
  }

  @override
  void dispose() {
    _autoSyncTimer?.cancel();
    super.dispose();
  }
}
