#pragma once
#pragma once
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include "cJSON.h"


// �������ڴ洢��Ӧ���ݵĽṹ
struct Memory {
    char* response;
    size_t size;
};

//ʹ�õ�LLM API KEY ע����ģ�
#define API_KEY "sk-zk2f9f24b5c15ff89a2642cb5ca134a9e20665fcb7849a17"

//�ص����������ڴ����յ�������
static size_t WriteCallback(void*, size_t, size_t, void*);

//����LLM������Ӧ�ĺ�����������ʹ�õ�ģ������Ϣ
char* link_LLM(const char*, const char*);

//����LLM��Ӧ�ַ�����ֻ����������
char* get_response_content(char*);

//����Ŀ¼���������ڴ��������ַ�����ָ��Ŀ¼
void create_directory_if_not_exists(char*);
