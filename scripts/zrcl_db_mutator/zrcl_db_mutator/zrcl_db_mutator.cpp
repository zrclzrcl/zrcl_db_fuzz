/*
* ������ zrcl_Richard_Zhang
* �������ڣ�2024-9-3
* ���ļ����ڱ�дzrcl���ƻ�������
* ��Ҫ����Ϊʵ��AFL++����ؽӿڣ�ʵ�ֿ��ƻ�����������SQL
* ��Ҫ���ɷ������ô������̵߳�ģʽ�����߳����ڽ����жϣ����߳���������LLM���粢���ɲ�������
*/
#include <cassert>
#include <fstream>
#include <iostream>
#include <memory>
#include <stack>
#include <string>

#include "afl-fuzz.h"
#include "config_validate.h"
#include "db.h"
#include "env.h"
#include "yaml-cpp/yaml.h"

void* afl_custom_init(afl_state_t* afl, unsigned int seed) {

}