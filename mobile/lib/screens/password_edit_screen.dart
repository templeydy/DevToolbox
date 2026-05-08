import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/storage_service.dart';

class PasswordEditScreen extends StatefulWidget {
  final Map<String, dynamic>? entry;
  const PasswordEditScreen({super.key, this.entry});

  @override
  State<PasswordEditScreen> createState() => _PasswordEditScreenState();
}

class _PasswordEditScreenState extends State<PasswordEditScreen> {
  late TextEditingController _titleCtrl;
  late TextEditingController _usernameCtrl;
  late TextEditingController _passwordCtrl;
  late TextEditingController _urlCtrl;
  late TextEditingController _notesCtrl;
  late TextEditingController _groupCtrl;
  bool _obscurePassword = true;
  bool _isNew = false;

  @override
  void initState() {
    super.initState();
    _isNew = widget.entry == null;
    _titleCtrl = TextEditingController(text: widget.entry?['title'] ?? '');
    _usernameCtrl = TextEditingController(text: widget.entry?['username'] ?? '');
    _passwordCtrl = TextEditingController(text: widget.entry?['password'] ?? '');
    _urlCtrl = TextEditingController(text: widget.entry?['url'] ?? '');
    _notesCtrl = TextEditingController(text: widget.entry?['notes'] ?? '');
    _groupCtrl = TextEditingController(text: widget.entry?['group'] ?? '默认');
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    _urlCtrl.dispose();
    _notesCtrl.dispose();
    _groupCtrl.dispose();
    super.dispose();
  }

  String _generatePassword() {
    const chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#\$%&*';
    final random = Random.secure();
    return List.generate(16, (_) => chars[random.nextInt(chars.length)]).join();
  }

  void _save() {
    if (_titleCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('标题不能为空')),
      );
      return;
    }

    final storage = context.read<StorageService>();
    final now = DateTime.now().toString().substring(0, 19);

    if (_isNew) {
      storage.addPassword({
        'id': DateTime.now().millisecondsSinceEpoch.toString(),
        'group': _groupCtrl.text.trim().isEmpty ? '默认' : _groupCtrl.text.trim(),
        'title': _titleCtrl.text.trim(),
        'username': _usernameCtrl.text.trim(),
        'password': _passwordCtrl.text,
        'url': _urlCtrl.text.trim(),
        'notes': _notesCtrl.text.trim(),
        'created': now,
        'updated': now,
      });
    } else {
      storage.updatePassword(widget.entry!['id'], {
        'group': _groupCtrl.text.trim().isEmpty ? '默认' : _groupCtrl.text.trim(),
        'title': _titleCtrl.text.trim(),
        'username': _usernameCtrl.text.trim(),
        'password': _passwordCtrl.text,
        'url': _urlCtrl.text.trim(),
        'notes': _notesCtrl.text.trim(),
        'updated': now,
      });
    }
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isNew ? '新增账号' : '编辑账号'),
        actions: [
          IconButton(icon: const Icon(Icons.check), onPressed: _save),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _groupCtrl,
              decoration: const InputDecoration(
                labelText: '分组',
                prefixIcon: Icon(Icons.folder_outlined),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _titleCtrl,
              decoration: const InputDecoration(
                labelText: '标题',
                prefixIcon: Icon(Icons.title),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _usernameCtrl,
              decoration: const InputDecoration(
                labelText: '用户名',
                prefixIcon: Icon(Icons.person_outline),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordCtrl,
              obscureText: _obscurePassword,
              decoration: InputDecoration(
                labelText: '密码',
                prefixIcon: const Icon(Icons.lock_outline),
                suffixIcon: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                      onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                    IconButton(
                      icon: const Icon(Icons.casino),
                      tooltip: '生成随机密码',
                      onPressed: () {
                        _passwordCtrl.text = _generatePassword();
                        setState(() => _obscurePassword = false);
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _urlCtrl,
              decoration: const InputDecoration(
                labelText: '网址',
                prefixIcon: Icon(Icons.link),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _notesCtrl,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: '备注',
                prefixIcon: Icon(Icons.note_outlined),
                alignLabelWithHint: true,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
