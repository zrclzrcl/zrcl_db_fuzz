/*
* 创建人 zrcl_Richard_Zhang
* 创建日期：2024-9-3
* 本文件用于编写zrcl客制化变异器
* 主要功能为实现AFL++的相关接口，实现客制化变异器生成SQL
* 主要生成方法采用创建新线程的模式，主线程用于进行判断，副线程用于链接LLM网络并生成测试用例
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