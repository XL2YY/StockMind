"""
核心分析引擎（Pro版）
完整6维分析 + 情景推演 — 适用于任意A股/ETF
"""

from ..fetcher import fetch_quote


def analyze_stock(code: str) -> dict:
    """获取行情并做完整6维分析（不依赖持仓）"""
    data = fetch_quote(code)
    if "error" in data:
        return data
    return _build_analysis(data, shares=0, entry=0)


def analyze_with_position(code: str, shares: int, entry: float) -> dict:
    """带持仓的完整6维分析"""
    data = fetch_quote(code)
    if "error" in data:
        return data
    return _build_analysis(data, shares, entry)


def _build_analysis(data: dict, shares: int, entry: float) -> dict:
    """核心分析引擎：6维度交叉分析"""
    p = data["price"]
    chg = data["change_pct"]
    turn = data["turnover"]
    amp = data["amplitude"]
    yc = data["yclose"]
    op = data["open"]
    hi = data["high"]
    lo = data["low"]

    result = {
        "quote": {
            "name": data["name"],
            "code": data["code"],
            "price": p,
            "yclose": yc,
            "open": op,
            "high": hi,
            "low": lo,
            "change": data["change"],
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
        "score": 50,
    }

    # ════════════════════════════════════════════════
    # 维度1: 价格行为分析
    # ════════════════════════════════════════════════
    price_sig = []

    # 涨跌幅分级
    if chg <= -9.5:
        price_sig.append(("[跌停]", f"跌幅{chg:.2f}%，封死跌停板，极度恐慌"))
    elif chg <= -7:
        price_sig.append(("[暴跌]", f"跌幅{chg:.2f}%，接近跌停，市场恐慌"))
    elif chg <= -5:
        price_sig.append(("[大跌]", f"跌幅{chg:.2f}%，空头强势，趋势破坏"))
    elif chg <= -3:
        price_sig.append(("[中跌]", f"跌幅{chg:.2f}%，空头占优"))
    elif chg <= -1:
        price_sig.append(("[小跌]", f"跌幅{chg:.2f}%，弱势调整"))
    elif chg >= 9.5:
        price_sig.append(("[涨停]", f"涨幅{chg:.2f}%，封死涨停板，极度强势"))
    elif chg >= 7:
        price_sig.append(("[暴涨]", f"涨幅{chg:.2f}%，接近涨停，多头亢奋"))
    elif chg >= 5:
        price_sig.append(("[大涨]", f"涨幅{chg:.2f}%，多头强势突破"))
    elif chg >= 3:
        price_sig.append(("[中涨]", f"涨幅{chg:.2f}%，多头占优"))
    elif chg >= 1:
        price_sig.append(("[小涨]", f"涨幅{chg:.2f}%，温和上涨"))
    else:
        price_sig.append(("[平盘]", f"涨跌幅{chg:.2f}%，窄幅震荡无方向"))

    # 跳空分析
    gap = (op / yc - 1) * 100 if yc else 0
    if abs(gap) > 2.5:
        d = "高开" if gap > 0 else "低开"
        price_sig.append(("[大跳空]", f"{d}{abs(gap):.2f}%，隔夜情绪极端"))
    elif abs(gap) > 1.5:
        d = "高开" if gap > 0 else "低开"
        price_sig.append(("[跳空]", f"{d}{abs(gap):.2f}%，注意缺口回补"))

    # K线形态
    body = abs(p - op)
    total_range = hi - lo
    if total_range > 0:
        up_shadow = hi - max(p, op)
        low_shadow = min(p, op) - lo

        if up_shadow > body * 2 and p < op:
            price_sig.append(("[长上影]", "冲高回落，上方抛压极重"))
        if low_shadow > body * 2 and p > op:
            price_sig.append(("[长下影]", "探底回升，下方承接有力"))
        if up_shadow > total_range * 0.6 and p >= op:
            price_sig.append(("[射击星]", "高位长上影，见顶信号"))
        if body > total_range * 0.8:
            price_sig.append(("[光头]", "单边行情，方向极为明确"))
        if body < total_range * 0.1:
            price_sig.append(("[十字星]", "多空均衡，变盘信号"))
        elif body < total_range * 0.3:
            price_sig.append(("[小K线]", "多空胶着，方向待选择"))

    # 收盘位置
    if hi > lo:
        close_pos = (p - lo) / (hi - lo) * 100
        if close_pos > 95:
            price_sig.append(("[收最高]", "收在日内最高点，极为强势"))
        elif close_pos < 5:
            price_sig.append(("[收最低]", "收在日内最低点，极为弱势"))

    result["dimensions"].append({"name": "价格行为", "signals": price_sig})

    # ════════════════════════════════════════════════
    # 维度2: 量价分析
    # ════════════════════════════════════════════════
    vol_sig = []

    if turn > 20:
        vol_sig.append(("[死亡换手]", f"换手率{turn:.2f}%，极端换手，主力对倒/出货"))
    elif turn > 10:
        vol_sig.append(("[天量]", f"换手率{turn:.2f}%，极端活跃，大资金博弈"))
    elif turn > 7:
        vol_sig.append(("[巨量]", f"换手率{turn:.2f}%，多空激烈交锋"))
    elif turn > 5:
        vol_sig.append(("[放量]", f"换手率{turn:.2f}%，交投活跃"))
    elif turn > 3:
        vol_sig.append(("[温和]", f"换手率{turn:.2f}%，正常交投"))
    elif turn > 1:
        vol_sig.append(("[缩量]", f"换手率{turn:.2f}%，交投清淡"))
    else:
        vol_sig.append(("[地量]", f"换手率{turn:.2f}%，极度冷清，无人问津"))

    amt = data["amount"]
    if amt > 50:
        vol_sig.append(("[天量成交]", f"成交额{amt}亿，超大资金深度参与"))
    elif amt > 10:
        vol_sig.append(("[大额成交]", f"成交额{amt}亿，主力资金活跃"))
    elif amt > 5:
        vol_sig.append(("[放量成交]", f"成交额{amt}亿，资金关注度高"))
    elif amt < 0.1:
        vol_sig.append(("[微量成交]", f"成交额{amt}亿，资金完全忽视"))

    # 量价配合
    if chg < -5 and turn > 8:
        vol_sig.append(("[放量暴跌]", "放量暴跌=危险信号，资金出逃"))
    elif chg > 5 and turn > 8:
        vol_sig.append(("[放量暴涨]", "放量暴涨=追涨信号，但需防出货"))
    elif chg < -3 and turn < 2:
        vol_sig.append(("[缩量下跌]", "缩量下跌=正常回调，抛压不大"))
    elif chg > 3 and turn < 2:
        vol_sig.append(("[缩量上涨]", "缩量上涨=上涨乏力，动量不足"))

    result["dimensions"].append({"name": "量价分析", "signals": vol_sig})

    # ════════════════════════════════════════════════
    # 维度3: 位置分析
    # ════════════════════════════════════════════════
    pos_sig = []

    h52, l52 = data["high_52w"], data["low_52w"]
    if h52 and l52 and h52 > l52:
        pct52 = (p - l52) / (h52 - l52) * 100
        if pct52 > 90:
            pos_sig.append(("[52周顶部]", f"处于52周顶部({pct52:.0f}%)，风险极高"))
        elif pct52 > 75:
            pos_sig.append(("[52周高位]", f"处于52周高位({pct52:.0f}%)，趋势强但追高需谨慎"))
        elif pct52 > 50:
            pos_sig.append(("[52周中上]", f"处于52周中上位置({pct52:.0f}%)，趋势偏强"))
        elif pct52 > 25:
            pos_sig.append(("[52周中下]", f"处于52周中下位置({pct52:.0f}%)，估值合理偏低"))
        elif pct52 > 10:
            pos_sig.append(("[52周低位]", f"处于52周低位({pct52:.0f}%)，超跌区域"))
        else:
            pos_sig.append(("[52周底部]", f"处于52周历史底部({pct52:.0f}%)，极度超跌"))
    else:
        pos_sig.append(("[位置]", "52周数据不可用"))

    # 相对于昨收的位置
    pct_of_yc = (p / yc - 1) * 100 if yc else 0
    if pct_of_yc < -7:
        pos_sig.append(("[近跌停]", "股价濒临跌停"))
    elif pct_of_yc > 7:
        pos_sig.append(("[近涨停]", "股价濒临涨停"))

    result["dimensions"].append({"name": "位置分析", "signals": pos_sig})

    # ════════════════════════════════════════════════
    # 维度4: 风险评估（仅持仓时）
    # ════════════════════════════════════════════════
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

        risk_sig = []
        if pnl_pct <= -10:
            risk_sig.append(("[止损线]", f"浮亏{pnl_pct:.1f}%，已触及止损线，必须执行止损"))
        elif pnl_pct <= -7:
            risk_sig.append(("[危险]", f"浮亏{pnl_pct:.1f}%，接近止损线，密切监控"))
        elif pnl_pct <= -4:
            risk_sig.append(("[亏损]", f"浮亏{pnl_pct:.1f}%，可控范围内，设好止损"))
        elif pnl_pct <= -2:
            risk_sig.append(("[微亏]", f"浮亏{pnl_pct:.1f}%，正常波动"))
        elif pnl_pct >= 15:
            risk_sig.append(("[暴赚]", f"浮盈{pnl_pct:.1f}%，强烈建议移动止盈"))
        elif pnl_pct >= 8:
            risk_sig.append(("[大赚]", f"浮盈{pnl_pct:.1f}%，考虑止盈保护利润"))
        elif pnl_pct >= 4:
            risk_sig.append(("[盈利]", f"浮盈{pnl_pct:.1f}%，可上移止损"))
        elif pnl_pct >= 2:
            risk_sig.append(("[微盈]", f"浮盈{pnl_pct:.1f}%，趋势良好"))

        if shares > 2000:
            risk_sig.append(("[极重仓]", f"持仓{shares}股，仓位极重，流动性风险大"))
        elif shares > 1000:
            risk_sig.append(("[重仓]", f"持仓{shares}股，仓位较重"))

        result["dimensions"].append({"name": "风险评估", "signals": risk_sig})

    # ════════════════════════════════════════════════
    # 维度5: 综合评分
    # ════════════════════════════════════════════════
    score = 50
    reasons = []

    # 涨跌幅打分
    if chg < -7: score -= 25; reasons.append("暴跌-25")
    elif chg < -5: score -= 15; reasons.append("大跌-15")
    elif chg < -3: score -= 8; reasons.append("中跌-8")
    elif chg < -1: score -= 3; reasons.append("小跌-3")
    elif chg > 7: score += 25; reasons.append("暴涨+25")
    elif chg > 5: score += 15; reasons.append("大涨+15")
    elif chg > 3: score += 8; reasons.append("中涨+8")
    elif chg > 1: score += 3; reasons.append("小涨+3")

    # 成交量修正
    if turn > 15 and chg < -5: score -= 15; reasons.append("放量暴跌-15")
    elif turn > 10: score -= 5; reasons.append("高换手-5")

    # 振幅修正
    if amp > 8: score -= 5; reasons.append("高振幅-5")

    # 52周位置修正
    if h52 and l52 and h52 > l52:
        pct52 = (p - l52) / (h52 - l52) * 100
        if pct52 > 90: score -= 5; reasons.append("高位-5")
        elif pct52 < 10: score += 5; reasons.append("低位+5")

    score = max(0, min(100, score))
    if score >= 70:
        label = "偏多"
    elif score >= 45:
        label = "中性"
    elif score >= 25:
        label = "偏空"
    else:
        label = "危险"

    result["score"] = score
    result["verdict"] = {"score": score, "label": label, "reasons": reasons}

    # ════════════════════════════════════════════════
    # 维度6: 情景推演
    # ════════════════════════════════════════════════
    s = shares if shares > 0 else 1000
    # 下跌概率
    if chg < -5 and turn > 8:
        down_prob = "很高"
    elif chg < -3 or turn > 10:
        down_prob = "高"
    elif chg < -1:
        down_prob = "中"
    else:
        down_prob = "低"

    # 反弹概率
    if chg > 5:
        up_prob = "高"
    elif chg > 2:
        up_prob = "中"
    elif chg < -5 and turn > 8:
        up_prob = "低"
    else:
        up_prob = "中"

    result["scenarios"] = [
        {
            "label": "继续下跌/回调",
            "prob": down_prob,
            "trigger": "开盘低于现价且量能不缩",
            "action": "减仓/止损，等企稳信号出现再进",
            "impact": f"亏损 {abs(p*0.97-p)*s:.0f}~{abs(p*0.95-p)*s:.0f}元" if shares > 0 else "观望",
        },
        {
            "label": "横盘整理",
            "prob": "中",
            "trigger": f"价格在 {p*0.98:.3f}~{p*1.02:.3f} 之间缩量",
            "action": "持有不动，观察量能变化",
            "impact": "持仓成本不变" if shares > 0 else "观望",
        },
        {
            "label": "技术反弹/突破",
            "prob": up_prob,
            "trigger": f"放量站稳 {p*1.02:.3f} 上方",
            "action": "持有/轻仓跟进，设好止损",
            "impact": f"盈利 {abs(p*1.03-p)*s:.0f}~{abs(p*1.08-p)*s:.0f}元" if shares > 0 else "可考虑建仓",
        },
    ]

    return result


def format_report(result: dict, show_ads: bool = True) -> str:
    """格式化为可读报告"""
    if "error" in result:
        return f"[错误] {result['error']}"

    q = result["quote"]
    chg_str = f"+{q['change_pct']:.2f}%" if q['change_pct'] >= 0 else f"{q['change_pct']:.2f}%"

    lines = [
        "=" * 55,
        "  StockMind Pro - 完整分析报告",
        "  %s (%s)  |  %s" % (q["name"], q["code"], chg_str),
        "=" * 55,
        "",
        "[行情概览]",
        "  现价: %.3f  昨收: %.3f  开盘: %.3f" % (q["price"], q["yclose"], q["open"]),
        "  最高: %.3f  最低: %.3f  振幅: %.2f%%" % (q["high"], q["low"], q["amplitude"]),
        "  成交: %s手  %s亿  换手: %.2f%%" % (
            "{:,}".format(q["volume"]), q["amount"], q["turnover"]),
    ]

    if q["high_52w"] and q["low_52w"]:
        lines.append("  52周: %.3f ~ %.3f  市值: %.1f亿" % (
            q["low_52w"], q["high_52w"], q["market_cap"]))
    lines.append("")

    # 持仓
    if result["position"]:
        pos = result["position"]
        pnl_icon = "亏" if pos["pnl"] < 0 else "盈"
        lines.append("[持仓状态]")
        lines.append("  持仓: %d股 @ %.3f" % (pos["shares"], pos["entry"]))
        lines.append("  成本: %.1f元  市值: %.1f元" % (pos["cost"], pos["market_value"]))
        lines.append("  盈亏: %+.1f元 (%+.2f%%)" % (pos["pnl"], pos["pnl_pct"]))
        lines.append("  止损: %.3f  距止损: %.1f%%" % (pos["stop_loss"], pos["distance_to_stop"]))
        lines.append("")

    # 多维分析
    lines.append("[多维交叉分析]")
    for dim in result["dimensions"]:
        for icon, text in dim["signals"]:
            lines.append("  %s %s" % (icon, text))
    lines.append("")

    # 评分
    v = result["verdict"]
    lines.append("[综合研判]")
    lines.append("  评分: %d/100 [%s]" % (v["score"], v["label"]))
    lines.append("")

    # 情景
    lines.append("[情景推演与应对]")
    for s in result["scenarios"]:
        lines.append("  [%s] 概率:%s" % (s["label"], s["prob"]))
        lines.append("    触发: %s" % s["trigger"])
        lines.append("    应对: %s" % s["action"])
        lines.append("    影响: %s" % s["impact"])
        lines.append("")

    # 纪律
    lines.extend([
        "[核心纪律]",
        "  1. 止损不犹豫，保本金才能打下一枪",
        "  2. 不抄底不追高，等确认信号再出手",
        "  3. 单票仓位不超总资产40%",
        "  4. 市场是流动的机会，不是固定的持仓",
        "  5. 每一次交易都要有明确理由",
        "",
    ])

    if show_ads:
        lines.extend([
            "-" * 55,
            "  StockMind Pro - 支持全市场5000+ A股/ETF",
            "  买断价: $49.9 | 永久使用 | 微信/支付宝购买",
            "-" * 55,
        ])

    return "\n".join(lines)
