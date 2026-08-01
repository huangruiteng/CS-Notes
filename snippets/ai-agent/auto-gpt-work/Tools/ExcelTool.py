import pandas as pd


def get_sheet_names(
        filename: str
) -> str:
    """获取 Excel 文件的工作表名称"""
    excel_file = pd.ExcelFile(filename)
    sheet_names = excel_file.sheet_names
    return f"这是 '{filename}' 文件的工作表名称：\n\n{sheet_names}"


def get_column_names(
        filename: str
) -> str:
    """获取 Excel 文件的列名"""

    # 读取 Excel 文件的第一个工作表
    df = pd.read_excel(filename, sheet_name=0)  # sheet_name=0 表示第一个工作表

    column_names = '\n'.join(
        df.columns.to_list()
    )

    result = f"这是 '{filename}' 文件第一个工作表的列名：\n\n{column_names}"
    return result


def get_first_n_rows(
        filename: str,
        n: int = 3
) -> str:
    """获取 Excel 文件的前 n 行"""

    result = get_sheet_names(filename) + "\n\n"

    result += get_column_names(filename) + "\n\n"

    # 读取 Excel 文件的第一个工作表
    df = pd.read_excel(filename, sheet_name=0)  # sheet_name=0 表示第一个工作表

    n_lines = '\n'.join(
        df.head(n).to_string(index=False, header=True).split('\n')
    )

    result += f"这是 '{filename}' 文件第一个工作表的前{n}行样例：\n\n{n_lines}"
    return result
