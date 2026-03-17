# 图片批量处理器

> 一站式图片处理解决方案，格式转换、压缩、水印全搞定

## ✨ 功能特性

- 🔄 **格式转换** - 支持 JPG、PNG、GIF、WebP、BMP 互转
- 📐 **尺寸调整** - 批量调整图片大小，保持比例
- 🗜️ **智能压缩** - 减小文件体积，保持画质
- 🏷️ **批量重命名** - 按规则批量重命名
- 💧 **文字水印** - 批量添加水印
- 📊 **信息查看** - 查看图片详细参数

## 🚀 快速开始

### 安装依赖

```bash
pip install Pillow typer rich
```

### 基本用法

```bash
# 1. 格式转换（JPG → PNG）
python image_processor.py convert *.jpg --format png

# 2. 调整尺寸（宽度设为800，高度自适应）
python image_processor.py resize *.jpg --width 800

# 3. 压缩图片（质量75%）
python image_processor.py compress *.jpg --quality 75

# 4. 批量重命名
python image_processor.py rename *.jpg --pattern "photo_{index:03d}"

# 5. 添加水印
python image_processor.py watermark *.jpg --text "©贾维斯工作室"

# 6. 查看图片信息
python image_processor.py info *.jpg
```

## 📖 详细示例

### 场景1：网站图片优化

```bash
# 将相机原图压缩并调整尺寸，适合网站使用
python image_processor.py resize *.jpg \
    --width 1200 \
    --output ./web_images/

python image_processor.py compress ./web_images/*.jpg \
    --quality 80 \
    --output ./optimized/
```

### 场景2：电商产品图处理

```bash
# 统一尺寸并添加水印
python image_processor.py resize product*.jpg \
    --width 800 --height 800 \
    --output ./resized/

python image_processor.py watermark ./resized/*.jpg \
    --text "贾维斯商城" \
    --position bottom-right \
    --opacity 100
```

### 场景3：照片批量整理

```bash
# 按序号重命名照片
python image_processor.py rename IMG_*.jpg \
    --pattern "旅行_2025_{index:04d}" \
    --start 1
```

### 场景4：转换为 WebP 格式

```bash
# 批量转换为 WebP，体积更小
python image_processor.py convert *.png --format webp --quality 85
```

## 💰 商业授权

本工具采用 **MIT 开源协议**，可自由用于个人和商业用途。

如需**定制功能**或**技术支持**，欢迎联系：
- 知乎：[@贾维斯工作室](https://www.zhihu.com/people/hok7n4ms)

## 📝 更新日志

### v1.0.0 (2026-03-17)
- ✅ 初始版本发布
- ✅ 支持格式转换、尺寸调整、压缩、重命名、水印、信息查看
