import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/sync_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('设置')),
      body: Consumer<SyncService>(
        builder: (context, sync, child) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // 云同步设置
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.cloud_sync),
                          const SizedBox(width: 8),
                          const Text('云同步', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          const Spacer(),
                          Switch(
                            value: sync.enabled,
                            onChanged: (v) => sync.setEnabled(v),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        sync.enabled ? '已启用 (${sync.provider})' : '未启用（仅本地存储）',
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                      if (sync.enabled) ...[
                        const SizedBox(height: 12),
                        OutlinedButton.icon(
                          onPressed: () => _openSyncConfig(context, sync),
                          icon: const Icon(Icons.settings),
                          label: const Text('配置云存储'),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '待同步: ${sync.queueCount} 项',
                          style: const TextStyle(fontSize: 12, color: Colors.grey),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // AI 配置
              Card(
                child: ListTile(
                  leading: const Icon(Icons.smart_toy),
                  title: const Text('AI Agent 配置'),
                  subtitle: const Text('API 地址、Key、模型'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: AI 配置页
                  },
                ),
              ),
              const SizedBox(height: 12),

              // 关于
              Card(
                child: ListTile(
                  leading: const Icon(Icons.info_outline),
                  title: const Text('关于'),
                  subtitle: const Text('DevToolbox v1.0.0'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _openSyncConfig(BuildContext context, SyncService sync) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => _SyncConfigSheet(sync: sync),
    );
  }
}

class _SyncConfigSheet extends StatefulWidget {
  final SyncService sync;
  const _SyncConfigSheet({required this.sync});

  @override
  State<_SyncConfigSheet> createState() => _SyncConfigSheetState();
}

class _SyncConfigSheetState extends State<_SyncConfigSheet> {
  late String _provider;
  final _webdavUrlCtrl = TextEditingController();
  final _webdavUserCtrl = TextEditingController();
  final _webdavPassCtrl = TextEditingController();
  final _s3EndpointCtrl = TextEditingController();
  final _s3BucketCtrl = TextEditingController();
  final _s3AkCtrl = TextEditingController();
  final _s3SkCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    final cfg = widget.sync.config;
    _provider = cfg['provider'] ?? 'webdav';
    _webdavUrlCtrl.text = cfg['webdav_url'] ?? '';
    _webdavUserCtrl.text = cfg['webdav_user'] ?? '';
    _webdavPassCtrl.text = cfg['webdav_password'] ?? '';
    _s3EndpointCtrl.text = cfg['s3_endpoint'] ?? '';
    _s3BucketCtrl.text = cfg['s3_bucket'] ?? '';
    _s3AkCtrl.text = cfg['s3_access_key'] ?? '';
    _s3SkCtrl.text = cfg['s3_secret_key'] ?? '';
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20, right: 20, top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('云存储配置', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _provider,
              decoration: const InputDecoration(labelText: '存储类型'),
              items: const [
                DropdownMenuItem(value: 'webdav', child: Text('WebDAV')),
                DropdownMenuItem(value: 's3', child: Text('S3 兼容 (OSS/COS/MinIO)')),
              ],
              onChanged: (v) => setState(() => _provider = v!),
            ),
            const SizedBox(height: 16),
            if (_provider == 'webdav') ...[
              TextField(controller: _webdavUrlCtrl, decoration: const InputDecoration(labelText: 'WebDAV URL')),
              TextField(controller: _webdavUserCtrl, decoration: const InputDecoration(labelText: '用户名')),
              TextField(controller: _webdavPassCtrl, decoration: const InputDecoration(labelText: '密码'), obscureText: true),
            ] else ...[
              TextField(controller: _s3EndpointCtrl, decoration: const InputDecoration(labelText: 'Endpoint')),
              TextField(controller: _s3BucketCtrl, decoration: const InputDecoration(labelText: 'Bucket')),
              TextField(controller: _s3AkCtrl, decoration: const InputDecoration(labelText: 'Access Key')),
              TextField(controller: _s3SkCtrl, decoration: const InputDecoration(labelText: 'Secret Key'), obscureText: true),
            ],
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _save,
                child: const Text('保存'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _save() {
    widget.sync.configure({
      'enabled': true,
      'provider': _provider,
      'webdav_url': _webdavUrlCtrl.text,
      'webdav_user': _webdavUserCtrl.text,
      'webdav_password': _webdavPassCtrl.text,
      's3_endpoint': _s3EndpointCtrl.text,
      's3_bucket': _s3BucketCtrl.text,
      's3_access_key': _s3AkCtrl.text,
      's3_secret_key': _s3SkCtrl.text,
    });
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('云同步配置已保存')),
    );
  }
}
