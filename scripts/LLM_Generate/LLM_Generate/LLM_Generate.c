#include "zrcl_Richard.h"

int main(void) {
    const char* model = "gpt-3.5-turbo";
    const char* message = "Q: I want to test the bug of KingBaseES. Need to generate a SQL statement. When SQL are generate need considerate the following problems: 1. Syntax correctness; 2. Semantic correctness; 3. Functional uniqueness; 4. Statement complexity; 5. Functional diversity; 6. Nested layers. I will give you the DBMS meta-data.Can you generate a SQL statementfor me,remember step by step.";

    char* response = link_LLM(model, message);

    if (response) {
        //若有响应 则开始解析该JSON
        char* content = get_response_content(response);
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
