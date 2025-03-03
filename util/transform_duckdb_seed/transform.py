import os
import re

def extract_sql_blocks_from_file(file_path):
    """
    从一个 .test 文件中提取 SQL 命令块：
    - 文件中以“statement”或“query”开头的行标识后面的 SQL 命令
    - 控制行（例如注释行、require行、标识输出的“----”行）均会被跳过
    - 当遇到空行或输出标记时，认为当前 SQL 块结束
    """
    sql_blocks = []
    current_block = []
    state = "search"  # 两种状态："search"（查找控制标识），"collect"（收集 SQL 命令）

    # 控制标识正则：匹配以 "statement" 或 "query" 开头（忽略大小写）
    start_marker = re.compile(r'^(statement|query)\b', re.IGNORECASE)
    # 输出标识：通常以 "----" 开头
    output_marker = re.compile(r'^----')

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()
            # 跳过空行
            if not stripped:
                if state == "collect" and current_block:
                    sql_blocks.append("\n".join(current_block))
                    current_block = []
                    state = "search"
                continue
            # 跳过注释和 require 开头的行（不区分大小写）
            if stripped.startswith("#") or stripped.lower().startswith("require"):
                continue

            if state == "search":
                # 如果遇到控制标识，则后续的非空行就属于 SQL 语句
                if start_marker.match(stripped):
                    state = "collect"
                # 否则继续搜索
            elif state == "collect":
                # 如果遇到输出分隔符，则认为当前 SQL 块结束
                if output_marker.match(stripped):
                    if current_block:
                        sql_blocks.append("\n".join(current_block))
                        current_block = []
                    state = "search"
                    continue
                # 如果又遇到控制标识，则也认为前一个块结束，且不把这行作为 SQL（它本身只是标识）
                if start_marker.match(stripped):
                    if current_block:
                        sql_blocks.append("\n".join(current_block))
                        current_block = []
                    # 保持 state 为 "collect" 或重置为 "search"（这里我们直接跳过控制标识行）
                    continue
                # 否则，将该行作为 SQL 命令的一部分
                current_block.append(stripped)
        # 文件结束后，若还有未结束的块，则追加
        if state == "collect" and current_block:
            sql_blocks.append("\n".join(current_block))
    return sql_blocks

def extract_sql_from_directory(directory):
    """
    递归遍历目录下所有 .test 文件，返回一个列表，
    每个元素为 (文件路径, [SQL块, SQL块, ...])
    """
    results = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.test'):
                full_path = os.path.join(root, filename)
                blocks = extract_sql_blocks_from_file(full_path)
                if blocks:
                    results.append((full_path, blocks))
    return results

def write_sql_to_txt_files(sql_extracted, output_dir):
    """
    将提取结果写入单独的 txt 文件中，每个文件保存一个 .test 文件中的所有 SQL 块，
    文件命名为 1.txt, 2.txt, ... 依次递增。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    counter = 1
    for file_path, blocks in sql_extracted:
        combined_sql = "\n\n".join(blocks)
        output_file = os.path.join(output_dir, f"{counter}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(combined_sql)
        counter += 1

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="从 DuckDB 的 .test 文件中提取 SQL 命令，并生成编号递增的 txt 文件")
    parser.add_argument("input_dir", help="包含 .test 文件的目录")
    parser.add_argument("output_dir", help="生成的 txt 文件存放目录")
    args = parser.parse_args()

    extracted = extract_sql_from_directory(args.input_dir)
    write_sql_to_txt_files(extracted, args.output_dir)
    print("提取完成！")
