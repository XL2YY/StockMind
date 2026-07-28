"""
StockMind Pro — 完整6维分析引擎
包含: 持仓管理、情景推演、止损预警、钉钉推送

激活方式: 将收到的激活码保存到 ~/.stockmind/license.key
购买价格: ¥49.9（买断永久使用）
"""

from .portfolio import Portfolio, validate_license
from .scenario import analyze_full, format_pro_report
from .alerter import AlertManager
from .pusher import PushManager
