#define _CRT_SECURE_NO_WARNINGS 1
#include "zrcl_Richard.h"

int main(void) {
    const char* model = "gpt-4";
    const char* message = "Q: I want to test the bug of sqlite. Need to generate 15 testcases. Each testcases need Contains a complete sequence of sql statements. Remember that each test case needs to be complex enough to utilize a large number of functions and contain expansive functionality for comprehensive database testing. Also the substance of testcase are not just one SQL statement need be several statement, not a description of the test.";
    char path[1024] = "../LLM_Generate_testcase/";
    char* filename = "testcases_2.txt";
    char* response = link_LLM(model, message);

    if (response) {
        //若有响应 则开始解析该JSON
        char* content = get_response_content(response);

        //判断想要保存的路径是否存在
        create_directory_if_not_exists(path);
        //判断后组成完整的路径
        strcat(path, filename);
        //将返回信息存入文件中
        FILE* file = fopen(path, "w");
        if (file) {
            fprintf(file, "%s\n", content);  // 将内容写入文件
            fclose(file);  // 关闭文件
            printf("Response saved to output.txt\n");
        }
        else {
            fprintf(stderr, "Failed to open file for writing.\n");
        }


        printf("API Response: %s\n", content);
        free(content); // 释放解析出来的内容
        free(response); // 释放API响应内存
    }
    else {
        //若无响应则输出失败
        fprintf(stderr, "Failed to get a response from the API.\n");
    }

    return 0;
}
