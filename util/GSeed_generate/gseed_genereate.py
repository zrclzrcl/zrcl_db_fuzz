#生成指定数据库的gseed
import os
import random
import re
import time


import chardet
from ollama import chat

#   首先获取想要转换哪个数据库
#   获取生成多少个gseed
#   然后构建prompt
#   联系LLM生成
#   保存生成的测试用例

def chat_llm(prompt):
    response = chat(
        model='deepseek-r1:32b',
        messages=[
            {
                'role': 'user',
                'content': prompt
            }],
        options=
        {
            'temperature': 0.6
        },
    )
    return response.message.content

def main():
    target_db = input("请输入gseed的目标数据库，sqlite/mysql/mariadb/postgresql/duckdb")
    generate_num = int(input("请输入生成gseed的个数，0表示默认个数"))
    output_path = rf"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\GSeed_generate\output_{target_db}"
    if generate_num == 0:
        if target_db == "mariadb":
            generate_num = 9
        elif target_db == "postgresql":
            generate_num = 16
        elif target_db == "duckdb":
            generate_num = 30
        elif target_db == "mysql":
            generate_num = 9
        elif target_db == "sqlite":
            generate_num = 30
        else:
            raise Exception("输入的目标数据库不被支持")

    #构建PROMPT
    prompt = rf"""
    *背景* 你需要为数据库模糊测试生成优秀的初始种子，你需要从以下几个部分生成优秀的初始种子。
    1. 一个初始种子包含多个SQL语句，并只包含SQL语句
    2. 一个优秀的初始种子需要具有如下的几个特性：是否能测试到边缘条件|是否有可能测试到更多功能|是否有可能达到更高的程序覆盖率|是否有可能触发数据库漏洞与bug|作为初始种子是否有更加复杂的结构易于后续的模糊测试种子变异\
    4. 初始种子还要尽可能包含目标数据库所特有而其他数据库没有的特色功能的SQL语句，以尝试覆盖更多的路径。
    3. 你需要确保生成的初始种子具有正确的目标数据库的语法与语义。不满足目标数据库语法的需要改正，语义不正确的需要修改语句（例如缺少表则建表，缺少字段就创建字段）\
    
    *目标* 你现在需要为{target_db}生成1个高质量且优秀的初始种子，你的测试用例中不能涉及到创建与切换数据库的语句。
    *输出格式* 使用 '\n```sql\n (你生成的初始种子) \n```\n' 来包裹你生成的初始种子。
    """

    flag = 1
    while flag <= generate_num:
        start_time = time.time()
        print(f"当前正在生成第{flag}个")
        response = chat_llm(prompt)
        #保存结果
        if not os.path.exists(os.path.dirname(f"{output_path}\\")):
            os.makedirs(os.path.dirname(f"{output_path}\\"))

        pattern = r'```sql\s+(.*?)\s+```'
        matches = re.findall(pattern, response, re.DOTALL)
        with open(rf'{output_path}\LLM_{flag}.txt', 'w', encoding='utf-8') as file:
            file.write(matches[0])
        end_time = time.time()
        print(f"第{flag}个生成结束，用时：{end_time - start_time:.2f}s")
        flag += 1


if __name__ == '__main__':
    main()