"""
图片批量处理器
功能：格式转换、压缩、调整尺寸、批量重命名、添加水印
作者：贾维斯
版本：1.0.0
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import io

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="图片批量处理器 - 让图片处理更高效")
console = Console()

# 尝试导入 PIL，如果失败则提示安装
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    console.print("[yellow]警告：Pillow 未安装，图片处理功能不可用[/yellow]")
    console.print("[blue]请运行：pip install Pillow[/blue]")


def check_pil():
    """检查 Pillow 是否可用"""
    if not PIL_AVAILABLE:
        console.print("[red]错误：Pillow 库未安装[/red]")
        console.print("[yellow]请运行：pip install Pillow[/yellow]")
        raise typer.Exit(1)


def get_image_files(folder: Path, recursive: bool = False) -> List[Path]:
    """获取文件夹中的所有图片文件"""
    extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    if recursive:
        files = [f for f in folder.rglob("*") if f.suffix.lower() in extensions]
    else:
        files = [f for f in folder.glob("*") if f.suffix.lower() in extensions]
    
    return sorted(files)


def get_image_info(image_path: Path) -> dict:
    """获取图片信息"""
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'width': img.width,
                'height': img.height,
                'size': image_path.stat().st_size
            }
    except Exception as e:
        return {'error': str(e)}


@app.command()
def convert(
    input_files: List[Path] = typer.Argument(..., help="输入图片文件（可多个）"),
    output_format: str = typer.Option("jpg", "--format", "-f", help="输出格式: jpg, png, gif, webp, bmp"),
    output_folder: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件夹"),
    quality: int = typer.Option(85, "--quality", "-q", help="JPEG/WebP 质量 (1-100)"),
):
    """批量转换图片格式"""
    check_pil()
    
    valid_files = []
    for f in input_files:
        if f.exists():
            valid_files.append(f)
        else:
            console.print(f"[yellow]跳过不存在文件: {f}[/yellow]")
    
    if not valid_files:
        console.print("[red]错误：没有有效的输入文件[/red]")
        raise typer.Exit(1)
    
    output_folder = output_folder or valid_files[0].parent / "converted"
    output_folder.mkdir(exist_ok=True)
    
    console.print(f"[blue]准备转换 {len(valid_files)} 个文件为 {output_format.upper()} 格式...[/blue]")
    
    success_count = 0
    failed_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("转换中...", total=len(valid_files))
        
        for img_file in valid_files:
            progress.update(task, description=f"处理: {img_file.name}")
            
            try:
                with Image.open(img_file) as img:
                    # 转换为 RGB（如果是RGBA且目标格式不支持透明）
                    if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # 生成输出文件名
                    output_file = output_folder / f"{img_file.stem}.{output_format}"
                    
                    # 保存
                    save_kwargs = {}
                    if output_format.lower() in ['jpg', 'jpeg']:
                        save_kwargs['quality'] = quality
                        save_kwargs['optimize'] = True
                    elif output_format.lower() == 'webp':
                        save_kwargs['quality'] = quality
                    elif output_format.lower() == 'png':
                        save_kwargs['optimize'] = True
                    
                    img.save(output_file, **save_kwargs)
                    success_count += 1
                    
            except Exception as e:
                failed_files.append((img_file.name, str(e)))
            
            progress.advance(task)
    
    # 显示结果
    table = Table(title="转换结果")
    table.add_column("项目", style="cyan")
    table.add_column("数值", style="magenta")
    
    table.add_row("成功", str(success_count))
    table.add_row("失败", str(len(failed_files)))
    table.add_row("总计", str(len(valid_files)))
    table.add_row("输出格式", output_format.upper())
    table.add_row("输出文件夹", str(output_folder))
    
    console.print(table)
    
    if failed_files:
        console.print("\n[red]失败的文件：[/red]")
        for name, error in failed_files[:5]:
            console.print(f"  - {name}: {error}")
        if len(failed_files) > 5:
            console.print(f"  ... 还有 {len(failed_files) - 5} 个")


@app.command()
def resize(
    input_files: List[Path] = typer.Argument(..., help="输入图片文件"),
    width: Optional[int] = typer.Option(None, "--width", "-w", help="目标宽度"),
    height: Optional[int] = typer.Option(None, "--height", "-h", help="目标高度"),
    scale: Optional[float] = typer.Option(None, "--scale", "-s", help="缩放比例 (0.1-10.0)"),
    output_folder: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件夹"),
    keep_ratio: bool = typer.Option(True, "--keep-ratio/--no-keep-ratio", help="保持宽高比"),
):
    """批量调整图片尺寸"""
    check_pil()
    
    if not width and not height and not scale:
        console.print("[red]错误：请指定 --width、--height 或 --scale[/red]")
        raise typer.Exit(1)
    
    valid_files = [f for f in input_files if f.exists()]
    if not valid_files:
        console.print("[red]错误：没有有效的输入文件[/red]")
        raise typer.Exit(1)
    
    output_folder = output_folder or valid_files[0].parent / "resized"
    output_folder.mkdir(exist_ok=True)
    
    console.print(f"[blue]准备调整 {len(valid_files)} 个图片的尺寸...[/blue]")
    
    success_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("调整中...", total=len(valid_files))
        
        for img_file in valid_files:
            progress.update(task, description=f"处理: {img_file.name}")
            
            try:
                with Image.open(img_file) as img:
                    original_width, original_height = img.size
                    
                    # 计算新尺寸
                    if scale:
                        new_width = int(original_width * scale)
                        new_height = int(original_height * scale)
                    elif width and height and not keep_ratio:
                        new_width, new_height = width, height
                    elif width:
                        new_width = width
                        new_height = int(original_height * (width / original_width))
                    elif height:
                        new_height = height
                        new_width = int(original_width * (height / original_height))
                    else:
                        new_width, new_height = original_width, original_height
                    
                    # 调整尺寸
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # 保存
                    output_file = output_folder / f"{img_file.stem}_resized{img_file.suffix}"
                    resized_img.save(output_file)
                    success_count += 1
                    
            except Exception as e:
                console.print(f"[red]处理 {img_file.name} 失败: {e}[/red]")
            
            progress.advance(task)
    
    console.print(f"\n[green]✅ 完成！成功调整 {success_count} 个图片[/green]")
    console.print(f"输出文件夹: {output_folder}")


@app.command()
def compress(
    input_files: List[Path] = typer.Argument(..., help="输入图片文件"),
    quality: int = typer.Option(75, "--quality", "-q", help="压缩质量 (1-100，越小体积越小)"),
    max_size: Optional[int] = typer.Option(None, "--max-size", "-m", help="最大文件大小 (KB)"),
    output_folder: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件夹"),
):
    """批量压缩图片"""
    check_pil()
    
    valid_files = [f for f in input_files if f.exists()]
    if not valid_files:
        console.print("[red]错误：没有有效的输入文件[/red]")
        raise typer.Exit(1)
    
    output_folder = output_folder or valid_files[0].parent / "compressed"
    output_folder.mkdir(exist_ok=True)
    
    console.print(f"[blue]准备压缩 {len(valid_files)} 个图片...[/blue]")
    
    success_count = 0
    total_original_size = 0
    total_compressed_size = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("压缩中...", total=len(valid_files))
        
        for img_file in valid_files:
            progress.update(task, description=f"处理: {img_file.name}")
            
            try:
                original_size = img_file.stat().st_size
                total_original_size += original_size
                
                with Image.open(img_file) as img:
                    output_file = output_folder / img_file.name
                    
                    # 根据格式选择压缩方式
                    if img_file.suffix.lower() in ['.jpg', '.jpeg']:
                        if img.mode in ('RGBA', 'P'):
                            img = img.convert('RGB')
                        img.save(output_file, 'JPEG', quality=quality, optimize=True)
                    elif img_file.suffix.lower() == '.png':
                        img.save(output_file, 'PNG', optimize=True)
                    elif img_file.suffix.lower() == '.webp':
                        img.save(output_file, 'WEBP', quality=quality)
                    else:
                        img.save(output_file)
                    
                    compressed_size = output_file.stat().st_size
                    total_compressed_size += compressed_size
                    success_count += 1
                    
            except Exception as e:
                console.print(f"[red]处理 {img_file.name} 失败: {e}[/red]")
            
            progress.advance(task)
    
    # 显示压缩结果
    if total_original_size > 0:
        savings = total_original_size - total_compressed_size
        savings_percent = (savings / total_original_size) * 100
        
        table = Table(title="压缩结果")
        table.add_column("项目", style="cyan")
        table.add_column("数值", style="magenta")
        
        table.add_row("成功压缩", str(success_count))
        table.add_row("原始大小", f"{total_original_size / 1024:.2f} KB")
        table.add_row("压缩后大小", f"{total_compressed_size / 1024:.2f} KB")
        table.add_row("节省空间", f"{savings / 1024:.2f} KB ({savings_percent:.1f}%)")
        
        console.print(table)
    
    console.print(f"\n[green]✅ 压缩完成！[/green]")
    console.print(f"输出文件夹: {output_folder}")


@app.command()
def rename(
    input_files: List[Path] = typer.Argument(..., help="输入图片文件"),
    pattern: str = typer.Option("image_{index:03d}", "--pattern", "-p", help="重命名模式，{index} 会被替换为序号"),
    start_index: int = typer.Option(1, "--start", "-s", help="起始序号"),
    dry_run: bool = typer.Option(False, "--dry-run", help="预览模式，不实际重命名"),
):
    """批量重命名图片"""
    check_pil()
    
    valid_files = sorted([f for f in input_files if f.exists()])
    if not valid_files:
        console.print("[red]错误：没有有效的输入文件[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]准备重命名 {len(valid_files)} 个文件...[/blue]")
    console.print(f"[blue]模式: {pattern}[/blue]")
    
    if dry_run:
        console.print("\n[yellow]【预览模式】以下操作不会实际执行：[/yellow]\n")
    
    table = Table(title="重命名预览" if dry_run else "重命名结果")
    table.add_column("原文件名", style="cyan")
    table.add_column("新文件名", style="green")
    
    renamed_count = 0
    
    for i, img_file in enumerate(valid_files, start=start_index):
        new_name = pattern.format(index=i) + img_file.suffix
        new_path = img_file.parent / new_name
        
        table.add_row(img_file.name, new_name)
        
        if not dry_run:
            try:
                img_file.rename(new_path)
                renamed_count += 1
            except Exception as e:
                console.print(f"[red]重命名 {img_file.name} 失败: {e}[/red]")
    
    console.print(table)
    
    if dry_run:
        console.print("\n[yellow]这是预览模式，实际重命名请去掉 --dry-run 参数[/yellow]")
    else:
        console.print(f"\n[green]✅ 成功重命名 {renamed_count} 个文件[/green]")


@app.command()
def info(
    input_files: List[Path] = typer.Argument(..., help="输入图片文件"),
):
    """查看图片详细信息"""
    check_pil()
    
    valid_files = [f for f in input_files if f.exists()]
    if not valid_files:
        console.print("[red]错误：没有有效的输入文件[/red]")
        raise typer.Exit(1)
    
    table = Table(title="图片信息")
    table.add_column("文件名", style="cyan", no_wrap=True)
    table.add_column("格式", style="magenta")
    table.add_column("尺寸", style="green")
    table.add_column("模式", style="yellow")
    table.add_column("大小", style="blue")
    
    for img_file in valid_files:
        img_info = get_image_info(img_file)
        
        if 'error' in img_info:
            table.add_row(img_file.name, "错误", "-", "-", img_info['error'])
        else:
            dimensions = f"{img_info['width']}x{img_info['height']}"
            size_str = f"{img_info['size'] / 1024:.2f} KB"
            table.add_row(
                img_file.name,
                img_info['format'] or 'Unknown',
                dimensions,
                img_info['mode'],
                size_str
            )
    
    console.print(table)


@app.command()
def watermark(
    input_files: List[Path] = typer.Argument(..., help="输入图片文件"),
    text: str = typer.Option(..., "--text", "-t", help="水印文字"),
    position: str = typer.Option("bottom-right", "--position", "-p", help="位置: top-left, top-right, bottom-left, bottom-right, center"),
    opacity: int = typer.Option(128, "--opacity", "-o", help="透明度 (0-255)"),
    size: int = typer.Option(36, "--size", "-s", help="字体大小"),
    output_folder: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件夹"),
):
    """批量添加文字水印"""
    check_pil()
    
    valid_files = [f for f in input_files if f.exists()]
    if not valid_files:
        console.print("[red]错误：没有有效的输入文件[/red]")
        raise typer.Exit(1)
    
    output_folder = output_folder or valid_files[0].parent / "watermarked"
    output_folder.mkdir(exist_ok=True)
    
    console.print(f"[blue]准备为 {len(valid_files)} 个图片添加水印...[/blue]")
    
    success_count = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("添加水印...", total=len(valid_files))
        
        for img_file in valid_files:
            progress.update(task, description=f"处理: {img_file.name}")
            
            try:
                with Image.open(img_file).convert("RGBA") as img:
                    # 创建透明层
                    watermark_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
                    draw = ImageDraw.Draw(watermark_layer)
                    
                    # 使用默认字体
                    try:
                        font = ImageFont.truetype("arial.ttf", size)
                    except:
                        font = ImageFont.load_default()
                    
                    # 计算文字位置
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    padding = 20
                    positions = {
                        "top-left": (padding, padding),
                        "top-right": (img.width - text_width - padding, padding),
                        "bottom-left": (padding, img.height - text_height - padding),
                        "bottom-right": (img.width - text_width - padding, img.height - text_height - padding),
                        "center": ((img.width - text_width) // 2, (img.height - text_height) // 2),
                    }
                    
                    pos = positions.get(position, positions["bottom-right"])
                    
                    # 绘制文字
                    draw.text(pos, text, font=font, fill=(255, 255, 255, opacity))
                    
                    # 合并图层
                    result = Image.alpha_composite(img, watermark_layer)
                    
                    # 保存
                    output_file = output_folder / img_file.name
                    if output_file.suffix.lower() == '.jpg' or output_file.suffix.lower() == '.jpeg':
                        result = result.convert("RGB")
                        result.save(output_file, "JPEG", quality=90)
                    else:
                        result.save(output_file)
                    
                    success_count += 1
                    
            except Exception as e:
                console.print(f"[red]处理 {img_file.name} 失败: {e}[/red]")
            
            progress.advance(task)
    
    console.print(f"\n[green]✅ 完成！成功添加水印 {success_count} 个图片[/green]")
    console.print(f"输出文件夹: {output_folder}")


if __name__ == "__main__":
    app()
