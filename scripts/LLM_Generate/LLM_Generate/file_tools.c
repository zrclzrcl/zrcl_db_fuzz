#include "zrcl_Richard.h"

// ����һ������������Ŀ¼
void create_directory_if_not_exists(char* path) {
    // ���Դ���Ŀ¼
    if (_mkdir(path) == 0) {
        printf("Directory created: %s\n", path);
    }
    else {
        if (errno == EEXIST) {
            // Ŀ¼�Ѿ�����
            printf("Directory already exists: %s\n", path);
        }
        else {
            // ��������
            fprintf(stderr, "Failed to create directory: %s\n", path);
        }
    }
}

//ͨ�������������������Լ���ţ���ָ��Ŀ¼�´���LLM_X.txt ���ڷָ��LLM��ȡ���Ķ��testcase
void write_test_case_to_file(const char* test_case, int case_number) {
    char filename[512];
    snprintf(filename, sizeof(filename), "../LLM_Generate_testcase/after_split/LLM_%d.txt", case_number);

    create_directory_if_not_exists("../LLM_Generate_testcase/after_split/");

    FILE* file = fopen(filename, "w");
    if (file) {
        fprintf(file, "%s\n", test_case);
        fclose(file);
        printf("Test case %d saved to %s\n", case_number, filename);
    }
    else {
        fprintf(stderr, "Failed to open file %s for writing.\n", filename);
    }
}

int split_testcases(char* full_path) {
    FILE* input_file = fopen(full_path, "r");
    if (input_file == NULL) {
        fprintf(stderr, "Failed to open input file.\n");
        return 1;
    }

    char line[1024];
    char test_case[10000] = { 0 };
    int case_number = 0;
    int in_test_case = 0;

    while (fgets(line, sizeof(line), input_file)) {
        if (strncmp(line, "```sql", 6) == 0) {
            // Detect the start of a SQL block
            in_test_case = 1;
            case_number++;
            continue;  // Skip the ```sql line itself
        }
        else if (strncmp(line, "```", 3) == 0 && in_test_case) {
            // Detect the end of a SQL block
            in_test_case = 0;
            write_test_case_to_file(test_case, case_number);
            memset(test_case, 0, sizeof(test_case));  // Reset the test case buffer
            continue;  // Skip the closing ``` line itself
        }

        if (in_test_case) {
            // Only concatenate lines that are within ```sql blocks
            strcat(test_case, line);
        }
    }

    fclose(input_file);
    return 0;
}


