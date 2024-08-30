#include "zrcl_Richard.h"

// 回调函数，用于处理收到的数据
static size_t WriteCallback(void* data, size_t size, size_t nmemb, void* userp) {
    size_t realsize = size * nmemb;
    struct Memory* mem = (struct Memory*)userp;

    // 显式类型转换为char*
    char* ptr = (char*)realloc(mem->response, mem->size + realsize + 1);
    if (ptr == NULL) {
        printf("Not enough memory (realloc returned NULL)\n");
        return 0;  // 内存分配失败
    }

    mem->response = ptr;
    memcpy(&(mem->response[mem->size]), data, realsize);
    mem->size += realsize;
    mem->response[mem->size] = '\0';

    return realsize;
}


// 构建请求并调用API的函数
char* link_LLM(const char* model, const char* message_content) {
    CURL* curl;
    CURLcode res;
    struct Memory chunk = { 0 }; // 初始化响应数据结构

    // 初始化cURL
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        // 构建JSON请求数据
        cJSON* root = cJSON_CreateObject();
        cJSON_AddStringToObject(root, "model", model);
        cJSON* messages = cJSON_AddArrayToObject(root, "messages");
        cJSON* message = cJSON_CreateObject();
        cJSON_AddStringToObject(message, "role", "user");
        cJSON_AddStringToObject(message, "content", message_content);
        cJSON_AddItemToArray(messages, message);

        // 将JSON对象转换为字符串
        char* post_data = cJSON_PrintUnformatted(root);
        cJSON_Delete(root); // 清理JSON对象

        // 设置cURL选项
        curl_easy_setopt(curl, CURLOPT_URL, "https://api.zhizengzeng.com/v1/chat/completions");

        // 设置API密钥
        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        char auth_header[256];
        snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", API_KEY);
        headers = curl_slist_append(headers, auth_header);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // 设置POST数据
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data);

        // 设置回调函数来接收响应数据
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)&chunk);

        //禁用SSL证书检查
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);

        // 执行请求
        res = curl_easy_perform(curl);

        // 检查请求是否成功
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
            free(chunk.response);
            chunk.response = NULL;
        }

        // 清理
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        free(post_data);
    }

    curl_global_cleanup();

    return chunk.response; // 返回API响应
}

//输入响应的JSON 输出其中的信息，若解析失败则返回相应的错误信息
char* get_response_content(char* response)
{
    // 解析JSON字符串
    cJSON* json = cJSON_Parse(response);
    if (json == NULL) {
        return "Error parsing JSON!\n";
    }

    // 访问 "choices" 数组中的第一个对象
    cJSON* choices = cJSON_GetObjectItemCaseSensitive(json, "choices");
    if (!cJSON_IsArray(choices)) {
        cJSON_Delete(json);
        return "Choices is not an array!\n";
    }

    cJSON* first_choice = cJSON_GetArrayItem(choices, 0);
    if (!cJSON_IsObject(first_choice)) {
        cJSON_Delete(json);
        return "First choice is not an object!\n";
    }

    // 获取 "message" 对象中的 "content"
    cJSON* message = cJSON_GetObjectItemCaseSensitive(first_choice, "message");
    if (!cJSON_IsObject(message)) {
        cJSON_Delete(json);
        return "Message is not an object!\n";
    }

    cJSON* content = cJSON_GetObjectItemCaseSensitive(message, "content");
    if (!cJSON_IsString(content)) {
        cJSON_Delete(json);
        return "Content is not a string!\n";
    }


    char* need_return = strdup(content->valuestring);





    // 清理JSON对象
    cJSON_Delete(json);

    return need_return;
}
