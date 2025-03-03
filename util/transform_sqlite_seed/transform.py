import os
import re
import sys

def extract_brace_block(s, start):
    """从字符串 s 的 start 位置（必须为 '{'）开始，提取平衡的大括号内容，
    返回 (内容, 结束位置索引)。"""
    if s[start] != '{':
        return None, start
    depth = 0
    i = start
    while i < len(s):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return s[start+1:i], i
        i += 1
    return None, i

def extract_sql_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    sql_statements = []

    # 1. 提取 db eval 块中的 SQL
    pattern_db = r'db\s+eval\s+\{'
    for m in re.finditer(pattern_db, content, flags=re.DOTALL):
        start_index = m.end() - 1  # '{' 的位置
        block, end_index = extract_brace_block(content, start_index)
        if block is not None:
            sql_statements.append(block.strip())

    # 2. 如果有 do_execsql_test 块，也提取其中的 SQL（判断首词是否为SQL关键字）
    pattern_exec = r'do_execsql_test\s+\S+\s+\{'
    sql_keywords = {"CREATE", "INSERT", "SELECT", "PRAGMA", "DELETE", "UPDATE", "BEGIN", "ROLLBACK", "COMMIT", "ALTER", "DROP"}
    for m in re.finditer(pattern_exec, content, flags=re.DOTALL):
        start_index = m.end() - 1
        block, end_index = extract_brace_block(content, start_index)
        if block is not None:
            stripped = block.strip()
            # 仅当块首个单词为 SQL 关键字时才保留
            words = stripped.split()
            if words and words[0].upper() in sql_keywords:
                sql_statements.append(stripped)
    return sql_statements

def main(source_dir, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    file_counter = 1
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.test'):
                full_path = os.path.join(root, file)
                sqls = extract_sql_from_file(full_path)
                # 用空行分隔各个 SQL 块
                output_text = "\n\n".join(sqls)
                output_filename = os.path.join(target_dir, f"{file_counter}.txt")
                with open(output_filename, 'w', encoding='utf-8') as out_f:
                    out_f.write(output_text)
                print(f"已处理文件: {full_path} -> {output_filename}")
                file_counter += 1

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("用法: python script.py <源目录> <目标目录>")
        sys.exit(1)
    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    main(source_dir, target_dir)
