"""
基础分析模块（免费版）
提供行情概览、涨跌幅判断、成交量分析
"""

from .fetcher import fetch_quote


def quick_analysis(code: str) -> dict:
    """快速分析一只股票/ETF（免费版功能）"""
    data = fetch_quote(code)
    if "error" in data:
        return data

    result = {
        "quote": {
            "name": data["name"],
            "code": data["code"],
            "price": data["price"],
            "change_pct": data["change_pct"],
            "high": data["high"],
            "low": data["low"],
            "volume": data["volume"],
            "amount": data["amount"],
            "turnover": data["turnover"],
        },
        "signals": [],
        "verdict": "",
    }

    p = data["price"]
    chg = data["change_pct"]
    turn = data["turnover"]

    # 涨跌信号
    if chg <= -7:
        result["signals"].append(("[暴跌]", f"跌幅{chg:.2f}%，接近跌停"))
    elif chg <= -4:
        result["signals"].append(("[大跌]", f"跌幅{chg:.2f}%，空头强势"))
    elif chg >= 7:
        result["signals"].append(("[暴涨]", f"涨幅{chg:.2f}%，接近涨停"))
    elif chg >= 4:
        result["signals"].append(("[大涨]", f"涨幅{chg:.2f}%，多头强势"))
    elif abs(chg) < 1:
        result["signals"].append(("[平盘]", f"涨跌幅{chg:.2f}%，窄幅震荡"))

    # 成交量信号
    if turn > 10:
        result["signals"].append(("[天量]", f"换手率{turn:.2f}%，极端活跃"))
    elif turn > 5:
        result["signals"].append(("[放量]", f"换手率{turn:.2f}%，交投活跃"))
    elif turn < 1:
        result["signals"].append(("[缩量]", f"换手率{turn:.2f}%，交投冷清"))

    # 综合判断（免费版只给大致方向）
    score = 50
    if chg < -5: score -= 15
    elif chg < -3: score -= 8
    elif chg > 5: score += 15
    elif chg > 2: score += 8

    result["score"] = max(0, min(100, score))
    if result["score"] >= 60:
        result["verdict"] = "偏多"
    elif result["score"] >= 40:
        result["verdict"] = "中性"
    else:
        result["verdict"] = "偏空"

    return result


def format_report(result: dict) -> str:
    """格式化输出报告"""
    if "error" in result:
        return f"[错误] {result['error']}"

    q = result["quote"]
    chg = q["change_pct"]
    chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"

    lines = [
        f"StockMind - 免费版分析",
        f"{'='*40}",
        f"  {q['name']} ({q['code']})",
        f"  现价: {q['price']:.3f}  涨跌: {chg_str}",
        f"  最高: {q['high']:.3f}  最低: {q['low']:.3f}",
        f"  成交: {q['volume']:,}手  {q['amount']}亿",
        f"  换手: {q['turnover']:.2f}%",
        f"",
        f"信号:",
    ]
    for icon, text in result["signals"]:
        lines.append(f"  {icon} {text}")

    lines.extend([
        f"",
        f"评分: {result['score']}/100 [{result['verdict']}]",
        f"",
        f"{'='*40}",
        f"[提示] 免费版仅提供基础分析",
        f"[升级] StockMind Pro 可解锁完整6维分析:",
        f"      持仓盈亏 + 情景推演 + 止损预警 + 钉钉推送",
        f"      仅 ¥49.9 买断，永久使用",
        f"{'='*40}",
    ])
    return "\n".join(lines)
