"""
StockMind Pro — 完整AI股票分析引擎
适用于全市场5000+ A股和ETF

功能:
  - 完整6维分析（价格+量价+位置+风险+评分+情景推演）
  - 持仓盈亏管理 + 止损预警
  - 自选股管理 + 批量分析 + 多股对比
  - 钉钉/微信消息推送
  - 每日热门扫描

激活: 将激活码保存到 ~/.stockmind/license.key
购买: ¥49.9 买断永久使用
"""

from .engine import analyze_stock, analyze_with_position, format_report
from .portfolio import Portfolio, validate_license
from .alerter import AlertManager
from .pusher import PushManager
from .watchlist import Watchlist, hot_stocks
