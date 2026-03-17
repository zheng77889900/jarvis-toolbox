# PDF 智能工具箱

> 一站式 PDF 处理解决方案，合并、拆分、加密、解密全搞定

## ✨ 功能特性

- 📑 **PDF 合并** - 多个文件合并为一个，支持书签
- ✂️ **PDF 拆分** - 按页码或范围拆分
- 🔒 **PDF 加密** - 设置密码保护
- 🔓 **PDF 解密** - 移除密码保护（需知道密码）
- 📊 **PDF 信息** - 查看文件元数据、页数、尺寸

## 🚀 快速开始

### 安装依赖

```bash
pip install PyPDF2 typer rich
```

### 基本用法

```bash
# 1. 合并多个 PDF
python pdf_tools.py merge file1.pdf file2.pdf file3.pdf -o merged.pdf

# 2. 拆分 PDF（每页单独保存）
python pdf_tools.py split input.pdf -o ./output/

# 3. 拆分指定页码
python pdf_tools.py split input.pdf -p "1-5,8,10-12"

# 4. 查看 PDF 信息
python pdf_tools.py info input.pdf

# 5. 加密 PDF
python pdf_tools.py encrypt input.pdf -p "mypassword"

# 6. 解密 PDF
python pdf_tools.py decrypt input.pdf -p "mypassword"
```

## 📖 详细示例

### 场景1：合并合同文件

```bash
# 将多份合同扫描件合并为一个文件
python pdf_tools.py merge \
    合同-第1页.pdf \
    合同-第2页.pdf \
    合同-第3页.pdf \
    -o 完整合同.pdf \
    --bookmark
```

### 场景2：提取报告中的特定页面

```bash
# 只提取报告的第5-10页和封面
python pdf_tools.py split 年度报告.pdf \
    -p "1,5-10" \
    -o ./提取页面/
```

### 场景3：给敏感文件加密

```bash
# 给财务报表添加密码
python pdf_tools.py encrypt 财务报表.pdf \
    -p "MySecurePass123" \
    -o 财务报表-加密.pdf
```

### 场景4：批量处理文件夹中的 PDF

```bash
# 合并文件夹中所有 PDF
python pdf_tools.py merge *.pdf -o 合并结果.pdf
```

## 💰 商业授权

本工具采用 **MIT 开源协议**，可自由用于个人和商业用途。

如需**定制功能**或**技术支持**，欢迎联系：
- 知乎：[@贾维斯工作室](https://www.zhihu.com/people/hok7n4ms)

## 📝 更新日志

### v1.0.0 (2026-03-17)
- ✅ 初始版本发布
- ✅ 支持合并、拆分、加密、解密、信息查看
