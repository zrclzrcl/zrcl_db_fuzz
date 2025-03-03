# 用于将其他数据库原始种子转化为目标数据库的种子
# 1. 读取所有的种子文件的路径下的种子
# 2. 确定当前需要转化为哪个数据库
# 3. 形成prompt，不断发送给LLM进行转化
# 4. 保存转化后的种子到指定路径
import os
import random
import re
import time


import chardet
from ollama import chat



def get_user_set():
    select_db = 0
    while True:
        print("请选择种子转化的目标数据库：")
        print("1-Sqlite 2-Mysql 3-PostgreSQL 4-mariadb 5-DuckDB")
        select_db = input()
        if select_db != '1' and select_db !='2' and select_db !='3' and select_db !='4' and select_db !='5':
            print("输入错误！")
        else: break
    print("请选择种子转化的蒸馏数：")
    print("表示多少个提纯出1个，如20则为每20个提取1个优秀种子进行转化 0为默认")
    cluster_num = input()
    if cluster_num == '0':
        if select_db == '1':
            cluster_num=23
        if select_db == '2':
            cluster_num=2
        if select_db == '3':
            cluster_num=28
        if select_db == '4':
            cluster_num=2
        if select_db == '5':
            cluster_num=6
    return select_db, cluster_num

def get_true_output_path(select_db):
    out_put_path = ""
    if select_db == 1:
        out_put_path = r"\sqlite_tseed"
    elif select_db == 2:
        out_put_path = r"\mysql_tseed"
    elif select_db == 3:
        out_put_path = r"\postgresql_tseed"
    elif select_db == 4:
        out_put_path = r"\mariadb_tseed"
    elif select_db == 5:
        out_put_path = r"\duckdb_tseed"
    return out_put_path
def add_to_path(select_db,path_list):
    sqlite_dseed_path = r"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\transform_sqlite_seed\sqlite_dseed"
    mysql_dseed_path = r"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\transform_mysql_seed\mysql_dseed"
    mariadb_dseed_path = r"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\scan_sql\mariaDB_dseed"
    postgres_dseed_path = r"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\scan_sql\postgre_dseed"
    duckdb_dseed_path = r"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\transform_duckdb_seed\duckdb_dseed"
    if select_db == '1':
        path_list.append(mysql_dseed_path)
        path_list.append(mariadb_dseed_path)
        path_list.append(postgres_dseed_path)
        path_list.append(duckdb_dseed_path)
    elif select_db == '2':
        path_list.append(sqlite_dseed_path)
        path_list.append(mariadb_dseed_path)
        path_list.append(postgres_dseed_path)
        path_list.append(duckdb_dseed_path)
    elif select_db == '3':
        path_list.append(mysql_dseed_path)
        path_list.append(sqlite_dseed_path)
        path_list.append(mariadb_dseed_path)
        path_list.append(duckdb_dseed_path)
    elif select_db == '4':
        path_list.append(mysql_dseed_path)
        path_list.append(sqlite_dseed_path)
        path_list.append(postgres_dseed_path)
        path_list.append(duckdb_dseed_path)
    elif select_db == '5':
        path_list.append(mysql_dseed_path)
        path_list.append(sqlite_dseed_path)
        path_list.append(mariadb_dseed_path)
        path_list.append(postgres_dseed_path)
def chat_llm(prompt):
    response = chat(
        model='deepseek-r1:32b',
        messages=[
            {
                'role': 'user',
                'content': prompt,
            }],
        options=
        {
            'temperature': 0.6
        },
    )
    return response.message.content

