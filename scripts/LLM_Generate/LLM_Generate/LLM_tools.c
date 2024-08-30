#include "zrcl_Richard.h"

// �ص����������ڴ����յ�������
static size_t WriteCallback(void* data, size_t size, size_t nmemb, void* userp) {
    size_t realsize = size * nmemb;
    struct Memory* mem = (struct Memory*)userp;

    // ��ʽ����ת��Ϊchar*
    char* ptr = (char*)realloc(mem->response, mem->size + realsize + 1);
    if (ptr == NULL) {
        printf("Not enough memory (realloc returned NULL)\n");
        return 0;  // �ڴ����ʧ��
    }

    mem->response = ptr;
    memcpy(&(mem->response[mem->size]), data, realsize);
    mem->size += realsize;
    mem->response[mem->size] = '\0';

    return realsize;
}


// �������󲢵���API�ĺ���
char* link_LLM(const char* model, const char* message_content) {
    CURL* curl;
    CURLcode res;
    struct Memory chunk = { 0 }; // ��ʼ����Ӧ���ݽṹ

    // ��ʼ��cURL
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if (curl) {
        // ����JSON��������
        cJSON* root = cJSON_CreateObject();
        cJSON_AddStringToObject(root, "model", model);
        cJSON* messages = cJSON_AddArrayToObject(root, "messages");
        cJSON* message = cJSON_CreateObject();
        cJSON_AddStringToObject(message, "role", "user");
        cJSON_AddStringToObject(message, "content", message_content);
        cJSON_AddItemToArray(messages, message);

        // ��JSON����ת��Ϊ�ַ���
        char* post_data = cJSON_PrintUnformatted(root);
        cJSON_Delete(root); // ����JSON����

        // ����cURLѡ��
        curl_easy_setopt(curl, CURLOPT_URL, "https://api.zhizengzeng.com/v1/chat/completions");

        // ����API��Կ
        struct curl_slist* headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        char auth_header[256];
        snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", API_KEY);
        headers = curl_slist_append(headers, auth_header);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        // ����POST����
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data);

        // ���ûص�������������Ӧ����
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void*)&chunk);

        //����SSL֤����
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);

        // ִ������
        res = curl_easy_perform(curl);

        // ��������Ƿ�ɹ�
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
            free(chunk.response);
            chunk.response = NULL;
        }

        // ����
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        free(post_data);
    }

    curl_global_cleanup();

    return chunk.response; // ����API��Ӧ
}

//������Ӧ��JSON ������е���Ϣ��������ʧ���򷵻���Ӧ�Ĵ�����Ϣ
char* get_response_content(char* response)
{
    // ����JSON�ַ���
    cJSON* json = cJSON_Parse(response);
    if (json == NULL) {
        return "Error parsing JSON!\n";
    }

    // ���� "choices" �����еĵ�һ������
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

    // ��ȡ "message" �����е� "content"
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





    // ����JSON����
    cJSON_Delete(json);

    return need_return;
}
