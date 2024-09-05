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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include <direct.h>//win下启动
#include "afl-fuzz.h"
#include <sys/stat.h>//linux
#include <sys/types.h>//linux
 
struct ZrclMutator {
	ZrclMutator() : fuzz_now(-1),fuzz_next(0) {				// 初始化 fuzz_now 为 0
		strcpy(LLM_in_dir, "/home/LLM_testcase/");  // 使用 strcpy 初始化字符数组
	}
	~ZrclMutator() {
		// 如果有需要清理的资源，可以在这里处理
		// 目前没有需要清理的动态资源
	}
	char LLM_in_dir[50];
	int fuzz_now;
	int fuzz_next;
};


extern "C" {
	
	/*
	* 初始化afl客制化变异器
	* 初始化的工作内容,当前还未知
	* 
	*/
	void* afl_custom_init(afl_state_t* afl, unsigned int seed) {
		//初始化一个变异器类
		ZrclMutator* mutator = new ZrclMutator();


		//返回初始化的变异器
		return mutator;
	}


	/*
	* 空函数，告知afl不用传递拼接文本，减少参数传递
	*/
	void afl_custom_splice_optout(void* data)
	{
		;
	}

	/*
	* 主要的fuzz函数
	* 用于进行变异，并返回变异输入的大小
	* 此时的变异为LLM的生成
	*/
	size_t afl_custom_fuzz(
		ZrclMutator* mutator,
		unsigned char* buf, 
		size_t buf_size, 
		unsigned char** out_buf, 
		unsigned char* add_buf, 
		size_t add_buf_size, 
		size_t max_size)
	{
		/*
		* 读取LLM的测试用例
		* 首先拼接字符串，形成最新的路径
		* 判断路径上的测试用例是否存在
		* 当不存在时则返回0，跳过本次变异。
		*/
		//拼接字符串
		char char_tmp_next[30];
		char file_name[40] = "LLM_G_";
		char LLM_in_path[50];

		//首先拼接文件名
		strcpy(LLM_in_path, mutator->LLM_in_dir);	//将mutator中的路径取出放入LLM_in_path
		sprintf(char_tmp_next, "%d", mutator->fuzz_next);	//将下一个测试的数字转为字符串存入char_tmp_next
		strcat(file_name, char_tmp_next);//拼接前缀与数字
		strcat(file_name, ".txt");
		//拼接路径
		strcat(LLM_in_path, file_name);

		//得到路径后，开始读取文件
		FILE* file = fopen(LLM_in_path, "r");

		if (file == NULL) {
			//此时若无法打开文件则表示LLM生成速度慢于测试速度，返回0，跳过本次变异,则只使用SQUIRREL
			return 0;
		}

		//获取文件大小
		fseek(file, 0, SEEK_END);
		size_t file_size = ftell(file);
		rewind(file);
		
		// 读取文件内容到缓冲区out_buf中


		size_t bytes_read = fread(*out_buf, 1, file_size, file);

		// 关闭文件
		fclose(file);

		// 返回读取的字节数
		return bytes_read;
	}
	
	//fuzz停止后，删除客制化变异器
	void afl_custom_deinit(ZrclMutator* data) { delete data; }

}