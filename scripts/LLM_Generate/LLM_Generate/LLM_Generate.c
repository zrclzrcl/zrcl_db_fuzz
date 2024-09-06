#include "zrcl_Richard.h"

int main(void) {
    const char* model = "gpt-3.5-turbo";
    const char* message = "I want to perform fuzzy testing of SQLITE and need to generate test cases for SQLITE. Each test case consists of several SQLs. I will give you some examples of test cases below: \
```sql \
CREATE TABLE v0 ( v2 FLOAT , v4 FLOAT , v3 TEXT , v1 TEXT ) ; INSERT INTO v0 ( v2 ) VALUES ( 1 ) ,( 1 ) ; UPDATE v0 SET v2 = ( v3 < v1 + 2147483647 IN ( 1.100000 , 9223372036854775807 , v3 < ( SELECT v2 WHERE v1 BETWEEN 1.100000 AND v3 + NULL LIKE v4 ) ) ) ; \
```\
You can refer to the test cases I gave and generate more test cases “randomly”. It is not only important to refer to the test cases I have given, but it is also important to think about the process of generating them according to the procedure I have given below.\
First of all, you need to make sure that the SQL syntax is correct when generating the test cases.\
Second, whether the generated test cases have sufficient statement diversity, there are no more statement types in the test cases, CREATE DATABASE, CREATE TABLE, CREATE INDEX, CREATE VIEW, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TRIGGER, BEGIN, COMMIT, ROLLBACK, MERGE, TRUNCATE. ANALYZE, EXPLAIN, SHOW, DESCRIBE and so on.\
Third, it is very important that the generated test cases test the functionality that the target database has and other databases do not. If not, it needs to be added to the test cases.\
Fourth, is the generated SQL complex enough to have a nested structure greater than 3 levels.\
Fifth, check whether the SQL is semantically correct, and whether there is corresponding data in it to be manipulated, and if not, then create the insert data statement first to ensure that the statement can be successfully executed.\
Based on the above description, you can start generating 15 test cases and start them with\
```sql\
```\
Separate the generated test cases.";
    char path[1024] = "../LLM_Generate_testcase/";
    char* filename = "testcases.txt";

    //判断想要保存的路径是否存在
    create_directory_if_not_exists(path);
    //判断后组成完整的路径
    strcat(path, filename);

    char* response = link_LLM(model, message);

    if (response) {
        //若有响应 则开始解析该json
        char* content = get_response_content(response);

        //将返回信息存入文件中
        FILE* file = fopen(path, "a+");
        if (file) {
            fprintf(file, "%s\n", content);  // 将内容写入文件
            fclose(file);  // 关闭文件
            printf("response saved to output.txt\n");
        }
        else {
            fprintf(stderr, "failed to open file for writing.\n");
        }


        printf("api response: %s\n", content);
        free(content); // 释放解析出来的内容
        free(response); // 释放api响应内存
    }
    else {
        //若无响应则输出失败
        fprintf(stderr, "failed to get a response from the api.\n");
    }

    //将测试用例文件分割为更小的测试用例txt
    //split_testcases(path);

    return 0;
}
