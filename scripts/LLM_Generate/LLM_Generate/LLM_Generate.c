#include "zrcl_Richard.h"

int main(void) {
    const char* model = "gpt-4";
    const char* message = "Q: I want to test the bug of sqlite. Need to generate 15 testcases. Each testcases need Contains a complete sequence of sql statements. Remember that each test case needs to be complex enough to utilize a large number of functions and contain expansive functionality for comprehensive database testing. Also the substance of testcase are not just one SQL statement need be several statement, not a description of the test.";
    char path[1024] = "../LLM_Generate_testcase/";
    char* filename = "testcases.txt";

    //判断想要保存的路径是否存在
    create_directory_if_not_exists(path);
    //判断后组成完整的路径
    strcat(path, filename);

    char* response = link_llm(model, message);

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
    split_testcases(path);

    return 0;
}
