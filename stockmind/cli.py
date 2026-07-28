#!/usr/bin/env python3
"""
StockMind 命令行入口

用法:
  stockmind <代码>               免费版基础分析（任意A股/ETF）
  stockmind pro <代码>           Pro版完整分析（需激活）
  stockmind pro <代码> --hold N@P  带持仓分析
  stockmind watchlist add <代码>   添加自选股
  stockmind watchlist list         查看自选股
  stockmind watchlist analyze      批量分析自选股
  stockmind compare <代码1> <代码2> 多股对比
  stockmind hot                    热门股票扫描
"""

import argparse
import sys
import io
from . import __version__, __pro_price__
from .fetcher import fetch_quote
from .analyzer import quick_analysis, format_report as free_format

# 修复Windows GBK
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


BANNER = """
  ========================================
     StockMind  -  AI 思维引擎
     支持全市场5000+ A股/ETF  v%s
  ========================================
""" % __version__


def cmd_free(code):
    """免费版：分析任意一只股票/ETF"""
    print(BANNER)
    result = quick_analysis(code)
    print(free_format(result))


def cmd_pro(args):
    """Pro版：完整6维分析"""
    try:
        from .pro import analyze_stock, analyze_with_position, format_report
        from .pro.portfolio import validate_license
    except ImportError:
        print(BANNER)
        print("[错误] Pro版模块未安装。请购买后获取完整版。")
        return

    has_license = validate_license()
    if not has_license:
        print(BANNER)
        print("[提示] StockMind Pro 需要激活后才能使用完整功能")
        print("")
        print("  Pro版包含 (适用于任意A股/ETF):")
        print("  - 完整6维分析引擎（价格+量价+趋势+位置+风险+推演）")
        print("  - 持仓盈亏管理（多股票组合）")
        print("  - 止损预警（钉钉/微信推送）")
        print("  - 自选股管理 + 批量分析 + 多股对比")
        print("  - 每日热门扫描")
        print("")
        print("  买断价格: %s" % __pro_price__)
        print("  购买方式: 闲鱼搜索用户「下了一夜雨」下单")
        print("  下单后通过闲鱼聊天获取激活码")
        print("")
        # 演示模式：展示但不给完整分析
        print("  [演示模式] 免费版可查询任意股票基础数据:")
        code = args.code
        data = fetch_quote(code)
        if "error" not in data:
            print("  %s (%s)  现价: %.3f  涨跌: %+.2f%%" % (
                data["name"], data["code"], data["price"], data["change_pct"]))
        return

    # 已激活 → 完整分析
    if args.hold:
        try:
            shares, entry = args.hold.split("@")
            shares, entry = int(shares), float(entry)
            result = analyze_with_position(args.code, shares, entry)
        except ValueError:
            print("[错误] --hold 格式错误，应为: 股数@成本价, 如 1300@1.136")
            return
    else:
        result = analyze_stock(args.code)

    print()
    print(format_report(result))


def cmd_watchlist(args):
    """自选股管理"""
    try:
        from .pro import Watchlist
        from .pro.engine import format_report
    except ImportError:
        print("[错误] Pro版模块未安装")
        return

    wl = Watchlist()

    if args.action == "add":
        code = args.code
        data = fetch_quote(code)
        name = data.get("name", "") if "error" not in data else ""
        wl.add(code, name, args.note or "")
        print("[自选股] 已添加: %s (%s)" % (name or code, code))

    elif args.action == "remove":
        wl.remove(args.code)
        print("[自选股] 已移除: %s" % args.code)

    elif args.action == "list":
        stocks = wl.list_all()
        if not stocks:
            print("[自选股] 列表为空。使用 stockmind watchlist add <代码> 添加")
            return
        print("[自选股] 共 %d 只" % len(stocks))
        print("  %-8s  %-16s  %s" % ("代码", "名称", "添加时间"))
        print("  " + "-" * 45)
        for s in stocks:
            print("  %-8s  %-16s  %s" % (s["code"], s["name"][:12], s.get("added", "")))

    elif args.action == "analyze":
        print(BANNER)
        results = wl.batch_analyze()
        print("[批量分析] 共 %d 只股票\n" % len(results))
        for r in results:
            if "error" in r:
                print("  [%s] 分析失败: %s" % (r.get("code", "?"), r["error"]))
            else:
                q = r["quote"]
                chg = "%+.2f%%" % q["change_pct"]
                print("  %-6s %-12s 现价:%.3f %s 评分:%d/100 [%s]" % (
                    q["code"], q["name"][:8], q["price"], chg,
                    r["score"], r["verdict"]["label"]))

    elif args.action == "compare":
        wl2 = Watchlist()
        if args.codes:
            codes = args.codes
        else:
            codes = [s["code"] for s in wl2.list_all()]
        if not codes:
            print("[对比] 请先添加自选股或指定代码")
            return
        result = wl2.compare(codes)
        print(wl2.format_compare(codes))


