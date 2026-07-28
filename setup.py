#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="stockmind",
    version="1.0.0",
    description="StockMind - AI股票思维分析引擎 | A股/ETF实时智能分析",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="StockMind Team",
    author_email="stockmind@example.com",
    url="https://github.com/yourname/stockmind",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "stockmind=stockmind.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
)
