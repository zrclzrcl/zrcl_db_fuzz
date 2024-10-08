import sys
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from Sqlparser.MySqlLexer import MySqlLexer
from Sqlparser.MySqlParser import MySqlParser
import os
import glob
import re

class CustomErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, charPositionInLine, msg, e):
        print(f"Syntax error at line {line}:{charPositionInLine} - {msg}")

def read_file_by_id(path, filename_prefix, current):
    # 构建文件名，假设文件名格式为 id_000000后接其他字符
    filename = f"{filename_prefix}{current:06d}*"  # 使用通配符匹配后缀
    file_path = os.path.join(path, filename)

    # 使用 glob 获取匹配的文件
    matched_files = glob.glob(file_path)

    # 如果找到匹配的文件，直接读取第一个文件
    if matched_files:
        with open(matched_files[0], 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    else:
        print(f"没有找到匹配的文件以 {filename_prefix}{current:06d} 开头。")
        return None

#检查是否显式给出数据类型
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




def main(argv):
    #文件路径
    testcase_file_path = "I:\\Richard Zhang - zrcl\\BigLoong 备份\\2024-9-26\\Master\\DBMS_FUZZ\\实验数据\\变异生成文件保存\\docker_data_0_5"
    out_parser_file_path = "F:\\Master\\DBMS_FUZZ\\after_parser"

    #文件名开头：
    file_name_prefix = 'id_'
    current = 0 #当前的文件id
    count = 0
    for current in range(0, 100):
        file_content = read_file_by_id(testcase_file_path, file_name_prefix, current)#读文件
        sql_in_testcase = [sql + ';' for sql in file_content.split(';') if sql!='' and sql != ' ']  #分割为sql

        for sql in sql_in_testcase:
            #先添加数据类型
            sql_add_blob = process_create_table(sql)
            input_stream = InputStream(sql_add_blob)
            lexer = MySqlLexer(input_stream)
            token_stream = CommonTokenStream(lexer)
            parser = MySqlParser(token_stream)

            parser.removeErrorListeners()  # 移除默认错误监听器
            parser.addErrorListener(CustomErrorListener())  # 添加自定义错误监听器

            try:
                tree = parser.sqlStatement()  # 解析
                if tree is not None:  # 只有在解析成功时才打印
                    print(tree.toStringTree(parser.ruleNames))  # 正确调用
                    count += 1
            except Exception as e:
                print(f"Parsing failed: {str(e)}")

            file_path = os.path.join(out_parser_file_path, f'{current}'+'.txt')
            with open(file_path, 'a', encoding='utf-8') as file:
                file.write('---'+tree.toStringTree(parser.ruleNames))
    print(count)
if __name__ == '__main__':
    main(sys.argv)

##失败率 155/473=32.8%
##失败率 63/473=13%

# def add_blob_to_missing_types(sql):
#     # 找到 CREATE TABLE 语句的位置
#     create_index = sql.lower().find('create table')
#     if create_index == -1:
#         return sql  # 如果没有找到 CREATE TABLE，返回原始 SQL
#
#     # 提取表定义部分
#     table_definition_start = sql.find('(', create_index)
#     table_definition_end = sql.rfind(')')
#
#     if table_definition_start == -1 or table_definition_end == -1:
#         return sql  # 如果没有找到括号，返回原始 SQL
#
#     table_definition = sql[table_definition_start + 1:table_definition_end].strip()
#
#     # 分割字段定义
#     fields = [field.strip() for field in table_definition.split(',')]
#
#     # 检查字段并添加 BLOB 类型
#     modified_fields = []
#     for field in fields:
#         # 检查字段是否有类型
#         if not any(field.startswith(type) for type in ['INTEGER', 'VARCHAR', 'FLOAT', 'DATE']):
#             field += ' BLOB'
#         modified_fields.append(field)
#
#     # 重新组合字段定义
#     new_table_definition = ', '.join(modified_fields)
#
#     # 构造新的 SQL 语句
#     modified_sql = f"{sql[:table_definition_start + 1]} {new_table_definition} {sql[table_definition_end:]}"
#
#     return modified_sql
#
#
# # 示例 SQL 语句
# sql_statement = """
# CREATE TABLE v191110750 (
#     v191110752 ,
#     v191110751 INTEGER AS( '199419' ) CHECK( 10 )
#     CHECK( v191110752 NOT LIKE 'LG CASEaaaaaaaaaaaa' ) NOT NULL UNIQUE
# ) ;
# """
#
# # 添加 BLOB 类型
# modified_sql = add_blob_to_missing_types(sql_statement)
#
# print(modified_sql)
#


