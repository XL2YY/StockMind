# StockMind Pro 安装与激活指南

> 感谢购买 StockMind Pro！请按以下步骤操作。

## 第1步：下载代码

**方式A：从 GitHub 下载（推荐）**
```bash
git clone https://github.com/你的用户名/StockMind.git
cd StockMind
```

**方式B：下载 ZIP 压缩包**
- 打开卖家发给你的仓库地址
- 点击绿色 "Code" 按钮 → "Download ZIP"
- 解压到某个文件夹

## 第2步：安装

```bash
# 进入项目目录
cd StockMind

# 安装（任选一种）
pip install -e .              # 方式1：以开发模式安装
# 或者直接用
python -m stockmind.cli       # 方式2：不用安装，直接执行
```

## 第3步：激活 Pro 版

把卖家发给你的激活码用以下命令激活：

```bash
# Windows / Mac / Linux 都支持
stockmind activate SM-XXXX-XXXX-XXXX
```

看到 `[StockMind] Pro版激活成功！` 就说明激活成功了！

验证激活：
```bash
stockmind pro 159246
```

如果看到完整的6维分析报告（不是"需要激活"的提示），就说明激活成功了！

## 第4步：开始使用

```bash
# 分析任意股票
stockmind 600519          # 贵州茅台
stockmind 300750          # 宁德时代
stockmind 159246          # 创业板人工智能ETF

# 带持仓分析
stockmind pro 159246 --hold 1300@1.136

# 自选股管理
stockmind watchlist add 600519
stockmind watchlist analyze

# 多股对比
stockmind compare 159246 159995 588000

# 热门扫描
stockmind hot
```

## 遇到问题？

- 检查 Python 版本：`python --version`（需要 3.8 以上）
- 检查激活码是否保存正确：`cat ~/.stockmind/license.key`（应该显示 SM-开头）
- 联系卖家微信：stockmind_pro
