/// 密码条目数据模型
class PasswordEntry {
  final String id;
  String group;
  String title;
  String username;
  String password;
  String url;
  String notes;
  final String created;
  String updated;

  PasswordEntry({
    required this.id,
    required this.group,
    required this.title,
    required this.username,
    required this.password,
    this.url = '',
    this.notes = '',
    required this.created,
    required this.updated,
  });

  factory PasswordEntry.fromJson(Map<String, dynamic> json) {
    return PasswordEntry(
      id: json['id'] ?? '',
      group: json['group'] ?? '默认',
      title: json['title'] ?? '',
      username: json['username'] ?? '',
      password: json['password'] ?? '',
      url: json['url'] ?? '',
      notes: json['notes'] ?? '',
      created: json['created'] ?? '',
      updated: json['updated'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'group': group,
      'title': title,
      'username': username,
      'password': password,
      'url': url,
      'notes': notes,
      'created': created,
      'updated': updated,
    };
  }

  factory PasswordEntry.create({
    required String title,
    required String username,
    required String password,
    String group = '默认',
    String url = '',
    String notes = '',
  }) {
    final now = DateTime.now().toString().substring(0, 19);
    return PasswordEntry(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      group: group,
      title: title,
      username: username,
      password: password,
      url: url,
      notes: notes,
      created: now,
      updated: now,
    );
  }
}
