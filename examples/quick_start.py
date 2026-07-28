"""
StockMind 使用示例
"""

# ── 示例1：免费版分析 ──
from stockmind.fetcher import fetch_quote
from stockmind.analyzer import quick_analysis, format_report

# 获取实时数据
data = fetch_quote("159246")
print(f"{data['name']} 现价: {data['price']}")

# 快速分析
result = quick_analysis("159246")
print(format_report(result))


# ── 示例2：Pro版持仓管理（需激活） ──
from stockmind.pro import Portfolio

portfolio = Portfolio()
portfolio.add("159246", "创业板人工智能ETF富国", 1300, 1.136)
print(portfolio.list_all())
