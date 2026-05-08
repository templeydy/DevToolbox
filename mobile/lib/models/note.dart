/// 笔记数据模型
class Note {
  final String id;
  String title;
  String content;
  final String created;
  String updated;

  Note({
    required this.id,
    required this.title,
    required this.content,
    required this.created,
    required this.updated,
  });

  factory Note.fromJson(Map<String, dynamic> json) {
    return Note(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      content: json['content'] ?? '',
      created: json['created'] ?? '',
      updated: json['updated'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'content': content,
      'created': created,
      'updated': updated,
    };
  }

  factory Note.create({String title = '新笔记', String content = ''}) {
    final now = DateTime.now().toString().substring(0, 19);
    return Note(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      title: title,
      content: content,
      created: now,
      updated: now,
    );
  }
}
