"""
止损预警模块（Pro版）
价格监控 + 止损触发 + 钉钉/微信推送
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from ..fetcher import fetch_quote


class AlertManager:
    """预警管理器"""

    def __init__(self):
        self.config_file = Path.home() / ".stockmind" / "alerts.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.alerts = self._load()
        self._running = False
        self._thread = None

    def _load(self) -> list:
        if self.config_file.exists():
            try:
                return json.loads(self.config_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self):
        self.config_file.write_text(
            json.dumps(self.alerts, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add(self, code: str, name: str, alert_type: str, target_price: float,
            shares: int = 0, entry: float = 0):
        """添加预警
        alert_type: stop_loss / take_profit / price_alert
        """
        alert = {
            "id": f"{code}_{int(time.time())}",
            "code": code,
            "name": name,
            "type": alert_type,
            "target": target_price,
            "shares": shares,
            "entry": entry,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "triggered": False,
        }
        self.alerts.append(alert)
        self._save()
        return alert

    def remove(self, alert_id: str):
        self.alerts = [a for a in self.alerts if a["id"] != alert_id]
        self._save()

    def check(self) -> list:
        """检查所有未触发的预警"""
        triggered = []
        for alert in self.alerts:
            if alert["triggered"]:
                continue
            data = fetch_quote(alert["code"])
            if "error" in data:
                continue
            price = data["price"]

            if alert["type"] == "stop_loss" and price <= alert["target"]:
                alert["triggered"] = True
                alert["triggered_at"] = datetime.now().strftime("%H:%M:%S")
                alert["trigger_price"] = price
                triggered.append(alert)
            elif alert["type"] == "take_profit" and price >= alert["target"]:
                alert["triggered"] = True
                alert["triggered_at"] = datetime.now().strftime("%H:%M:%S")
                alert["trigger_price"] = price
                triggered.append(alert)
            elif alert["type"] == "price_alert" and abs(price - alert["target"]) / alert["target"] <= 0.01:
                alert["triggered"] = True
                alert["triggered_at"] = datetime.now().strftime("%H:%M:%S")
                alert["trigger_price"] = price
                triggered.append(alert)

        if triggered:
            self._save()
        return triggered

    def start_monitor(self, interval: int = 60, callback=None):
        """启动后台监控（每interval秒检查一次）"""
        if self._running:
            print("[预警] 监控已在运行中")
            return

        self._running = True

        def _loop():
            while self._running:
                try:
                    triggered = self.check()
                    for t in triggered:
                        msg = (f"[预警触发] {t['name']}({t['code']})\n"
                               f"  类型: {t['type']}\n"
                               f"  目标: {t['target']:.3f}\n"
                               f"  触发价: {t['trigger_price']:.3f}")
                        print(f"\n{'='*40}")
                        print(msg)
                        print(f"{'='*40}\n")
                        if callback:
                            callback(t)
                except Exception as e:
                    print(f"[预警] 检查出错: {e}")
                time.sleep(interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        print(f"[预警] 监控已启动 (每{interval}秒检查一次)")

    def stop_monitor(self):
        self._running = False
        print("[预警] 监控已停止")

    def list_alerts(self) -> list:
        active = [a for a in self.alerts if not a["triggered"]]
        triggered = [a for a in self.alerts if a["triggered"]]
        return {"active": active, "triggered": triggered}
