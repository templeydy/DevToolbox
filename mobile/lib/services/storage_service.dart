import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// 本地存储服务
/// 数据格式与桌面端一致，支持云同步共享
class StorageService extends ChangeNotifier {
  List<Map<String, dynamic>> _notes = [];
  List<Map<String, dynamic>> _passwords = [];

  List<Map<String, dynamic>> get notes => _notes;
  List<Map<String, dynamic>> get passwords => _passwords;

  StorageService() {
    _loadAll();
  }

  Future<String> get _dataDir async {
    final dir = await getApplicationDocumentsDirectory();
    final dataDir = Directory('${dir.path}/devtoolbox');
    if (!await dataDir.exists()) {
      await dataDir.create(recursive: true);
    }
    return dataDir.path;
  }

  // ---------- 笔记 ----------

  Future<void> _loadNotes() async {
    try {
      final path = '${await _dataDir}/notes.json';
      final file = File(path);
      if (await file.exists()) {
        final content = await file.readAsString();
        _notes = List<Map<String, dynamic>>.from(jsonDecode(content));
      }
    } catch (e) {
      debugPrint('Load notes error: $e');
    }
  }

  Future<void> _saveNotes() async {
    final path = '${await _dataDir}/notes.json';
    await File(path).writeAsString(jsonEncode(_notes));
  }

  void addNote(Map<String, dynamic> note) {
    _notes.insert(0, note);
    _saveNotes();
    notifyListeners();
  }

  void updateNote(String id, Map<String, dynamic> updates) {
    final index = _notes.indexWhere((n) => n['id'] == id);
    if (index >= 0) {
      _notes[index].addAll(updates);
      _saveNotes();
      notifyListeners();
    }
  }

  void deleteNote(String id) {
    _notes.removeWhere((n) => n['id'] == id);
    _saveNotes();
    notifyListeners();
  }

  // ---------- 密码 ----------

  Future<void> _loadPasswords() async {
    try {
      final path = '${await _dataDir}/passwords.json';
      final file = File(path);
      if (await file.exists()) {
        final content = await file.readAsString();
        _passwords = List<Map<String, dynamic>>.from(jsonDecode(content));
      }
    } catch (e) {
      debugPrint('Load passwords error: $e');
    }
  }

  Future<void> _savePasswords() async {
    final path = '${await _dataDir}/passwords.json';
    await File(path).writeAsString(jsonEncode(_passwords));
  }

  void addPassword(Map<String, dynamic> entry) {
    _passwords.insert(0, entry);
    _savePasswords();
    notifyListeners();
  }

  void updatePassword(String id, Map<String, dynamic> updates) {
    final index = _passwords.indexWhere((p) => p['id'] == id);
    if (index >= 0) {
      _passwords[index].addAll(updates);
      _savePasswords();
      notifyListeners();
    }
  }

  void deletePassword(String id) {
    _passwords.removeWhere((p) => p['id'] == id);
    _savePasswords();
    notifyListeners();
  }

  // ---------- 加载全部 ----------

  Future<void> _loadAll() async {
    await _loadNotes();
    await _loadPasswords();
    notifyListeners();
  }

  /// 获取所有数据用于同步上传
  Future<Map<String, dynamic>> exportAll() async {
    return {
      'notes': _notes,
      'passwords': _passwords,
      'exported_at': DateTime.now().toIso8601String(),
    };
  }

  /// 从云端数据导入
  Future<void> importAll(Map<String, dynamic> data) async {
    if (data.containsKey('notes')) {
      _notes = List<Map<String, dynamic>>.from(data['notes']);
      await _saveNotes();
    }
    if (data.containsKey('passwords')) {
      _passwords = List<Map<String, dynamic>>.from(data['passwords']);
      await _savePasswords();
    }
    notifyListeners();
  }
}
