import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/storage_service.dart';
import 'password_edit_screen.dart';

class PasswordsScreen extends StatelessWidget {
  const PasswordsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('账号密码'),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
        ],
      ),
      body: Consumer<StorageService>(
        builder: (context, storage, child) {
          final entries = storage.passwords;
          if (entries.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.lock_outline, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text('暂无保存的账号', style: TextStyle(color: Colors.grey, fontSize: 16)),
                  SizedBox(height: 8),
                  Text('点击右下角按钮添加', style: TextStyle(color: Colors.grey)),
                ],
              ),
            );
          }

          // 按分组归类
          final groups = <String, List<Map<String, dynamic>>>{};
          for (final e in entries) {
            final g = e['group'] ?? '默认';
            groups.putIfAbsent(g, () => []).add(e);
          }

          return ListView(
            padding: const EdgeInsets.all(12),
            children: groups.entries.map((group) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
                    child: Text(group.key,
                        style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Theme.of(context).colorScheme.primary)),
                  ),
                  ...group.value.map((entry) => Card(
                        margin: const EdgeInsets.only(bottom: 6),
                        child: ListTile(
                          leading: CircleAvatar(
                            child: Text(
                              (entry['title'] ?? '?')[0].toUpperCase(),
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                          title: Text(entry['title'] ?? ''),
                          subtitle: Text(entry['username'] ?? ''),
                          trailing: PopupMenuButton<String>(
                            onSelected: (action) {
                              if (action == 'copy_user') {
                                Clipboard.setData(ClipboardData(text: entry['username'] ?? ''));
                                ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('用户名已复制'), duration: Duration(seconds: 1)));
                              } else if (action == 'copy_pass') {
                                Clipboard.setData(ClipboardData(text: entry['password'] ?? ''));
                                ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('密码已复制'), duration: Duration(seconds: 1)));
                              } else if (action == 'edit') {
                                Navigator.push(context,
                                    MaterialPageRoute(builder: (_) => PasswordEditScreen(entry: entry)));
                              } else if (action == 'delete') {
                                _confirmDelete(context, storage, entry);
                              }
                            },
                            itemBuilder: (_) => [
                              const PopupMenuItem(value: 'copy_user', child: Text('复制用户名')),
                              const PopupMenuItem(value: 'copy_pass', child: Text('复制密码')),
                              const PopupMenuItem(value: 'edit', child: Text('编辑')),
                              const PopupMenuItem(value: 'delete', child: Text('删除')),
                            ],
                          ),
                          onTap: () {
                            Navigator.push(context,
                                MaterialPageRoute(builder: (_) => PasswordEditScreen(entry: entry)));
                          },
                        ),
                      )),
                ],
              );
            }).toList(),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(context,
              MaterialPageRoute(builder: (_) => const PasswordEditScreen()));
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  void _confirmDelete(BuildContext context, StorageService storage, Map<String, dynamic> entry) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('确定删除「${entry['title']}」？'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
          TextButton(
            onPressed: () {
              storage.deletePassword(entry['id']);
              Navigator.pop(ctx);
            },
            child: const Text('删除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}
