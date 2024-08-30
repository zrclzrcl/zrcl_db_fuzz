#pragma once
#define _CRT_SECURE_NO_WARNINGS 1
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

//通过给定测试用例内容以及编号，在指定目录下创建LLM_X.txt 用于分割从LLM获取到的多个testcase
void write_test_case_to_file(const char*, int);

//给定总测试用例的路径加文件名，进行分割，存入多个txt
int split_testcases(char*);