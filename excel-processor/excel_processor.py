"""
Excel 批量处理器
功能：批量格式转换、数据清洗、报表生成
作者：贾维斯
版本：1.0.0
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(help="Excel 批量处理器 - 让表格处理自动化")
console = Console()


def get_excel_files(folder: Path, recursive: bool = False) -> List[Path]:
    """获取文件夹中的所有 Excel 文件"""
    patterns = ["*.xlsx", "*.xls", "*.xlsm"]
    files = []
    for pattern in patterns:
        if recursive:
            files.extend(folder.rglob(pattern))
        else:
            files.extend(folder.glob(pattern))
    return sorted(set(files))


@app.command()
def convert(
    input_folder: Path = typer.Argument(..., help="输入文件夹路径"),
    output_format: str = typer.Option("csv", "--format", "-f", help="输出格式: csv, json, xlsx"),
    output_folder: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件夹路径"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="递归处理子文件夹"),
):
    """批量转换 Excel 文件格式"""
    
    if not input_folder.exists():
        console.print(f"[red]错误：文件夹不存在 {input_folder}[/red]")
        raise typer.Exit(1)
    
    output_folder = output_folder or input_folder / "converted"
    output_folder.mkdir(exist_ok=True)
    
    files = get_excel_files(input_folder, recursive)
    
    if not files:
        console.print(f"[yellow]未找到 Excel 文件[/yellow]")
        raise typer.Exit(0)
    
    console.print(f"[blue]找到 {len(files)} 个 Excel 文件[/blue]")
    
    success_count = 0
    failed_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("转换中...", total=len(files))
        
        for file in files:
            progress.update(task, description=f"处理: {file.name}")
            
            try:
                # 读取所有 sheet
                xl = pd.ExcelFile(file)
                
                for sheet_name in xl.sheet_names:
                    df = pd.read_excel(file, sheet_name=sheet_name)
                    
                    # 生成输出文件名
                    base_name = file.stem
                    if len(xl.sheet_names) > 1:
                        base_name = f"{file.stem}_{sheet_name}"
                    
                    output_file = output_folder / f"{base_name}.{output_format}"
                    
                    # 根据格式保存
                    if output_format == "csv":
                        df.to_csv(output_file, index=False, encoding="utf-8-sig")
                    elif output_format == "json":
                        df.to_json(output_file, orient="records", force_ascii=False, indent=2)
                    elif output_format == "xlsx":
                        df.to_excel(output_file, index=False, sheet_name=sheet_name)
                
                success_count += 1
                
            except Exception as e:
                failed_files.append((file.name, str(e)))
            
            progress.advance(task)
    
    # 显示结果
    table = Table(title="转换结果")
    table.add_column("项目", style="cyan")
    table.add_column("数量", style="magenta")
    
    table.add_row("成功", str(success_count))
    table.add_row("失败", str(len(failed_files)))
    table.add_row("总计", str(len(files)))
    
    console.print(table)
    
    if failed_files:
        console.print("\n[red]失败的文件：[/red]")
        for name, error in failed_files:
            console.print(f"  - {name}: {error}")
    
    console.print(f"\n[green]输出文件夹: {output_folder}[/green]")


@app.command()
def merge(
    input_folder: Path = typer.Argument(..., help="输入文件夹路径"),
    output_file: Path = typer.Option(..., "--output", "-o", help="输出文件路径"),
    pattern: str = typer.Option("*.xlsx", "--pattern", "-p", help="文件匹配模式"),
    sheet_name: str = typer.Option("Sheet1", "--sheet", "-s", help="要合并的 Sheet 名称"),
):
    """合并多个 Excel 文件为一个"""
    
    if not input_folder.exists():
        console.print(f"[red]错误：文件夹不存在 {input_folder}[/red]")
        raise typer.Exit(1)
    
    files = list(input_folder.glob(pattern))
    
    if not files:
        console.print(f"[yellow]未找到匹配的文件[/yellow]")
        raise typer.Exit(0)
    
    console.print(f"[blue]找到 {len(files)} 个文件，开始合并...[/blue]")
    
    all_data = []
    failed_files = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("合并中...", total=len(files))
        
        for file in files:
            progress.update(task, description=f"读取: {file.name}")
            
            try:
                df = pd.read_excel(file, sheet_name=sheet_name)
                df["_来源文件"] = file.name  # 添加来源标记
                all_data.append(df)
            except Exception as e:
                failed_files.append((file.name, str(e)))
            
            progress.advance(task)
    
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)
        merged_df.to_excel(output_file, index=False)
        
        console.print(f"\n[green]合并完成！[/green]")
        console.print(f"  总行数: {len(merged_df)}")
        console.print(f"  总列数: {len(merged_df.columns)}")
        console.print(f"  输出文件: {output_file}")
    
    if failed_files:
        console.print(f"\n[yellow]失败的文件 ({len(failed_files)}):[/yellow]")
        for name, error in failed_files:
            console.print(f"  - {name}")


@app.command()
def clean(
    input_file: Path = typer.Argument(..., help="输入 Excel 文件"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="输出文件路径"),
    remove_empty: bool = typer.Option(True, "--remove-empty/--keep-empty", help="删除空行"),
    trim_spaces: bool = typer.Option(True, "--trim-spaces/--no-trim", help="去除首尾空格"),
    remove_duplicates: bool = typer.Option(False, "--remove-duplicates", "-d", help="删除重复行"),
):
    """清洗 Excel 数据"""
    
    if not input_file.exists():
        console.print(f"[red]错误：文件不存在 {input_file}[/red]")
        raise typer.Exit(1)
    
    output_file = output_file or input_file.parent / f"{input_file.stem}_cleaned{input_file.suffix}"
    
    console.print(f"[blue]正在清洗: {input_file.name}[/blue]")
    
    try:
        # 读取所有 sheet
        xl = pd.ExcelFile(input_file)
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(input_file, sheet_name=sheet_name)
                original_rows = len(df)
                
                # 清洗操作
                if remove_empty:
                    df = df.dropna(how='all')
                
                if trim_spaces:
                    for col in df.select_dtypes(include=['object']).columns:
                        df[col] = df[col].str.strip()
                
                if remove_duplicates:
                    df = df.drop_duplicates()
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                removed = original_rows - len(df)
                if removed > 0:
                    console.print(f"  [green]{sheet_name}: 删除了 {removed} 行[/green]")
        
        console.print(f"\n[green]清洗完成！输出: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def info(
    input_file: Path = typer.Argument(..., help="输入 Excel 文件"),
):
    """查看 Excel 文件信息"""
    
    if not input_file.exists():
        console.print(f"[red]错误：文件不存在 {input_file}[/red]")
        raise typer.Exit(1)
    
    try:
        xl = pd.ExcelFile(input_file)
        
        table = Table(title=f"文件信息: {input_file.name}")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="magenta")
        
        table.add_row("文件大小", f"{input_file.stat().st_size / 1024:.2f} KB")
        table.add_row("Sheet 数量", str(len(xl.sheet_names)))
        table.add_row("Sheet 列表", ", ".join(xl.sheet_names))
        
        console.print(table)
        
        # 每个 sheet 的详细信息
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(input_file, sheet_name=sheet_name)
            
            sheet_table = Table(title=f"Sheet: {sheet_name}")
            sheet_table.add_column("属性", style="cyan")
            sheet_table.add_column("值", style="magenta")
            
            sheet_table.add_row("行数", str(len(df)))
            sheet_table.add_row("列数", str(len(df.columns)))
            sheet_table.add_row("列名", ", ".join(df.columns.astype(str)))
            
            console.print(sheet_table)
        
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
