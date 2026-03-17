# Excel 批量处理器

> 一键处理海量 Excel 文件，告别重复劳动

## ✨ 功能特性

- 🔄 **格式转换** - Excel ↔ CSV ↔ JSON 批量互转
- 📊 **智能合并** - 多文件合并，自动处理表头
- 🧹 **数据清洗** - 去空行、去重、去空格
- 📈 **文件分析** - 快速查看文件结构和统计信息

## 🚀 快速开始

### 安装依赖

```bash
pip install pandas openpyxl typer rich
```

### 基本用法

```bash
# 1. 批量转换格式
python excel_processor.py convert ./data --format csv

# 2. 合并多个文件
python excel_processor.py merge ./data --output merged.xlsx

# 3. 清洗数据
python excel_processor.py clean data.xlsx --remove-duplicates

# 4. 查看文件信息
python excel_processor.py info data.xlsx
```

## 📖 详细示例

### 场景1：财务月度报表合并

```bash
# 将12个月的报表合并为一个文件
python excel_processor.py merge ./月度报表 \
    --output 2025年度汇总.xlsx \
    --pattern "2025-*.xlsx"
```

### 场景2：系统导出数据清洗

```bash
# 清洗从ERP系统导出的数据
python excel_processor.py clean export.xlsx \
    --output cleaned.xlsx \
    --remove-empty \
    --remove-duplicates \
    --trim-spaces
```

### 场景3：批量转换为CSV导入数据库

```bash
# 递归转换所有Excel为CSV
python excel_processor.py convert ./data \
    --format csv \
    --recursive \
    --output ./csv_export
```

## 💰 商业授权

本工具采用 **MIT 开源协议**，可自由用于个人和商业用途。

如需**定制功能**或**技术支持**，欢迎联系：
- 知乎：[贾维斯工作室](https://zhuanlan.zhihu.com/p/17805879591)

## 📝 更新日志

### v1.0.0 (2026-03-17)
- ✅ 初始版本发布
- ✅ 支持格式转换、合并、清洗、信息查看
