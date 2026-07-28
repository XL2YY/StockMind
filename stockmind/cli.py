#!/usr/bin/env python3
"""
StockMind 命令行入口

使用:
  stockmind <代码>              # 免费版分析
  stockmind pro <代码> [选项]    # Pro版介绍（需激活）
"""

import argparse
import sys
import io
from . import __version__, __pro_price__
from .fetcher import fetch_quote
from .analyzer import quick_analysis, format_report

# 修复Windows GBK编码问题
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


BANNER = """
  ========================================
     StockMind  -  AI 思维引擎
     A股/ETF 智能分析工具  v%s
  ========================================
""" % __version__


def cmd_free(code):
    """免费版：基础分析"""
    print(BANNER)
    result = quick_analysis(code)
    print(format_report(result))


def cmd_pro(args):
    """Pro版入口（需要激活）"""
    print(BANNER)
    print("[提示] StockMind Pro 需要激活后才能使用完整功能")
    print("")
    print("  Pro版包含:")
    print("  - 完整6维分析引擎（价格+量价+K线+位置+风险+推演）")
    print("  - 持仓盈亏管理（多股票组合）")
    print("  - 止损预警（钉钉/微信推送）")
    print("  - 三种情景推演（涨/跌/震 + 应对方案）")
    print("  - 历史分析记录 + 报告导出")
    print("")
    print("  买断价格: %s" % __pro_price__)
    print("  购买方式: 微信/支付宝支付后获取激活码")
    print("")
    print("  联系购买: GitHub Issues 或 发送邮件至 stockmind@example.com")
    code = args.code if hasattr(args, 'code') else ''
    if code:
        print("")
        print("  当前目标: %s" % code)
        print("  使用 --hold 参数可分析持仓: stockmind pro %s --hold 1300@1.136" % code)
    print("")


def main():
    # 没有参数 → 显示帮助
    if len(sys.argv) == 1 or sys.argv[1] in ("-h", "--help"):
        print(BANNER)
        print("用法:")
        print("  stockmind <代码>                   免费版分析")
        print("  stockmind pro <代码> [选项]          Pro版介绍")
        print("")
        print("示例:")
        print("  stockmind 159246")
        print("  stockmind pro 159246")
        print("  stockmind 000333")
        print("")
        print("版本: v%s  |  Pro价格: %s" % (__version__, __pro_price__))
        return

    # pro 子命令
    if sys.argv[1] == "pro":
        parser = argparse.ArgumentParser(description="StockMind Pro")
        parser.add_argument("code", help="股票/ETF代码")
        parser.add_argument("--hold", "-H", type=str, help="持仓格式: 股数@成本价, 如 1300@1.136")
        parser.add_argument("--alert", "-A", type=float, help="设置止损价")
        parser.add_argument("--push", "-P", type=str, help="推送方式: dingtalk/wechat")
        args = parser.parse_args(sys.argv[2:])
        cmd_pro(args)
        return

    # 默认：免费版
    code = sys.argv[1]
    if code.startswith("-"):
        print(BANNER)
        print("未知选项: %s" % code)
        print("用法: stockmind <代码>, 如 stockmind 159246")
        return

    cmd_free(code)


if __name__ == "__main__":
    main()
