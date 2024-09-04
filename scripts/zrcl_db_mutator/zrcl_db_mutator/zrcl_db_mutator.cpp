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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include <direct.h>//win������
#include "alloc-inl.h"
#include "afl-fuzz.h"
#include <sys/stat.h>//linux
#include <sys/types.h>//linux
 
struct ZrclMutator {
	ZrclMutator() : fuzz_now(-1),fuzz_next(0) {				// ��ʼ�� fuzz_now Ϊ 0
		strcpy(LLM_in_dir, "../LLM_testcase/");  // ʹ�� strcpy ��ʼ���ַ�����
	}
	~ZrclMutator() {
		// �������Ҫ�������Դ�����������ﴦ��
		// Ŀǰû����Ҫ����Ķ�̬��Դ
	}
	char LLM_in_dir[50];
	int fuzz_now;
	int fuzz_next;
};

static int make_dir(char* dir_name) {

	// ����Ŀ¼
	if (mkdir(dir_name) == -1) {
		std::cerr << "can not create LLM testcase dir"<< std::endl;
		exit(-1);
		return 1;
	}
	return 0;
}


extern "C" {
	
	/*
	* ��ʼ��afl���ƻ�������
	* ��ʼ���Ĺ�������,��ǰ��δ֪
	* 
	*/
	void* afl_custom_init(afl_state_t* afl, unsigned int seed) {
		//��ʼ��һ����������
		ZrclMutator* mutator = new ZrclMutator();

		//����LLM���ɲ����������ļ���
		make_dir(mutator->LLM_in_dir);
		//����LLM���ӣ����ɲ�������
		//���س�ʼ���ı�����
		return mutator;
	}


	/*
	* �պ�������֪afl���ô���ƴ���ı������ٲ�������
	*/
	void afl_custom_splice_optout(void* data)
	{
		;
	}

	/*
	* ��Ҫ��fuzz����
	* ���ڽ��б��죬�����ر�������Ĵ�С
	* ��ʱ�ı���ΪLLM������
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
		* ��ȡLLM�Ĳ�������
		* ����ƴ���ַ������γ����µ�·��
		* �ж�·���ϵĲ��������Ƿ����
		* ��������ʱ�򷵻�0���������α��졣
		*/
		//ƴ���ַ���
		char char_tmp_next[30];
		char file_name[40] = "LLM_G_";
		char LLM_in_path[50];

		//����ƴ���ļ���
		strcpy(LLM_in_path, mutator->LLM_in_dir);	//��mutator�е�·��ȡ������LLM_in_path
		sprintf(char_tmp_next, "%d", mutator->fuzz_next);	//����һ�����Ե�����תΪ�ַ�������char_tmp_next
		strcat(file_name, char_tmp_next);//ƴ��ǰ׺������
		strcat(file_name, ".txt");
		//ƴ��·��
		strcat(LLM_in_path, file_name);

		//�õ�·���󣬿�ʼ��ȡ�ļ�
		FILE* file = fopen(LLM_in_path, "r");

		if (file == NULL) {
			//��ʱ���޷����ļ����ʾLLM�����ٶ����ڲ����ٶȣ�����0���������α���,��ֻʹ��SQUIRREL
			return 0;
		}

		//��ȡ�ļ���С
		fseek(file, 0, SEEK_END);
		size_t file_size = ftell(file);
		rewind(file);
		
		// ��ȡ�ļ����ݵ�������out_buf��
		size_t bytes_read = fread(*out_buf, 1, file_size, file);

		// �ر��ļ�
		fclose(file);

		// ���ض�ȡ���ֽ���
		return bytes_read;
	}
	
	//fuzzֹͣ��ɾ�����ƻ�������
	void afl_custom_deinit(ZrclMutator* data) { delete data; }

}