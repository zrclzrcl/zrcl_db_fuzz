import os
import sqlparse


def count_sql_statements_in_file(file_path):
    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            statements = sqlparse.split(content)
            count = len(statements)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return count

def analyze_directory(path):
    total_files = 0
    total_size = 0
    total_sql_statements = 0

    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            total_files += 1
            total_size += os.path.getsize(file_path)
            total_sql_statements += count_sql_statements_in_file(file_path)

    return total_files, total_size, total_sql_statements


if __name__ == "__main__":
    path = input("请输入要分析的路径: ")
    if not os.path.exists(path):
        print("路径不存在!")
    else:
        files_count, total_size, sql_count = analyze_directory(path)
        print(f"文件总数: {files_count}")
        print(f"文件总大小: {total_size} 字节")
        print(f"SQL 语句总数: {sql_count}")