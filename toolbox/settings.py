"""
全局设置模块
管理 SMTP 配置等全局共享设置，供所有工具使用
"""

import json
import os
import smtplib
import secrets
import hashlib
import base64
from email.mime.text import MIMEText

SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".devtoolbox_settings")


def _ensure_dir():
    os.makedirs(SETTINGS_DIR, exist_ok=True)


def _settings_file():
    return os.path.join(SETTINGS_DIR, "global_config.json")


def load_settings() -> dict:
    """加载全局设置"""
    _ensure_dir()
    path = _settings_file()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_settings(settings: dict):
    """保存全局设置"""
    _ensure_dir()
    with open(_settings_file(), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def get_smtp_config() -> dict:
    """获取 SMTP 配置"""
    settings = load_settings()
    return settings.get("smtp", {})


def save_smtp_config(smtp: dict):
    """保存 SMTP 配置"""
    settings = load_settings()
    settings["smtp"] = smtp
    save_settings(settings)


def get_smtp_account() -> str:
    """获取 SMTP 绑定的发件邮箱账号"""
    smtp = get_smtp_config()
    return smtp.get("user", "")


def generate_verification_code() -> str:
    """生成6位数字验证码"""
    return "".join([str(secrets.randbelow(10)) for _ in range(6)])


def send_verification_email(to_email: str, code: str):
    """发送验证码邮件"""
    smtp = get_smtp_config()
    host = smtp.get("host", "")
    port = int(smtp.get("port", "465"))
    user = smtp.get("user", "")
    password = smtp.get("password", "")
    use_ssl = smtp.get("use_ssl", True)

    if not host or not user or not password:
        raise ValueError("请先在全局设置中配置 SMTP 信息")

    if "pop" in host.lower():
        raise ValueError(
            f"主机 {host} 看起来是 POP3 服务器（收邮件），请改为 SMTP 服务器（发邮件）。\n"
            f"例如：smtp.qq.com、smtp.163.com"
        )

    msg = MIMEText(
        f"您的验证码是：{code}\n\n该验证码用于开发工具集登录验证，5分钟内有效。\n如非本人操作，请忽略此邮件。",
        "plain", "utf-8"
    )
    msg["Subject"] = "开发工具集 - 验证码"
    msg["From"] = user
    msg["To"] = to_email

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            server.starttls()
        server.login(user, password)
        server.sendmail(user, [to_email], msg.as_string())
        server.quit()
    except smtplib.SMTPAuthenticationError:
        raise ValueError("SMTP 认证失败，请检查邮箱和密码/授权码是否正确")
    except ConnectionRefusedError:
        raise ValueError(f"无法连接到 {host}:{port}，请检查主机和端口是否正确")
    except Exception as e:
        raise ValueError(f"邮件发送失败: {str(e)}\n请确认 SMTP 主机和端口配置正确")


def derive_key_from_account(account: str, salt: bytes) -> bytes:
    """从 SMTP 账号派生加密密钥"""
    return hashlib.pbkdf2_hmac("sha256", account.encode("utf-8"), salt, 100000)


def encrypt_data(plaintext: str, account: str) -> dict:
    """使用 SMTP 账号加密数据"""
    salt = secrets.token_bytes(16)
    key = derive_key_from_account(account, salt)
    data = plaintext.encode("utf-8")
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return {
        "salt": base64.b64encode(salt).decode(),
        "ciphertext": base64.b64encode(encrypted).decode(),
        "account_hash": hashlib.sha256(account.encode("utf-8")).hexdigest(),
    }


def decrypt_data(enc_data: dict, account: str) -> str:
    """使用 SMTP 账号解密数据，账号不匹配会解密失败"""
    # 验证账号是否匹配
    stored_hash = enc_data.get("account_hash", "")
    current_hash = hashlib.sha256(account.encode("utf-8")).hexdigest()
    if stored_hash and stored_hash != current_hash:
        raise PermissionError("当前 SMTP 账号与加密时使用的账号不一致，无法解密数据")

    salt = base64.b64decode(enc_data["salt"])
    ciphertext = base64.b64decode(enc_data["ciphertext"])
    key = derive_key_from_account(account, salt)
    decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(ciphertext))
    return decrypted.decode("utf-8")