def trans_seed(select_db,cluster_num,path_list,out_put_path):
    #构建循环
    #每次循环开始处理一个其他数据库的种子
    target_db = ''
    if select_db == '1':
        target_db = r"sqlite"
    elif select_db == '2':
        target_db = r"mysql"
    elif select_db == '3':
        target_db = r"postgre"
    elif select_db == '4':
        target_db = r"mariadb"
    elif select_db == '5':
        target_db = r"duckdb"

    count_all = 0
    error_time = 0
    count_in_all_db = []
    for each_seed_path in path_list:
        count_in_one_db = 0
        #每一次循环处理一个其他数据库的所有种子
        #首先读取这个path下的所有文件
        files = [os.path.join(each_seed_path, f) for f in os.listdir(each_seed_path) if os.path.isfile(os.path.join(each_seed_path, f))]
        now_db = ''
        if 'mysql' in each_seed_path:
            now_db = 'mysql'
        elif 'sqlite' in each_seed_path:
            now_db = 'sqlite'
        elif 'mariaDB' in each_seed_path:
            now_db = 'mariadb'
        elif 'duckdb' in each_seed_path:
            now_db = 'duckdb'
        elif 'postgre' in each_seed_path:
            now_db = 'postgre'
        else:
            raise Exception("当前db识别错误！")
        # 循环处理，直到所有文件都被读取过
        while files:
            start_time = time.time()
            # 如果剩余文件不足20个，则取全部；否则随机抽取20个
            if len(files) < cluster_num:
                selected_files = files[:]  # 复制一份列表
                files = []  # 清空列表，表示所有文件都处理完了
            else:
                selected_files = random.sample(files, cluster_num)
                # 从剩余文件列表中移除已经选中的文件
                for f in selected_files:
                    files.remove(f)

            # 读取每个文件的内容
            contents = []
            for file in selected_files:
                with open(file, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result['encoding']
                try:

                    with open(file, "r", encoding=encoding, errors='replace') as f:
                        contents.append(f.read())
                except Exception as e:
                    pass

            all_testcase = ''
            for each_seed in contents:
                all_testcase += '\n```sql\n' + each_seed + '\n```\n'

            #这里得到了一次随机抽取的20个，现在开始给llm进行翻译
            pre_prompt = (f"*背景* 当前你正在为测试对象为{target_db}数据库模糊测试收集初始种子，下面是来自于{now_db}数据库的一些官方测试用例。"
                          f"你需要分析下面的测试用例，并选择一个优秀的测试用例并将其转化为{target_db}语法，并要求其完成的功能完全等效。\n*测试用例* ")
            post_prompt = (rf"*格式与目标* 注意，上述的测试用例通过 \n```sql\n \n```\n进行分割，你的目标是必须分析所有{cluster_num}个测试用例（包含多个SQL语句）后才能选择一个优秀的测试用例并把它转换为完全等效的{target_db}数据库的语法。你的转换后的结果也需要使用：选择了第几个测试用例 \n```sql\n （一个完整的测试用例） \n```\n进行包裹，不需要回答多余的部分只需要回答选择了第几个和测试用例转换后的结果即可。注意：你只允许进行等效的语法转换，保证在{target_db}数据库可以正确的等效运行，并且不要把选择的情况包裹进入```sql```中。"
                           rf"优秀的测试用例需要从如下几个方面考虑：1.是否能测试到边缘条件 2.是否有可能测试到更多功能 3.是否有可能达到更高的程序覆盖率 4.是否有可能触发数据库漏洞与bug 5.作为初始种子是否有更加复杂的结构易于后续的模糊测试种子变异。")

            all_prompt = pre_prompt + all_testcase + post_prompt
            llm_response = chat_llm(all_prompt)


            pattern = r'```sql\s+(.*?)\s+```'
            matches = re.findall(pattern, llm_response, re.DOTALL)
            if not os.path.exists(os.path.dirname(rf'{out_put_path}_{target_db}\{now_db}\\')):
                os.makedirs(os.path.dirname(rf'{out_put_path}_{target_db}\{now_db}\\'))
            try:
                with open(rf'{out_put_path}_{target_db}\{now_db}\{count_in_one_db}.txt', 'w', encoding='utf-8') as file:
                    file.write(matches[0])
            except Exception as e:
                count_all += 1
                count_in_one_db += 1
                print(f"当前总计转换{count_all}个，{now_db}的第{count_in_one_db}个。出现错误！\n {e}")
                error_time += 1
                continue
            count_all += 1
            count_in_one_db += 1
            end_time = time.time()
            print(f"{now_db}->{target_db}：当前总计转换{count_all}个，{now_db}的第{count_in_one_db}个。用时：{end_time-start_time:.2f}")
        count_in_all_db.append({f'{now_db}':count_in_one_db})
    return count_in_all_db, error_time
def main():
    # 参数定义区
    out_put_path = r"F:\Master\DBMS_FUZZ\zrcl_db_fuzz\util\to_target_tseed\output"

    select_target_db = 0
    cluster_count = 0
    need_transform_path_list = []

    # 主过程区
    select_target_db,cluster_count = get_user_set()  #获取用户需求，到底是转化为哪个数据库，蒸馏数是多少

    out_put_path += get_true_output_path(select_target_db)  #根据用户需求确定输出路径

    # 根据选择配置需要转换的路径序列
    add_to_path(select_target_db,need_transform_path_list)

    #添加之后，开始转化种子
    status,error_times = trans_seed(select_target_db,cluster_count,need_transform_path_list,out_put_path)
    for each_status in status:
        key,value = each_status.items()
        print(f"{key}:{value}")
    print(f"错误：{error_times}")
    input("转换完毕，输入任意字符退出")








if __name__ == '__main__':
    main()