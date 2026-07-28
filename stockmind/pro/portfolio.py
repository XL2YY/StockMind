"""
持仓管理模块（Pro版）
多股票持仓追踪 + 盈亏核算 + 止损管理 + 情景推演
"""

import json
from datetime import datetime
from pathlib import Path


def validate_license() -> bool:
    """验证Pro版许可证（简易版）
    正式版会使用加密验证机制"""
    lic_file = Path.home() / ".stockmind" / "license.key"
    if not lic_file.exists():
        return False
    try:
        key = lic_file.read_text().strip()
        # 简易验证：key长度>10且包含特定前缀
        return len(key) > 10 and key.startswith("SM-")
    except Exception:
        return False


class Portfolio:
    """投资组合管理器"""

    def __init__(self, data_file: str = None):
        if data_file:
            self.data_file = Path(data_file)
        else:
            self.data_file = Path.home() / ".stockmind" / "portfolio.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.positions = self._load()

    def _load(self) -> list:
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self):
        self.data_file.write_text(
            json.dumps(self.positions, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add(self, code: str, name: str, shares: int, price: float, note: str = ""):
        """添加/更新持仓"""
        for p in self.positions:
            if p["code"] == code:
                # 更新现有持仓（加权平均成本）
                old_cost = p["shares"] * p["entry"]
                new_cost = shares * price
                p["shares"] += shares
                p["entry"] = round((old_cost + new_cost) / p["shares"], 3)
                p["note"] = f"{p['note']}; {datetime.now().strftime('%m-%d')}加仓{shares}股@{price}"
                self._save()
                return p

        self.positions.append({
            "code": code,
            "name": name,
            "shares": shares,
            "entry": price,
            "stop_loss": round(price * 0.9, 3),
            "note": note or f"{datetime.now().strftime('%Y-%m-%d')} 买入{shares}股@{price}",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._save()
        return self.positions[-1]

    def remove(self, code: str):
        """移除持仓（清仓）"""
        self.positions = [p for p in self.positions if p["code"] != code]
        self._save()

    def get(self, code: str) -> dict | None:
        for p in self.positions:
            if p["code"] == code:
                return p
        return None

    def list_all(self) -> list:
        return self.positions

    def calc_pnl(self, code: str, current_price: float) -> dict | None:
        """计算单只盈亏"""
        pos = self.get(code)
        if not pos:
            return None
        cost = pos["shares"] * pos["entry"]
        market = pos["shares"] * current_price
        pnl = market - cost
        return {
            "code": code,
            "name": pos["name"],
            "shares": pos["shares"],
            "entry": pos["entry"],
            "cost": round(cost, 2),
            "market_value": round(market, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round((current_price / pos["entry"] - 1) * 100, 2),
            "stop_loss": pos.get("stop_loss", round(pos["entry"] * 0.9, 3)),
            "distance_to_stop": round(
                (current_price - pos.get("stop_loss", 0)) / current_price * 100, 2
            ) if pos.get("stop_loss") else None,
        }

    def total_assets(self, prices: dict) -> dict:
        """计算总资产"""
        total_market = 0
        details = []
        for p in self.positions:
            price = prices.get(p["code"], 0)
            market = p["shares"] * price
            total_market += market
            details.append({
                "code": p["code"],
                "name": p["name"],
                "shares": p["shares"],
                "market_value": round(market, 2),
            })
        return {
            "total_market": round(total_market, 2),
            "details": details,
        }