def cmd_compare(args):
    """多股对比"""
    try:
        from .pro import Watchlist
    except ImportError:
        print("[错误] Pro版模块未安装")
        return

    wl = Watchlist()
    codes = args.codes
    print()
    print(wl.format_compare(codes))


def cmd_activate(args):
    """激活Pro版"""
    from pathlib import Path
    lic_dir = Path.home() / ".stockmind"
    lic_dir.mkdir(parents=True, exist_ok=True)
    lic_file = lic_dir / "license.key"
    lic_file.write_text(args.key.strip(), encoding="utf-8")
    print("[StockMind] Pro版激活成功！激活码: %s" % args.key[:20] + "...")
    print("[StockMind] 现在可以使用 stockmind pro <代码> 体验完整功能")


def cmd_hot():
    """热门扫描"""
    try:
        from .pro import Watchlist, hot_stocks
        from .pro.engine import analyze_stock
    except ImportError:
        print("[错误] Pro版模块未安装")
        return

    print(BANNER)
    print("[热门扫描] 主要ETF和龙头股实时状态\n")
    stocks = hot_stocks(15)
    print("  %-8s %-16s %8s %8s %6s %s" % (
        "代码", "名称", "现价", "涨跌", "评分", "研判"))
    print("  " + "-" * 55)
    for r in stocks:
        q = r["quote"]
        chg = "%+.2f%%" % q["change_pct"]
        print("  %-8s %-16s %8.3f %8s %5d %s" % (
            q["code"], q["name"][:12], q["price"], chg,
            r["score"], r["verdict"]["label"]))
    print()


def main():
    if len(sys.argv) == 1 or sys.argv[1] in ("-h", "--help"):
        print(BANNER)
        print("用法:")
        print("  stockmind <代码>                  分析任意股票/ETF（免费版）")
        print("  stockmind pro <代码> [--hold N@P]  Pro版完整分析")
        print("  stockmind watchlist add <代码>     添加自选股")
        print("  stockmind watchlist list           查看自选股")
        print("  stockmind watchlist analyze        批量分析自选股")
        print("  stockmind compare <A> <B> [C..]    多股对比")
        print("  stockmind hot                      热门股票扫描")
        print("  stockmind activate <激活码>         激活Pro版")
        print("")
        print("示例:")
        print("  stockmind 159246           # 分析创业板人工智能ETF")
        print("  stockmind 000333           # 分析美的集团")
        print("  stockmind 600519           # 分析贵州茅台")
        print("  stockmind pro 159246 --hold 1300@1.136")
        print("  stockmind compare 159246 159995")
        print("  stockmind hot")
        print("")
        print("版本: v%s  |  Pro: %s" % (__version__, __pro_price__))
        return

    # Pro版
    if sys.argv[1] == "pro":
        parser = argparse.ArgumentParser(description="StockMind Pro")
        parser.add_argument("code", help="股票/ETF代码")
        parser.add_argument("--hold", "-H", type=str, help="持仓: 股数@成本价")
        args = parser.parse_args(sys.argv[2:])
        cmd_pro(args)
        return

    # watchlist
    if sys.argv[1] == "watchlist":
        parser = argparse.ArgumentParser(description="自选股管理")
        parser.add_argument("action", choices=["add", "remove", "list", "analyze", "compare"])
        parser.add_argument("code", nargs="?", help="股票代码")
        parser.add_argument("--note", "-n", type=str, default="", help="备注")
        parser.add_argument("codes", nargs="*", help="对比用代码列表")
        args = parser.parse_args(sys.argv[2:])
        cmd_watchlist(args)
        return

    # compare
    if sys.argv[1] == "compare":
        if len(sys.argv) < 3:
            print("用法: stockmind compare <代码1> <代码2> [代码3...]")
            return
        codes = sys.argv[2:]
        class Args: pass
        args = Args()
        args.codes = codes
        cmd_compare(args)
        return

    # activate
    if sys.argv[1] == "activate":
        if len(sys.argv) < 3:
            print("用法: stockmind activate <激活码>")
            print("示例: stockmind activate SM-6127D078-853B8F44-8BDF56D5")
            return
        class Args: pass
        args = Args()
        args.key = sys.argv[2]
        cmd_activate(args)
        return

    # hot
    if sys.argv[1] == "hot":
        cmd_hot()
        return

    # 默认：免费版（支持任意A股/ETF代码）
    code = sys.argv[1]
    if code.startswith("-"):
        print(BANNER)
        print("未知选项: %s" % code)
        print("用法: stockmind <代码>, 如 stockmind 159246")
        return

    cmd_free(code)


if __name__ == "__main__":
    main()
