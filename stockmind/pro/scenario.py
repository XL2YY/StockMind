"""
情景推演模块（Pro版） — 兼容层
实际逻辑已迁移到 engine.py
"""

from .engine import analyze_stock, analyze_with_position, format_report

# 保留旧接口兼容
analyze_full = analyze_with_position
format_pro_report = format_report
