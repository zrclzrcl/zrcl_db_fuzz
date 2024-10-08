from antlr4 import *
import re
from MySqlLexer import MySqlLexer
from MySqlParser import MySqlParser

import re


def is_create_table(sql):
    return sql.strip().upper().startswith("CREATE TABLE")


def extract_columns(sql):
    if is_create_table(sql):
        start = sql.find('(')
        end = start
        level = 0

        for i, char in enumerate(sql[start:], start):
            if char == '(':
                level += 1
            elif char == ')':
                level -= 1

            if level == 0:
                end = i
                break

        return sql[start + 1:end].strip() if level == 0 else None
    return None


def split_columns(columns_content):
    if columns_content:
        return [col.strip() for col in columns_content.split(',')]
    return []


def has_data_type(column):
    data_types = ["INTEGER", "INT", "DOUBLE", "FLOAT", "TEXT", "BLOB",
                  "VARCHAR", "CHAR", "DATE", "TIMESTAMP", "BOOLEAN",
                  "DECIMAL", "NUMERIC", "TIME"]
    return any(dtype in column.upper() for dtype in data_types)

def add_blob_if_needed(columns):
    for i, column in enumerate(columns):
        if not has_data_type(column):
            # 查找第一个空格
            space_index = column.find(' ')
            if space_index != -1:
                # 在第一个空格后插入BLOB
                columns[i] = column[:space_index + 1] + "BLOB " + column[space_index + 1:]
            else:
                # 如果没有空格，则直接在末尾添加 BLOB
                columns[i] += " BLOB"
    return columns


def reconstruct_create_table(sql, columns):
    # 找到最外层括号
    start = sql.find('(')
    end = start
    level = 0

    for i, char in enumerate(sql[start:], start):
        if char == '(':
            level += 1
        elif char == ')':
            level -= 1

        if level == 0:
            end = i
            break

    # 重新组合
    new_columns_content = ', '.join(columns)
    return sql[:start + 1] + new_columns_content + sql[end:]

def process_create_table(sql):
    if is_create_table(sql):
        columns_content = extract_columns(sql)
        columns = split_columns(columns_content)
        columns = add_blob_if_needed(columns)
        return reconstruct_create_table(sql,columns)
    return sql

# 示例
sql_statement = "SELECT v1 , ( SELECT v3 , v1 WHERE v3 < v1 ) FROM v0 ORDER BY v1 ; "
updated_columns = process_create_table(sql_statement)

print(updated_columns)
input_stream = InputStream(updated_columns)
#input_stream = InputStream(sql)
lexer = MySqlLexer(input_stream)
token_stream = CommonTokenStream(lexer)
parser = MySqlParser(token_stream)
tree = parser.sqlStatement()
print(tree.toStringTree(parser.ruleNames))
