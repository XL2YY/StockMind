"""
自选股管理模块（Pro版）
支持多股票 watchlist + 批量分析 + 对比
"""

import json
from datetime import datetime
from pathlib import Path
from .engine import analyze_stock, format_report


class Watchlist:
    """自选股管理器"""

    def __init__(self):
        self.data_file = Path.home() / ".stockmind" / "watchlist.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.stocks = self._load()

    def _load(self) -> list:
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save(self):
        self.data_file.write_text(
            json.dumps(self.stocks, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add(self, code: str, name: str = "", note: str = ""):
        """添加自选股"""
        # 去重
        self.stocks = [s for s in self.stocks if s["code"] != code]
        self.stocks.append({
            "code": code,
            "name": name,
            "note": note,
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._save()

    def remove(self, code: str):
        """移除自选股"""
        self.stocks = [s for s in self.stocks if s["code"] != code]
        self._save()

    def list_all(self) -> list:
        return self.stocks

    def batch_analyze(self) -> list:
        """批量分析所有自选股"""
        results = []
        for s in self.stocks:
            try:
                r = analyze_stock(s["code"])
                r["note"] = s.get("note", "")
                results.append(r)
            except Exception as e:
                results.append({"error": str(e), "code": s["code"]})
        return results

    def compare(self, codes: list = None) -> dict:
        """多股票对比（核心指标一览）"""
        targets = codes or [s["code"] for s in self.stocks]
        comparison = []
        for code in targets:
            try:
                r = analyze_stock(code)
                if "error" not in r:
                    q = r["quote"]
                    comparison.append({
                        "code": q["code"],
                        "name": q["name"],
                        "price": q["price"],
                        "change_pct": q["change_pct"],
                        "turnover": q["turnover"],
                        "amount": q["amount"],
                        "amplitude": q["amplitude"],
                        "score": r["score"],
                        "verdict": r["verdict"]["label"],
                    })
            except Exception:
                pass

        # 按评分排序
        comparison.sort(key=lambda x: x["score"], reverse=True)
        return {"stocks": comparison, "count": len(comparison)}

    def format_compare(self, codes: list = None) -> str:
        """格式化为对比表格"""
        data = self.compare(codes)
        if not data["stocks"]:
            return "没有可对比的股票"

        lines = [
            "StockMind Pro - 多股票对比",
            "=" * 55,
            "  %-8s %-16s %8s %8s %6s %s" % (
                "代码", "名称", "现价", "涨跌", "评分", "研判"),
            "  " + "-" * 50,
        ]
        for s in data["stocks"]:
            chg = "%+.2f%%" % s["change_pct"]
            lines.append("  %-8s %-16s %8.3f %8s %5d %s" % (
                s["code"], s["name"][:8], s["price"], chg, s["score"], s["verdict"]))
        lines.append("  " + "-" * 50)
        lines.append("  共 %d 只股票" % data["count"])
        lines.append("=" * 55)
        return "\n".join(lines)


def hot_stocks(top_n: int = 10) -> list:
    """获取当日热门股票（基于换手率/成交额）
    注意: 腾讯行情不支持批量查询，此处为模拟
    建议集成专业数据源（如tushare/akshare）
    """
    # 常见热门ETF和龙头股快速分析
    hot_codes = [
        "159246", "159995", "159516", "588000", "512880",
        "510300", "510500", "159915", "159949", "512100",
        "000333", "000858", "002415", "300750", "600519",
        "601318", "600036", "000651", "002594", "300059",
    ]
    results = []
    for code in hot_codes[:top_n]:
        try:
            r = analyze_stock(code)
            if "error" not in r:
                results.append(r)
        except Exception:
            pass

    results.sort(key=lambda x: abs(x["quote"]["change_pct"]), reverse=True)
    return results
