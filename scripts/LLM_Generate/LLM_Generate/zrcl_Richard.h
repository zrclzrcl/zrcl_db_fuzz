#pragma once
#pragma once
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include "cJSON.h"


// 定义用于存储响应数据的结构
struct Memory {
    char* response;
    size_t size;
};

//使用的LLM API KEY 注意更改！
#define API_KEY "sk-zk2f9f24b5c15ff89a2642cb5ca134a9e20665fcb7849a17"

//回调函数，用于处理收到的数据
static size_t WriteCallback(void*, size_t, size_t, void*);

//链接LLM返回响应的函数，传递想使用的模型与信息
char* link_LLM(const char*, const char*);

//输入LLM响应字符串，只返回其内容
char* get_response_content(char*);

//创建目录函数，用于创建给定字符串所指向目录
void create_directory_if_not_exists(char*);
