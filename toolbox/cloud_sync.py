"""
云同步模块
支持 WebDAV 和对象存储（阿里云 OSS、腾讯 COS、S3 兼容）
离线时本地缓存，联网后自动同步
"""

import json
import os
import time
import threading
import urllib.request
import urllib.error
import base64
import hashlib
from datetime import datetime

SYNC_DIR = os.path.join(os.path.expanduser("~"), ".devtoolbox_settings")
SYNC_QUEUE_FILE = os.path.join(SYNC_DIR, "sync_queue.json")


class CloudSyncManager:
    """云同步管理器"""

    def __init__(self):
        self._config = {}
        self._sync_queue = []  # 离线时待同步的文件列表
        self._syncing = False
        self._auto_sync_thread = None
        self._running = False
        self._load_config()
        self._load_queue()

    def _load_config(self):
        from toolbox.settings import load_settings
        settings = load_settings()
        self._config = settings.get("cloud_sync", {})

    def _save_config(self, config):
        from toolbox.settings import load_settings, save_settings
        settings = load_settings()
        settings["cloud_sync"] = config
        save_settings(settings)
        self._config = config

    def _load_queue(self):
        if os.path.exists(SYNC_QUEUE_FILE):
            try:
                with open(SYNC_QUEUE_FILE, "r", encoding="utf-8") as f:
                    self._sync_queue = json.load(f)
            except Exception:
                self._sync_queue = []

    def _save_queue(self):
        os.makedirs(SYNC_DIR, exist_ok=True)
        with open(SYNC_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._sync_queue, f, ensure_ascii=False)

    @property
    def enabled(self):
        return self._config.get("enabled", False)

    @property
    def provider(self):
        return self._config.get("provider", "")

    def get_config(self):
        return self._config.copy()

    def configure(self, config):
        self._save_config(config)

    # ---------- 同步操作 ----------

    def upload_file(self, local_path, remote_path):
        """上传文件到云端"""
        if not self.enabled:
            return False

        try:
            with open(local_path, "rb") as f:
                data = f.read()
            return self._do_upload(remote_path, data)
        except Exception as e:
            # 离线或失败，加入队列
            self._add_to_queue("upload", local_path, remote_path)
            return False

    def upload_data(self, data: bytes, remote_path: str):
        """上传数据到云端"""
        if not self.enabled:
            return False
        try:
            return self._do_upload(remote_path, data)
        except Exception:
            # 保存到临时文件再加入队列
            tmp_path = os.path.join(SYNC_DIR, f"tmp_{hashlib.md5(remote_path.encode()).hexdigest()}")
            with open(tmp_path, "wb") as f:
                f.write(data)
            self._add_to_queue("upload", tmp_path, remote_path)
            return False

    def download_file(self, remote_path, local_path):
        """从云端下载文件"""
        if not self.enabled:
            return False
        try:
            data = self._do_download(remote_path)
            if data is not None:
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "wb") as f:
                    f.write(data)
                return True
        except Exception:
            pass
        return False

    def download_data(self, remote_path) -> bytes:
        """从云端下载数据"""
        if not self.enabled:
            return None
        try:
            return self._do_download(remote_path)
        except Exception:
            return None

    def sync_file(self, local_path, remote_path):
        """同步文件（上传本地文件到云端）"""
        if not self.enabled:
            return
        self.upload_file(local_path, remote_path)

    # ---------- 离线队列 ----------

    def _add_to_queue(self, action, local_path, remote_path):
        item = {
            "action": action,
            "local_path": local_path,
            "remote_path": remote_path,
            "timestamp": datetime.now().isoformat(),
        }
        self._sync_queue.append(item)
        self._save_queue()

    def process_queue(self):
        """处理离线队列"""
        if not self.enabled or not self._sync_queue:
            return

        remaining = []
        for item in self._sync_queue:
            try:
                if item["action"] == "upload":
                    if os.path.exists(item["local_path"]):
                        with open(item["local_path"], "rb") as f:
                            data = f.read()
                        self._do_upload(item["remote_path"], data)
                        # 清理临时文件
                        if "tmp_" in os.path.basename(item["local_path"]):
                            os.remove(item["local_path"])
                    # 成功，不加入 remaining
                elif item["action"] == "download":
                    data = self._do_download(item["remote_path"])
                    if data and item.get("local_path"):
                        with open(item["local_path"], "wb") as f:
                            f.write(data)
            except Exception:
                remaining.append(item)

        self._sync_queue = remaining
        self._save_queue()

    def get_queue_count(self):
        return len(self._sync_queue)

    # ---------- 自动同步 ----------

    def start_auto_sync(self, interval=60):
        """启动自动同步线程"""
        if self._running:
            return
        self._running = True
        self._auto_sync_thread = threading.Thread(
            target=self._auto_sync_loop, args=(interval,), daemon=True)
        self._auto_sync_thread.start()

    def stop_auto_sync(self):
        self._running = False

    def _auto_sync_loop(self, interval):
        while self._running:
            if self.enabled and self._sync_queue:
                self.process_queue()
            time.sleep(interval)

    # ---------- 网络检测 ----------

    def is_online(self):
        """检测网络是否可用"""
        try:
            urllib.request.urlopen("https://www.baidu.com", timeout=3)
            return True
        except Exception:
            return False

    # ---------- 提供者实现 ----------

    def _do_upload(self, remote_path, data: bytes) -> bool:
        provider = self.provider
        if provider == "webdav":
            return self._webdav_upload(remote_path, data)
        elif provider == "s3":
            return self._s3_upload(remote_path, data)
        else:
            raise ValueError(f"未知的云存储提供者: {provider}")

    def _do_download(self, remote_path) -> bytes:
        provider = self.provider
        if provider == "webdav":
            return self._webdav_download(remote_path)
        elif provider == "s3":
            return self._s3_download(remote_path)
        else:
            raise ValueError(f"未知的云存储提供者: {provider}")

    # --- WebDAV ---

    def _webdav_auth_header(self):
        user = self._config.get("webdav_user", "")
        password = self._config.get("webdav_password", "")
        auth = base64.b64encode(f"{user}:{password}".encode()).decode()
        return f"Basic {auth}"

    def _webdav_url(self, remote_path):
        base = self._config.get("webdav_url", "").rstrip("/")
        return f"{base}/{remote_path.lstrip('/')}"

    def _webdav_upload(self, remote_path, data: bytes) -> bool:
        url = self._webdav_url(remote_path)
        # 确保目录存在（MKCOL）
        dir_path = "/".join(remote_path.split("/")[:-1])
        if dir_path:
            self._webdav_mkcol(dir_path)

        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Authorization", self._webdav_auth_header())
        req.add_header("Content-Type", "application/octet-stream")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201, 204)

    def _webdav_download(self, remote_path) -> bytes:
        url = self._webdav_url(remote_path)
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", self._webdav_auth_header())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def _webdav_mkcol(self, dir_path):
        """创建 WebDAV 目录"""
        url = self._webdav_url(dir_path + "/")
        req = urllib.request.Request(url, method="MKCOL")
        req.add_header("Authorization", self._webdav_auth_header())
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass  # 目录可能已存在

    # --- S3 兼容（阿里云 OSS / 腾讯 COS / MinIO 等）---

    def _s3_upload(self, remote_path, data: bytes) -> bool:
        """简单 S3 PUT 上传（使用预签名或基础认证）"""
        endpoint = self._config.get("s3_endpoint", "")
        bucket = self._config.get("s3_bucket", "")
        access_key = self._config.get("s3_access_key", "")
        secret_key = self._config.get("s3_secret_key", "")

        url = f"{endpoint.rstrip('/')}/{bucket}/{remote_path.lstrip('/')}"

        # 简单签名（适用于支持 path-style 的 S3 兼容存储）
        date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        string_to_sign = f"PUT\n\napplication/octet-stream\n{date_str}\n/{bucket}/{remote_path.lstrip('/')}"
        import hmac
        signature = base64.b64encode(
            hmac.new(secret_key.encode(), string_to_sign.encode(), hashlib.sha1).digest()
        ).decode()

        req = urllib.request.Request(url, data=data, method="PUT")
        req.add_header("Date", date_str)
        req.add_header("Content-Type", "application/octet-stream")
        req.add_header("Authorization", f"AWS {access_key}:{signature}")

        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status in (200, 201)

    def _s3_download(self, remote_path) -> bytes:
        endpoint = self._config.get("s3_endpoint", "")
        bucket = self._config.get("s3_bucket", "")
        access_key = self._config.get("s3_access_key", "")
        secret_key = self._config.get("s3_secret_key", "")

        url = f"{endpoint.rstrip('/')}/{bucket}/{remote_path.lstrip('/')}"

        date_str = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        string_to_sign = f"GET\n\n\n{date_str}\n/{bucket}/{remote_path.lstrip('/')}"
        import hmac
        signature = base64.b64encode(
            hmac.new(secret_key.encode(), string_to_sign.encode(), hashlib.sha1).digest()
        ).decode()

        req = urllib.request.Request(url, method="GET")
        req.add_header("Date", date_str)
        req.add_header("Authorization", f"AWS {access_key}:{signature}")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise


# 全局单例
_sync_manager = None


def get_sync_manager() -> CloudSyncManager:
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = CloudSyncManager()
        _sync_manager.start_auto_sync()
    return _sync_manager
