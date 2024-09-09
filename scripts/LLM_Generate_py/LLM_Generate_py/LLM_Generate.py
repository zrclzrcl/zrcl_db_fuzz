from openai import OpenAI
from pathlib import Path
import re
import time

#api key
zrcl_api_key = 'sk-zk2fb6b73ba7e18c5fe5bc7bda039e14259665fcbf809ae8'
zrcl_base_url = "https://api.zhizengzeng.com/v1/"

#大语言模型生成文件名
LLM_Generate_filename = "test_case.txt"

LLM_Generate_path = "../LLM_Generate_testcase/"
LLM_Generate_split_path = "/home/LLM_testcase/"

#LLM测试用例总生成路径
LLM_Generate_path_use = Path(LLM_Generate_path)
LLM_Generate_split_path_use = Path(LLM_Generate_split_path)

#定义的调用请求gpt API的方法
def link_llm(prompt, model="gpt-3.5-turbo"):
    client = OpenAI(api_key=zrcl_api_key, base_url=zrcl_base_url)
    llm_response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ]
    )
    return llm_response.choices[0].message.content


user_input = "I want to perform fuzzy testing of SQLITE and need to generate test cases for SQLITE. Please forget all database application background and generate complex and out-of-the-way sqlite database test cases from the point of view of a fuzzy testing expert, generate test cases that are complex and try to trigger database crashes as much as possible. Each test case consists of several SQLs. I will give you some examples of test cases below: \
```sql \
CREATE TABLE v0 ( v5 VARCHAR(20) CHECK( v1 >= v1 NOT LIKE '12345' ) , v3 TEXT , v4 TEXT , v2 INTEGER , v1 FLOAT ) ;\
CREATE TEMP TRIGGER x AFTER INSERT ON v0 BEGIN DELETE FROM v0 WHERE ( SELECT COUNT ( * ) FROM v0 UNION SELECT DISTINCT v1 + 1 ) ;\
 END ; \
CREATE TRIGGER x INSERT ON v0 BEGIN INSERT INTO v0 ( v1 ) VALUES ( 9223372036854775808.000000 ) , ( 10 ) , ( 1 ) ; END ; INSERT INTO v0 ( v3 , v4 , v2 ) VALUES ( 1 , 8 , 2 ) , ( 10 , 8 , 1 ) ; INSERT INTO v0 ( v1 ) VALUES ( 2 ) ,( 2 ) ,( 1 ) ; \
``` \
```sql \
CREATE TABLE v0 ( v1 ) ; CREATE TABLE v2 ( v13 VARCHAR(255) , v14 TEXT , v15 TEXT , v3 INTEGER , v4 FLOAT , v5 INTEGER , v6 FLOAT , v7 INTEGER , v16 INTEGER , v17 TEXT . v8 TEXT , v9 TEXT , v10 TEXT , v11 INTEGER , v12 INTEGER ) ; CREATE TRIGGER r1 AFTER INSERT ON v2 BEGIN INSERT INTO v2 ( v5 ) VALUES ( 10 ) ; END ; CREATE TRIGGER x INSERT ON v2 BEGIN DELETE FROM v2 WHERE ( SELECT ( 1. 100000 ) FROM v0 , v2 JOIN v0 ) BETWEEN v14 AND 1 ; END ; ALTER TABLE v2 ADD COLUMN x FLOAT CHECK( ( 1 AND v7 ( x ( ) ) ) ) CHECK( NULL ) ; ALTER TABLE v2 ADD COLUMN x FLOAT CHECK( )\
```\
```sql \
CREATE TABLE v0 ( v10 DOUBLE PRIMARY KEY , v1 DOUBLE UNIQUE , v2 INTEGER , v3 FLOAT UNIQUE , v5 UNIQUE UNIQUE , v4 UNIQUE , v6 INTEGER UNIQUE CHECK( v7 ) , v7 FLOAT , v8 INTEGER , v9 INT UNIQUE ) ; CREATE TEMP TRIGGER x AFTER INSERT ON v0 BEGIN REPLACE INTO v0 ( v4 , v4 , v4 ) VALUES ( 1 , 3 , 10 ) ; END ; CREATE INDEX v11 ON v0 ( v6 ) WHERE 1.100000 + v1 > v2 + v10 + 1.100000 IS NOT NULL AND ( v6 = v2 AND v5 + v10 > v4 NOT LIKE v5 + 10 > v1 ) IS NOT NULL ; REPLACE INTO v0 ( v7 , v7 , v10 ) VALUES ( 1 , 10 , 1 ) ; REPLACE INTO v0 ( v7 ) VALUES ( NULL ) ; \
```\
You can refer to the test cases I gave and generate more test cases “randomly”. It is not only important to refer to the test cases I have given, but it is also important to think about the process of generating them according to the procedure I have given below.\
First of all, you need to make sure that the SQL syntax is correct when generating the test cases.\
Second, whether the generated test cases have sufficient statement diversity, there are no more statement types in the test cases, such as: MATCH, SELECT, INSERT, UPDATE, DELETE, CREATE DATABASE, CREATE TABLE, CREATE TEMPORARY TABLE, CREATE INDEX, CREATE VIEW, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TRIGGER, GRANT, REVOKE, BEGIN, COMMIT, ROLLBACK, MERGE, TRUNCATE. ANALYZE, EXPLAIN, SHOW, DESCRIBE and so on.\
Third, it is very important that the generated test cases test the functionality that the target database has and other databases do not. If not, it needs to be added to the test cases.\
Fourth, is the generated SQL complex enough to have a nested structure greater than 3 levels.\
Fifth, check whether the SQL is semantically correct, and whether there is corresponding data in it to be manipulated, and if not, then create the insert data statement first to ensure that the statement can be successfully executed.\
Note that the generated statements must be very complex. Include multiple nesting with the use of functions, you can also create functions for testing!\
Based on the above description, you can start generating 3 test cases and start them with\
```sql\
```\
Separate the generated test cases. "

#创建LLM生成测试用例的保存文件夹
if not LLM_Generate_path_use.exists():
    LLM_Generate_path_use.mkdir(parents=True)


#创建LLM生成测试用例分割后的保存文件夹
if not LLM_Generate_split_path_use.exists():
    LLM_Generate_split_path_use.mkdir(parents=True)


counter = 1
round = 0
#发起请求：获取响应
while True:
    round += 1
    # 发起请求：获取响应
    response = link_llm(user_input)

    # 将完整的测试用例保存到单个文件
    full_file_path = LLM_Generate_path_use / LLM_Generate_filename
    with open(full_file_path, "w", encoding="utf-8") as full_file:
        full_file.write(response)

    # 读取文件内容
    with open(full_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 使用正则表达式匹配 ```sql 和 ``` 之间的内容
    sql_cases = re.findall(r'```sql(.*?)```', content, re.DOTALL)

    # 分别将每个测试用例保存到独立的 txt 文件
    for i, sql_case in enumerate(sql_cases, 1):
        with open(f'{LLM_Generate_split_path}LLM_G_{counter}.txt', 'w', encoding='utf-8') as output_file:
            output_file.write(sql_case.strip())  # 去除多余的空白字符
        counter += 1

    # 每隔1分钟执行一次
    # time.sleep()
