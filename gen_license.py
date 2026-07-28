#!/usr/bin/env python3
"""
StockMind 激活码生成器 · 仅供卖家使用
======================================
生成并管理 Pro 版激活码，买家付款后用这个工具生成激活码发给他们。

用法:
  python gen_license.py new                 生成一个新激活码
  python gen_license.py new 3              批量生成3个
  python gen_license.py list                查看所有已生成的激活码
  python gen_license.py verify SM-xxxx-xxxx-xxxx  验证激活码是否有效
  python gen_license.py revoke SM-xxxx-xxxx-xxxx  吊销某个激活码
"""

import hashlib
import json
import secrets
import sys
import time
from datetime import datetime
from pathlib import Path


DB_FILE = Path.home() / ".stockmind" / "licenses_db.json"


def load_db() -> dict:
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    return {"counter": 0, "licenses": []}


def save_db(db: dict):
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    DB_FILE.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_key(seed: str = "") -> str:
    """生成格式: SM-XXXXXXXX-XXXXXXXX-XXXXXXXX"""
    raw = secrets.token_hex(12) + seed
    h = hashlib.sha256(raw.encode()).hexdigest()
    parts = [h[i:i+8].upper() for i in range(0, 24, 8)]
    return f"SM-{parts[0]}-{parts[1]}-{parts[2]}"


def cmd_new(count: int = 1):
    db = load_db()
    for _ in range(count):
        key = generate_key(str(time.time_ns()))
        db["counter"] += 1
        db["licenses"].append({
            "id": db["counter"],
            "key": key,
            "status": "active",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "activated": None,
            "activated_by": None,
        })
        print(f"  [{db['counter']}] {key}  [状态: 未激活]")
    save_db(db)
    print(f"\n共生成 {count} 个激活码，已保存到 {DB_FILE}")
    print("发送给买家后，买家执行: stockmind activate %s" % key)


def cmd_list():
    db = load_db()
    if not db["licenses"]:
        print("暂无激活码")
        return
    print("ID  | 激活码                       | 状态      | 激活时间       | 买家")
    print("-" * 70)
    for lic in db["licenses"]:
        status = "[已用]" if lic["status"] == "used" else "[有效]"
        act_time = lic["activated"][:16] if lic["activated"] else "-"
        buyer = lic["activated_by"][:12] if lic["activated_by"] else "-"
        print(f"{lic['id']:3d}  | {lic['key']}  | {status}  | {act_time}  | {buyer}")
    
    active = sum(1 for l in db["licenses"] if l["status"] == "active")
    used = sum(1 for l in db["licenses"] if l["status"] == "used")
    print(f"\n总计: {len(db['licenses'])} 个 | 有效: {active} 个 | 已用: {used} 个")


def cmd_verify(key: str):
    db = load_db()
    for lic in db["licenses"]:
        if lic["key"] == key:
            if lic["status"] == "active":
                print(f"[有效] 激活码 {key} 尚未使用")
                return True
            else:
                print(f"[已用] 激活码 {key} 已被 {lic.get('activated_by','?')} 于 {lic.get('activated','?')} 激活")
                return False
    print(f"[无效] 激活码 {key} 不存在")
    return False


def cmd_revoke(key: str):
    db = load_db()
    for lic in db["licenses"]:
        if lic["key"] == key:
            if lic["status"] == "active":
                lic["status"] = "revoked"
                save_db(db)
                print(f"[已吊销] 激活码 {key}")
            else:
                print(f"[错误] 该激活码状态为 {lic['status']}，不能吊销")
            return
    print(f"[错误] 激活码 {key} 不存在")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    if cmd == "new":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        cmd_new(count)
    elif cmd == "list":
        cmd_list()
    elif cmd == "verify" and len(sys.argv) > 2:
        cmd_verify(sys.argv[2])
    elif cmd == "revoke" and len(sys.argv) > 2:
        cmd_revoke(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
