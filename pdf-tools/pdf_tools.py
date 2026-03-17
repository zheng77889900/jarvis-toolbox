"""
PDF 智能工具箱
功能：PDF合并、拆分、压缩、转换、加密、解密
作者：贾维斯
版本：1.0.0
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="PDF 智能工具箱 - 让 PDF 处理更简单")
console = Console()

# 尝试导入 PyPDF2，如果失败则提示安装
try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    console.print("[yellow]警告：PyPDF2 未安装，部分功能不可用[/yellow]")
    console.print("[blue]请运行：pip install PyPDF2[/blue]")


def check_pypdf2():
    """检查 PyPDF2 是否可用"""
    if not PYPDF2_AVAILABLE:
        console.print("[red]错误：PyPDF2 库未安装[/red]")
        console.print("[yellow]请运行：pip install PyPDF2[/yellow]")
        raise typer.Exit(1)


def get_pdf_files(folder: Path, recursive: bool = False) -> List[Path]:
    """获取文件夹中的所有 PDF 文件"""
    if recursive:
        return sorted(folder.rglob("*.pdf"))
    else:
        return sorted(folder.glob("*.pdf"))


@app.command()
def merge(
    input_files: List[Path] = typer.Argument(..., help="输入 PDF 文件（可多个）"),
    output_file: Path = typer.Option(..., "--output", "-o", help="输出文件路径"),
    bookmark: bool = typer.Option(True, "--bookmark/--no-bookmark", help="为每个文件添加书签"),
):
    """合并多个 PDF 文件"""
    check_pypdf2()
    
    # 验证输入文件
    valid_files = []
    for f in input_files:
        if f.exists() and f.suffix.lower() == '.pdf':
            valid_files.append(f)
        else:
            console.print(f"[yellow]跳过无效文件: {f}[/yellow]")
    
    if not valid_files:
        console.print("[red]错误：没有有效的 PDF 文件[/red]")
        raise typer.Exit(1)
    
    console.print(f"[blue]准备合并 {len(valid_files)} 个 PDF 文件...[/blue]")
    
    merger = PdfWriter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("合并中...", total=len(valid_files))
        
        for i, pdf_file in enumerate(valid_files):
            progress.update(task, description=f"添加: {pdf_file.name}")
            
            try:
                reader = PdfReader(str(pdf_file))
                merger.append(reader)
                
                if bookmark:
                    # 添加书签（以文件名作为书签）
                    merger.add_outline_item(pdf_file.stem, i)
                    
            except Exception as e:
                console.print(f"[red]处理 {pdf_file.name} 失败: {e}[/red]")
            
            progress.advance(task)
    
    # 保存合并后的文件
    try:
        with open(output_file, 'wb') as output:
            merger.write(output)
        
        # 显示结果
        table = Table(title="合并结果")
        table.add_column("项目", style="cyan")
        table.add_column("数值", style="magenta")
        
        table.add_row("输入文件数", str(len(valid_files)))
        table.add_row("输出文件", str(output_file))
        table.add_row("输出大小", f"{output_file.stat().st_size / 1024:.2f} KB")
        
        console.print(table)
        console.print(f"\n[green]✅ 合并完成！[/green]")
        
    except Exception as e:
        console.print(f"[red]保存文件失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def split(
    input_file: Path = typer.Argument(..., help="输入 PDF 文件"),
    output_folder: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件夹"),
    pages: Optional[str] = typer.Option(None, "--pages", "-p", help="指定页码范围（如：1-5,8,10-12）"),
):
    """拆分 PDF 文件"""
    check_pypdf2()
    
    if not input_file.exists():
        console.print(f"[red]错误：文件不存在 {input_file}[/red]")
        raise typer.Exit(1)
    
    output_folder = output_folder or input_file.parent / f"{input_file.stem}_split"
    output_folder.mkdir(exist_ok=True)
    
    try:
        reader = PdfReader(str(input_file))
        total_pages = len(reader.pages)
        
        console.print(f"[blue]PDF 总页数: {total_pages}[/blue]")
        
        # 解析页码范围
        if pages:
            page_numbers = parse_page_range(pages, total_pages)
        else:
            page_numbers = list(range(total_pages))
        
        console.print(f"[blue]将拆分出 {len(page_numbers)} 页[/blue]")
        
        # 逐页保存
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("拆分中...", total=len(page_numbers))
            
            for i, page_num in enumerate(page_numbers):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num])
                
                output_file = output_folder / f"page_{page_num + 1:03d}.pdf"
                with open(output_file, 'wb') as f:
                    writer.write(f)
                
                progress.advance(task)
        
        console.print(f"\n[green]✅ 拆分完成！[/green]")
        console.print(f"输出文件夹: {output_folder}")
        console.print(f"生成文件数: {len(page_numbers)}")
        
    except Exception as e:
        console.print(f"[red]处理失败: {e}[/red]")
        raise typer.Exit(1)


def parse_page_range(pages_str: str, total_pages: int) -> List[int]:
    """解析页码范围字符串"""
    result = []
    parts = pages_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            start = int(start) - 1  # 转换为0-based
            end = int(end)
            result.extend(range(max(0, start), min(end, total_pages)))
        else:
            page = int(part) - 1  # 转换为0-based
            if 0 <= page < total_pages:
                result.append(page)
    
    return sorted(set(result))  # 去重并排序


@app.command()
def info(
    input_file: Path = typer.Argument(..., help="输入 PDF 文件"),
):
    """查看 PDF 文件信息"""
    check_pypdf2()
    
    if not input_file.exists():
        console.print(f"[red]错误：文件不存在 {input_file}[/red]")
        raise typer.Exit(1)
    
    try:
        reader = PdfReader(str(input_file))
        
        # 基本信息
        table = Table(title=f"PDF 文件信息: {input_file.name}")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="magenta")
        
        table.add_row("文件大小", f"{input_file.stat().st_size / 1024:.2f} KB")
        table.add_row("总页数", str(len(reader.pages)))
        table.add_row("是否加密", "是" if reader.is_encrypted else "否")
        
        # 元数据
        if reader.metadata:
            metadata = reader.metadata
            table.add_row("标题", str(metadata.get('/Title', 'N/A')))
            table.add_row("作者", str(metadata.get('/Author', 'N/A')))
            table.add_row("创建者", str(metadata.get('/Creator', 'N/A')))
            table.add_row("创建日期", str(metadata.get('/CreationDate', 'N/A')))
        
        console.print(table)
        
        # 页面尺寸信息
        if len(reader.pages) > 0:
            page = reader.pages[0]
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            
            console.print(f"\n[blue]页面尺寸:[/blue]")
            console.print(f"  宽度: {width:.2f} pt ({width * 0.3528:.2f} mm)")
            console.print(f"  高度: {height:.2f} pt ({height * 0.3528:.2f} mm)")
            
    except Exception as e:
        console.print(f"[red]读取失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def encrypt(
    input_file: Path = typer.Argument(..., help="输入 PDF 文件"),
    password: str = typer.Option(..., "--password", "-p", help="设置密码"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
):
    """加密 PDF 文件"""
    check_pypdf2()
    
    if not input_file.exists():
        console.print(f"[red]错误：文件不存在 {input_file}[/red]")
        raise typer.Exit(1)
    
    output_file = output_file or input_file.parent / f"{input_file.stem}_encrypted.pdf"
    
    try:
        reader = PdfReader(str(input_file))
        writer = PdfWriter()
        
        # 复制所有页面
        for page in reader.pages:
            writer.add_page(page)
        
        # 加密
        writer.encrypt(password)
        
        with open(output_file, 'wb') as f:
            writer.write(f)
        
        console.print(f"[green]✅ 加密完成！[/green]")
        console.print(f"输出文件: {output_file}")
        
    except Exception as e:
        console.print(f"[red]加密失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def decrypt(
    input_file: Path = typer.Argument(..., help="输入 PDF 文件"),
    password: str = typer.Option(..., "--password", "-p", help="PDF 密码"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
):
    """解密 PDF 文件"""
    check_pypdf2()
    
    if not input_file.exists():
        console.print(f"[red]错误：文件不存在 {input_file}[/red]")
        raise typer.Exit(1)
    
    output_file = output_file or input_file.parent / f"{input_file.stem}_decrypted.pdf"
    
    try:
        reader = PdfReader(str(input_file))
        
        if reader.is_encrypted:
            reader.decrypt(password)
        
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        with open(output_file, 'wb') as f:
            writer.write(f)
        
        console.print(f"[green]✅ 解密完成！[/green]")
        console.print(f"输出文件: {output_file}")
        
    except Exception as e:
        console.print(f"[red]解密失败: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
