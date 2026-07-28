"""
消息推送模块（Pro版）
支持钉钉机器人 + 微信（企业微信）推送
"""

import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from pathlib import Path


class PushManager:
    """推送管理器"""

    def __init__(self):
        self.config_file = Path.home() / ".stockmind" / "push_config.json"
        self.config = self._load()

    def _load(self) -> dict:
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(
            json.dumps(self.config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def config_dingtalk(self, webhook_url: str, secret: str = ""):
        """配置钉钉机器人"""
        self.config["dingtalk"] = {"webhook": webhook_url, "secret": secret}
        self._save()

    def config_wechat(self, webhook_url: str):
        """配置企业微信机器人"""
        self.config["wechat"] = {"webhook": webhook_url}
        self._save()

    def send_dingtalk(self, title: str, content: str) -> bool:
        """发送钉钉消息"""
        cfg = self.config.get("dingtalk", {})
        if not cfg.get("webhook"):
            print("[推送] 钉钉未配置，请先配置 webhook")
            return False

        data = json.dumps({
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": content,
            }
        }).encode("utf-8")

        try:
            req = Request(cfg["webhook"], data=data,
                         headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=10).read().decode()
            result = json.loads(resp)
            if result.get("errcode") == 0:
                print("[推送] 钉钉消息发送成功")
                return True
            else:
                print(f"[推送] 钉钉发送失败: {result}")
                return False
        except Exception as e:
            print(f"[推送] 钉钉发送异常: {e}")
            return False

    def send_wechat(self, content: str) -> bool:
        """发送企业微信消息"""
        cfg = self.config.get("wechat", {})
        if not cfg.get("webhook"):
            print("[推送] 企业微信未配置")
            return False

        data = json.dumps({
            "msgtype": "markdown",
            "markdown": {"content": content}
        }).encode("utf-8")

        try:
            req = Request(cfg["webhook"], data=data,
                         headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=10).read().decode()
            print("[推送] 企业微信消息发送成功")
            return True
        except Exception as e:
            print(f"[推送] 企业微信发送异常: {e}")
            return False

    def send_report(self, report: str, channels: list = None):
        """发送分析报告到指定渠道"""
        if channels is None:
            channels = ["dingtalk"]

        for ch in channels:
            if ch == "dingtalk":
                self.send_dingtalk("StockMind 分析报告", report)
            elif ch == "wechat":
                self.send_wechat(report)
