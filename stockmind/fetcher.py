"""
数据获取模块（免费版）
从腾讯行情API获取A股/ETF实时数据
"""

from urllib.request import urlopen, Request


def fetch_quote(code: str) -> dict:
    """获取实时行情数据"""
    market = "sz" if code.startswith(("15", "00", "30", "12")) else "sh"
    url = f"http://qt.gtimg.cn/q={market}{code}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urlopen(req, timeout=10).read()
    text = resp.decode("gbk", errors="replace")

    if not text or "=" not in text:
        return {"error": f"无法获取 {code} 的行情数据"}

    raw = text.split('="')[1].split('"')[0] if '"=' in text else text.split("=", 1)[1].strip('";\n')
    fields = raw.split("~")

    if len(fields) < 40:
        return {"error": f"行情数据不完整: {len(fields)} 个字段"}

    try:
        return {
            "code": code,
            "name": fields[1],
            "price": float(fields[3]) if fields[3] else 0,
            "yclose": float(fields[4]) if fields[4] else 0,
            "open": float(fields[5]) if fields[5] else 0,
            "volume": int(fields[6]) if fields[6] else 0,
            "high": float(fields[33]) if fields[33] else 0,
            "low": float(fields[34]) if fields[34] else 0,
            "change": float(fields[31]) if fields[31] else 0,
            "change_pct": float(fields[32]) if fields[32] else 0,
            "amount": round(float(fields[37]) / 10000, 2) if fields[37] else 0,
            "turnover": float(fields[38]) if fields[38] else 0,
            "amplitude": float(fields[43]) if fields[43] else 0,
            "market_cap": float(fields[44]) if fields[44] else 0,
            "high_52w": float(fields[47]) if fields[47] else 0,
            "low_52w": float(fields[48]) if fields[48] else 0,
        }
    except (ValueError, IndexError) as e:
        return {"error": f"数据解析失败: {e}"}


def search_stock(keyword: str) -> list:
    """搜索股票（简易版，按代码匹配）"""
    # 免费版只提供基础的代码搜索
    return [{"code": keyword, "name": "请使用正确代码"}]
