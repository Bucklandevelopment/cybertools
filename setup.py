#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="scanet",
    version="1.0.0",
    author="UTOP.IA SECos",
    description="WiFi Security Analysis Network Tool - Analyzes airodump-ng CSV files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/UTOP.IA/SECos/scanet",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "networkx>=3.1",
        "pdfkit>=1.0.0",
        "click>=8.0.0",
        "jinja2>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "scanet=scanet.cli:cli",
        ],
    },
)