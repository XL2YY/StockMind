"""
情景推演模块（Pro版）
三种情景分析 + 应对方案 + 风险评估
"""

from ..fetcher import fetch_quote
from .portfolio import Portfolio


def analyze_full(code: str, shares: int = 0, entry: float = 0) -> dict:
    """完整6维分析（Pro核心功能）"""
    data = fetch_quote(code)
    if "error" in data:
        return data

    p = data["price"]
    chg = data["change_pct"]
    turn = data["turnover"]
    amp = data["amplitude"]
    yc = data["yclose"]
    op = data["open"]

    result = {
        "quote": {
            "name": data["name"],
            "code": data["code"],
            "price": p,
            "yclose": yc,
            "open": op,
            "high": data["high"],
            "low": data["low"],
            "change_pct": chg,
            "volume": data["volume"],
            "amount": data["amount"],
            "turnover": turn,
            "amplitude": amp,
            "market_cap": data["market_cap"],
            "high_52w": data["high_52w"],
            "low_52w": data["low_52w"],
        },
        "dimensions": [],
        "scenarios": [],
        "verdict": {},
        "position": None,
    }

    # ── 维度1: 价格行为 ──
    price_signals = []
    if chg <= -7:
        price_signals.append(("[暴跌]", f"跌幅{chg:.2f}%，接近跌停，市场极度恐慌"))
    elif chg <= -4:
        price_signals.append(("[大跌]", f"跌幅{chg:.2f}%，空头占据绝对优势"))
    elif chg >= 7:
        price_signals.append(("[暴涨]", f"涨幅{chg:.2f}%，接近涨停"))
    elif chg >= 4:
        price_signals.append(("[大涨]", f"涨幅{chg:.2f}%，多头强势"))

    gap = (op / yc - 1) * 100 if yc else 0
    if abs(gap) > 1.5:
        d = "高开" if gap > 0 else "低开"
        price_signals.append(("[跳空]", f"{d}{abs(gap):.2f}%，隔夜情绪{'乐观' if gap>0 else '恐慌'}"))

    # K线形态
    body = abs(p - op)
    total_range = data["high"] - data["low"]
    if total_range > 0:
        up_shadow = data["high"] - max(p, op)
        low_shadow = min(p, op) - data["low"]
        if up_shadow > body * 2 and p < op:
            price_signals.append(("[上影]", "冲高回落，上方抛压沉重"))
        if low_shadow > body * 2 and p > op:
            price_signals.append(("[下影]", "探底回升，下方有承接盘"))
        if body > total_range * 0.7:
            price_signals.append(("[实体]", "单边行情，方向明确"))
        if body < total_range * 0.2:
            price_signals.append(("[十字]", "多空均衡，变盘信号"))

    result["dimensions"].append({"name": "价格行为", "signals": price_signals})

    # ── 维度2: 量价分析 ──
    vol_signals = []
    if turn > 10:
        vol_signals.append(("[天量]", f"换手率{turn:.2f}%，极端活跃，大资金剧烈博弈"))
    elif turn > 5:
        vol_signals.append(("[放量]", f"换手率{turn:.2f}%，交投活跃"))
    if data["amount"] > 5:
        vol_signals.append(("[大额]", f"成交额{data['amount']}亿，资金参与度高"))
    result["dimensions"].append({"name": "量价分析", "signals": vol_signals})

    # ── 维度3: 位置分析 ──
    pos_signals = []
    h52, l52 = data["high_52w"], data["low_52w"]
    if h52 and l52 and h52 > l52:
        pct = (p - l52) / (h52 - l52) * 100
        if pct > 85:
            pos_signals.append(("[高位]", f"52周高位({pct:.0f}%)，追高风险大"))
        elif pct < 15:
            pos_signals.append(("[低位]", f"52周低位({pct:.0f}%)，超跌区域"))
        else:
            pos_signals.append(("[中位]", f"52周{pct:.0f}%分位，方向待选择"))

    # 日内位置
    if data["high"] > data["low"]:
        intra = (p - data["low"]) / (data["high"] - data["low"]) * 100
        if intra < 15:
            pos_signals.append(("[收低]", f"收盘在日内低点({intra:.0f}%)，弱势"))
        elif intra > 85:
            pos_signals.append(("[收高]", f"收盘在日内高点({intra:.0f}%)，强势"))
    result["dimensions"].append({"name": "位置分析", "signals": pos_signals})

    # ── 维度4: 持仓分析 ──
    if shares > 0 and entry > 0:
        cost = shares * entry
        market_val = shares * p
        pnl = market_val - cost
        pnl_pct = (p / entry - 1) * 100
        stop = round(entry * 0.9, 3)
        result["position"] = {
            "shares": shares,
            "entry": entry,
            "cost": round(cost, 2),
            "market_value": round(market_val, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "stop_loss": stop,
            "distance_to_stop": round((p - stop) / p * 100, 2),
        }

        risk_signals = []
        if pnl_pct <= -8:
            risk_signals.append(("[危险]", f"浮亏{pnl_pct:.1f}%，接近止损线，密切监控"))
        elif pnl_pct <= -4:
            risk_signals.append(("[亏损]", f"浮亏{pnl_pct:.1f}%，在可控范围内"))
        elif pnl_pct >= 8:
            risk_signals.append(("[盈利]", f"浮盈{pnl_pct:.1f}%，考虑移动止盈"))
        if shares > 1000:
            risk_signals.append(("[重仓]", f"持仓{shares}股，仓位较重"))
        result["dimensions"].append({"name": "风险评估", "signals": risk_signals})

    # ── 维度5: 综合评分 ──
    score = 50
    if chg < -5: score -= 20
    elif chg < -3: score -= 10
    elif chg > 5: score += 20
    elif chg > 2: score += 10
    if turn > 8: score -= 5
    if amp > 5: score -= 5
    if chg < -5 and turn > 8: score -= 10

    score = max(0, min(100, score))
    if score >= 65:
        label = "偏多"
    elif score >= 40:
        label = "中性"
    else:
        label = "偏空"

    result["verdict"] = {"score": score, "label": label}

    # ── 维度6: 情景推演 ──
    s = shares or 1000
    down_prob = "高" if chg < -5 and turn > 8 else "中" if chg < -3 else "低"
    up_prob = "低" if chg < -5 else "中"

    result["scenarios"] = [
        {
            "label": "继续下跌",
            "prob": down_prob,
            "trigger": f"开盘 < {p*0.98:.3f}(-2%) 且量维持高位",
            "action": "立即止损，留现金等企稳",
            "impact": f"-{abs(p*0.97-p)*s:.0f} ~ -{abs(p*0.95-p)*s:.0f}元",
        },
        {
            "label": "横盘震荡",
            "prob": "高" if abs(chg) < 3 else "中",
            "trigger": f"开盘在 {p*0.98:.3f}~{p*1.02:.3f} 缩量整理",
            "action": "持有观察1-2天，换手<5%是企稳信号",
            "impact": "浮亏维持不变",
        },
        {
            "label": "技术反弹",
            "prob": up_prob,
            "trigger": f"放量拉升站稳 {p*1.03:.3f} 以上",
            "action": "持有看反弹力度，回补缺口则减仓",
            "impact": f"+{abs(p*1.05-p)*s:.0f} ~ +{abs(p*1.10-p)*s:.0f}元",
        },
    ]

    return result


def format_pro_report(result: dict) -> str:
    """格式化Pro版完整报告"""
    if "error" in result:
        return f"[错误] {result['error']}"
    if "quote" not in result:
        return "[错误] 无效的分析结果"

    q = result["quote"]
    chg_str = f"+{q['change_pct']:.2f}%" if q['change_pct'] >= 0 else f"{q['change_pct']:.2f}%"
    gap_str = f"(昨收{q['yclose']:.3f})" if q['yclose'] else ""

    lines = [
        f"StockMind Pro - 完整6维分析报告",
        f"{'='*55}",
        f"",
        f"【行情概览】",
        f"  {q['name']} ({q['code']})",
        f"  现价: {q['price']:.3f}  {chg_str}  {gap_str}",
        f"  最高: {q['high']:.3f}  最低: {q['low']:.3f}  振幅: {q['amplitude']:.2f}%",
        f"  成交: {q['volume']:,}手  {q['amount']}亿  换手: {q['turnover']:.2f}%",
        f"  52周: {q['low_52w']:.3f} ~ {q['high_52w']:.3f}  市值: {q['market_cap']}亿",
        f"",
    ]

    # 持仓
    if result["position"]:
        pos = result["position"]
        lines.extend([
            f"【持仓状态】",
            f"  持仓: {pos['shares']}股 @ {pos['entry']:.3f}",
            f"  成本: {pos['cost']}元  市值: {pos['market_value']}元",
            f"  盈亏: {pos['pnl']}元 ({pos['pnl_pct']:+.2f}%)",
            f"  止损: {pos['stop_loss']:.3f}  距止损: {pos['distance_to_stop']:.1f}%",
            f"",
        ])

    # 多维度
    lines.append(f"【多维交叉分析】")
    for dim in result["dimensions"]:
        for icon, text in dim["signals"]:
            lines.append(f"  {icon} {text}")
    lines.append("")

    # 评分
    v = result["verdict"]
    lines.append(f"【综合研判】")
    lines.append(f"  评分: {v['score']}/100 [{v['label']}]")
    lines.append("")

    # 情景
    lines.append(f"【情景推演与应对】")
    for s in result["scenarios"]:
        lines.append(f"  [{s['label']}] 概率:{s['prob']}")
        lines.append(f"    触发: {s['trigger']}")
        lines.append(f"    应对: {s['action']}")
        lines.append(f"    影响: {s['impact']}")
        lines.append("")

    # 纪律
    lines.extend([
        f"【核心纪律】",
        f"  1. 止损不犹豫，保本金才能打下一枪",
        f"  2. 不抄底不追高，等确认信号再出手",
        f"  3. 单票不超总资产40%",
        f"  4. 市场是流动的机会，不是固定的持仓",
        f"",
        f"{'='*55}",
        f"StockMind Pro v1.0 | 买断价¥49.9 | 微信/支付宝购买",
    ])

    return "\n".join(lines)
