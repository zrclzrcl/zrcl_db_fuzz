import os
import re

def extract_sql_statements(file_content):
    """
    从文件内容中提取 SQL 语句。
    """
    sql_lines = []
    in_sql_block = False

    for line in file_content.splitlines():
        stripped_line = line.strip()
        # 跳过注释行和空行
        if stripped_line.startswith('#') or not stripped_line:
            continue
        # 检测到 SQL 语句的起始
        if stripped_line.lower().startswith(('select', 'insert', 'update', 'delete', 'create', 'drop', 'alter', 'truncate', 'replace', 'with')):
            in_sql_block = True
        if in_sql_block:
            sql_lines.append(line)
            # 检测到 SQL 语句的结束
            if stripped_line.endswith(';'):
                in_sql_block = False

    return '\n'.join(sql_lines)

def process_files(input_dir, output_dir):
    """
    处理指定目录下的 .test 和 .inc 文件，提取 SQL 语句并保存为 .txt 文件。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_counter = 1

    for root, _, files in os.walk(input_dir):
        for file_name in files:
            if file_name.endswith('.test') or file_name.endswith('.inc'):
                input_file_path = os.path.join(root, file_name)
                with open(input_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    sql_statements = extract_sql_statements(content)
                    if sql_statements:
                        output_file_path = os.path.join(output_dir, f"{file_counter}.txt")
                        with open(output_file_path, 'w', encoding='utf-8') as output_file:
                            output_file.write(sql_statements)
                        print(f"提取并保存 SQL 语句到: {output_file_path}")
                        file_counter += 1

if __name__ == "__main__":
    input_directory = r'C:\Users\zrcl_Richard\Downloads\mysql-server'  # 替换为实际的输入目录路径
    output_directory = r'F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\transform_mysql_seed\mysql_dseed'  # 替换为实际的输出目录路径
    process_files(input_directory, output_directory)
