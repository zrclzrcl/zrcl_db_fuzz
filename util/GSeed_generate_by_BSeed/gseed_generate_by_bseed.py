# 生成指定数据库的gseed
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
def get_prompt(sample,target_db):
    # 构建PROMPT
    prompt = rf"""
    *背景* You need to generate high-quality initial seeds for database fuzz testing. These seeds should be generated based on the following criteria:
    1. An initial seed consists of multiple SQL statements and should contain only SQL statements.
    2. A high-quality initial seed should exhibit the following characteristics:Whether it can test edge cases.Whether it has the potential to test more functionalities.Whether it can achieve higher program coverage.Whether it is likely to trigger database vulnerabilities and bugs.
    3. You need to ensure that the generated initial seeds conform to the syntax and semantics of the target database.If the syntax does not meet the requirements of the target database, it must be corrected.If the semantics are incorrect, the statements need to be modified (e.g., if a table is missing, create it; if a column is missing, add it).
    4. The initial seed should also include SQL statements that are unique to the target database and not commonly found in other databases to attempt to cover more execution paths.
    5. Below are sample initial seeds provided by other fuzz testing tools for reference.
    *Sample*
    ```sql
    {sample}
    ```
    *Objective* You need to generate one high-quality and well-designed initial seed for {target_db}. Your test case must not include statements for creating or switching databases.
    *Output Format* Use the following format to wrap your generated initial seed: '\n```sql\n (Your generated initial seed) \n```\n'
    """
    return prompt

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
    target_db = input("请输入gseed的目标数据库，sqlite/mysql/mariadb/postgresql/duckdb：")
    input_path = input("请输入现有种子的样本路径：")
    output_path = rf"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\GSeed_generate_by_BSeed\output_{target_db}"



    flag = 1
    for each_file in os.listdir(input_path):
        each_full_path = os.path.join(input_path, each_file)
        if os.path.isfile(each_full_path):
            while True:
                try:
                    start_time = time.time()
                    print(f"当前正在生成第{flag}个")
                    with open(each_full_path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        prompt = get_prompt(content, target_db)

                    response = chat_llm(prompt)
                    # 保存结果
                    if not os.path.exists(os.path.dirname(f"{output_path}\\")):
                        os.makedirs(os.path.dirname(f"{output_path}\\"))

                    pattern = r'```sql\s+(.*?)\s+```'
                    matches = re.findall(pattern, response, re.DOTALL)
                    print(f"================prompt===================\n{prompt}\n================================")
                    print(f"================response===================\n{response}\n================================")
                    with open(rf'{output_path}\LLM_{flag}.txt', 'w', encoding='utf-8') as file:
                        file.write(matches[0])
                    end_time = time.time()
                    print(f"第{flag}个生成结束，用时：{end_time - start_time:.2f}s")
                    flag += 1
                    break
                except Exception as e:
                    pass




if __name__ == '__main__':
    main()