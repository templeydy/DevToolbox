import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/storage_service.dart';

class NoteEditorScreen extends StatefulWidget {
  final Map<String, dynamic>? note;

  const NoteEditorScreen({super.key, this.note});

  @override
  State<NoteEditorScreen> createState() => _NoteEditorScreenState();
}

class _NoteEditorScreenState extends State<NoteEditorScreen> {
  late TextEditingController _titleController;
  late TextEditingController _contentController;
  bool _isNew = false;

  @override
  void initState() {
    super.initState();
    _isNew = widget.note == null;
    _titleController = TextEditingController(text: widget.note?['title'] ?? '');
    _contentController = TextEditingController(text: widget.note?['content'] ?? '');
  }

  @override
  void dispose() {
    _titleController.dispose();
    _contentController.dispose();
    super.dispose();
  }

  void _save() {
    final storage = context.read<StorageService>();
    final now = DateTime.now().toString().substring(0, 19);

    if (_isNew) {
      storage.addNote({
        'id': DateTime.now().millisecondsSinceEpoch.toString(),
        'title': _titleController.text.isEmpty ? '无标题' : _titleController.text,
        'content': _contentController.text,
        'created': now,
        'updated': now,
      });
    } else {
      storage.updateNote(widget.note!['id'], {
        'title': _titleController.text.isEmpty ? '无标题' : _titleController.text,
        'content': _contentController.text,
        'updated': now,
      });
    }
    Navigator.pop(context);
  }

  void _delete() {
    if (widget.note != null) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('确认删除'),
          content: const Text('确定要删除这条笔记吗？'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('取消')),
            TextButton(
              onPressed: () {
                context.read<StorageService>().deleteNote(widget.note!['id']);
                Navigator.pop(ctx);
                Navigator.pop(context);
              },
              child: const Text('删除', style: TextStyle(color: Colors.red)),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isNew ? '新建笔记' : '编辑笔记'),
        actions: [
          if (!_isNew)
            IconButton(icon: const Icon(Icons.delete_outline), onPressed: _delete),
          IconButton(icon: const Icon(Icons.check), onPressed: _save),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _titleController,
              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              decoration: const InputDecoration(
                hintText: '标题',
                border: InputBorder.none,
              ),
            ),
            const Divider(),
            Expanded(
              child: TextField(
                controller: _contentController,
                maxLines: null,
                expands: true,
                textAlignVertical: TextAlignVertical.top,
                decoration: const InputDecoration(
                  hintText: '开始写笔记...',
                  border: InputBorder.none,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
