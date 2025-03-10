#注意，这里规定本脚本中使用的路径为绝对路径！并且无特殊情况路径的结尾是/如:/home'/'
import curses
import glob
import math
import os
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
import multiprocessing
from openai import OpenAI
from colorama import Fore, Style,init
import argparse
import heapq
import threading
import csv
import time
from collections import defaultdict

class DynamicIDAllocator:
    def __init__(self):
        self._recycled_ids = []       # 可回收ID堆
        self._max_id = 0              # 当前最大ID
        self._active_ids = set()      # 已分配ID集合
        self._lock = threading.Lock() # 线程锁
        self._total_allocated = 0 
        heapq.heapify(self._recycled_ids)

    def active_count(self) -> int:
        with self._lock:
            return len(self._active_ids)
        
    def acquire_id(self) -> int:
        with self._lock:
            self._total_allocated += 1
            if self._recycled_ids:
                new_id = heapq.heappop(self._recycled_ids)
            else:
                new_id = self._max_id
                self._max_id += 1
            self._active_ids.add(new_id)
            return new_id
    
    def release_id(self, id_num: int) -> None:
        with self._lock:
            if id_num in self._active_ids:
                self._active_ids.remove(id_num)
                heapq.heappush(self._recycled_ids, id_num)

allocator = DynamicIDAllocator()
passively_llm_generate = 0
saved_count = 0
variable_lock = threading.Lock()


#获得单次showmap的cmd指令行
def get_showmap_cmd(showmap_path, showmap_out_path, testcase_id, showmap_testcase):
    cmd = f"{showmap_path} -o {showmap_out_path}{testcase_id} -- /home/ossfuzz {showmap_testcase}"
    return cmd

#读取showmap对应id的内容
def get_showmap_content(showmap_out_path, testcase_id):
    result_dict = {}
    with open(f"{showmap_out_path}{testcase_id}", "r") as f:
        for line in f:
            key, value = line.strip().split(":")
            result_dict[int(key)] = int(value)  # 假设值是数字，转换为整数
    return result_dict

def get_prompt(samples,target_db,one_time_generete):
    prompt = f"""I want to perform fuzzy testing of {target_db} and need to generate test case for it. Please forget all database application background and generate complex and out-of-the-way {target_db} database test case from the point of view of a fuzzy testing expert, generate test cases that are complex and try to trigger database crashes as much as possible. Each test case consists of several SQLs. Below I will give a sample test case that can trigger more program coverage:"""

    for sample in samples:
        prompt += f"\n```sql\n{sample}\n```"

    prompt += f"""\nYou can refer to the test case I gave, add more contents base on the samples. And generate more test case randomly. It is not only important to refer to the test case I have given, but it is also important to think about the process of generating them according to the procedure I have given below.
    First of all, you need to make sure that the SQL syntax is correct when generating the test case.
    Second, whether the generated test case have sufficient statement diversity, there are no more statement types in the test case, such as: MATCH, SELECT, INSERT, UPDATE, DELETE, CREATE DATABASE, CREATE TABLE, CREATE TEMPORARY TABLE, CREATE INDEX, CREATE VIEW, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TRIGGER, GRANT, REVOKE, BEGIN, COMMIT, ROLLBACK, MERGE, TRUNCATE, ANALYZE, EXPLAIN, SHOW, DESCRIBE and so on.
    Third, it is very important that the generated test case test the functionality that the target database has and other databases do not. If not, it needs to be added to the test case.
    Fourth, is the generated SQL complex enough, at least it's more complex than the structure of the sample I gave you.
    Fifth, check whether the SQL is semantically correct, and whether there is corresponding data in it to be manipulated, and if not, then create the insert data statement first to ensure that the statement can be successfully executed.
    Note that the generated statements must be very complex. Include multiple nesting with the use of functions, you can also create functions for testing!
    Based on the above description, you can start generating {one_time_generete} test cases and start them with
    ```sql
    ```
    warp the generated test case. Now start generating sql testcase! Each testcase need have multiple sql. And just return the testcase!"""
    return prompt


#id 对应的测试用例id
#content 测试用例的内容
#showmap showmap的解析后字典
class ZrclTestcase:
    def __init__(self, testcase_id, content, showmap):
        self.id = testcase_id
        self.content = content
        self.showmap = showmap

#定义Map类用于计算覆盖率得分
class ZrclMap:
    def __init__(self):
        self.countVectors = [0]*65536   #每条边的覆盖计数
        self.binaryVectors = [0]*65536  #每条边是否被命中的情况
        self.eachEdgeCovPoint = [0]*65536   #每条边计算的覆盖得分
        self.vectorNow = [0] * 65536    #当前正在处理的向量
        self.mapSize = 65535    #总Map大小
        self.uniqueEdge = 0 #当前覆盖的唯一边总数


    #使用当前情况计算每条边的得分
    def calculate_edgeCovPoint(self):
        for index, countVector in enumerate(self.countVectors):
            if self.uniqueEdge == 0:    #当初始冷启动的时候，权重都是0
                pass
            else:
                self.eachEdgeCovPoint[index]=math.log(self.uniqueEdge / (1+countVector), 10)/math.sqrt(self.mapSize)

    #确定对应边是否已有值
    def is_index_exist(self, index):
        return self.binaryVectors[index]

    #向向量中添加一个覆盖
    def append_to_vector(self, index):
        self.countVectors[index] += 1
        if not self.binaryVectors[index]:
            self.binaryVectors[index]=1
            self.uniqueEdge += 1

    #获得指定位置的情况
    def get_index_data(self, index):
        return self.countVectors[index], self.binaryVectors[index]

    #从测试用例类转化进入当前处理向量
    def from_zrclTestcase_get_vectorNow(self, zrcl_testcase:ZrclTestcase):
        for key,value in zrcl_testcase.showmap.items():   #将每一个命中的边加入map
            self.vectorNow[int(key)] = value

    #计算当前向量的得分
    def calculate_now_cov_get_point(self):
        get_point = 0
        for index, is_hits in enumerate(self.vectorNow):
            if is_hits:
                get_point += self.eachEdgeCovPoint[index]
        return get_point

    #重新计算新的每边得分
    def recalculate_each_edgeCovPoint(self):
        for index, is_hits in enumerate(self.vectorNow):
            if is_hits:
                self.append_to_vector(index)
        self.calculate_edgeCovPoint()
        self.vectorNow = [0] * 65536



class ZrclSelectionQueue:
    def __init__(self):
        self.queueMaxLength = 10  # 最大个数
        self.lengthNow = 0  # 当前长度0开始计数
        self.selectTestcases=[ZrclTestcase(-1,None,None)] * self.queueMaxLength #保存的前MAX个测试用例
        self.pointQueue = [0] * self.queueMaxLength    #得分队列

    def order_selectTestcases(self):
        had_zip = zip(self.selectTestcases,self.pointQueue) #将两个队列组合成为元组
        after_sorted = sorted(had_zip,reverse=True,key=lambda x:x[1])#使用元组的point进行排序
        self.selectTestcases,self.pointQueue = list(zip(*after_sorted))
        self.selectTestcases = list(self.selectTestcases)
        self.pointQueue = list(self.pointQueue)


    def append_in(self, testcase, point):
        #无论怎么添加，都需要进行排序
        if self.lengthNow == self.queueMaxLength:#当前队列已满 进行剔除处理

            #1.对比当前的与最小的哪个最小，若不如最小的则剔除
            if point < self.pointQueue[self.lengthNow-1]:
                pass

            # 2.若比最小的大，则替换最小的，并排序
            else :
                self.pointQueue[self.lengthNow-1] = point
                self.selectTestcases[self.lengthNow-1] = testcase
                self.order_selectTestcases()

        #若队列没满 则直接加入到最后，并排序
        else :
            self.pointQueue[self.lengthNow] = point
            self.selectTestcases[self.lengthNow] = testcase
            self.lengthNow += 1
            self.order_selectTestcases()

    #用于弹出前3个测试用例，用于一次LLM调用样本
    def pop_one_combo(self):
        selected_testcases = []
        selected_testcases_to_str = []
        for i in range(0,3):
            if self.selectTestcases[i].id == -1:
                continue
            selected_testcases_to_str.append(self.selectTestcases[i].content)  #将前3个加入数组
            selected_testcases.append(self.selectTestcases[i])
        return selected_testcases,selected_testcases_to_str



#根据指定id获得完整文件名
def get_file_by_id(path, filename_prefix, current):
    # 构建文件名，假设文件名格式为 id_000000后接其他字符
    filename = f"{filename_prefix}{current:06d}*"  # 使用通配符匹配后缀
    file_path = os.path.join(path, filename)

    # 使用 glob 获取匹配的文件
    matched_files = glob.glob(file_path)

    # 如果找到匹配的文件，直接返回第一个文件的文件名
    if matched_files:
        with open(matched_files[0], "r") as file:
            content = file.read()
        return matched_files[0],content
    else:
        raise FileNotFoundError("文件不存在")

#不断产生ZrclTestcase的方法
#@myqueue 线程沟通的队列
#@testcase_path 测试用例所在的路径
#@showmap_path showmap工具所在的路径
#@showmap_out_path showmap输出结果保存的路径
def to_showmap(out_queue, testcase_path, showmap_path, showmap_out_path):
    # ===================定义区===================
    current_id = 0  #记录当前的id
    cmd = ''    #保存需要执行的cmd
    showmap_stop_time = 0
    showmap_stop_num = 0
    first_time = True
    # ===================定义区===================
    print("showmap子线程启动")
    while True:
        try:    #尝试读取文件
            full_testcase_path, testcase_content = get_file_by_id(testcase_path,'id:',current_id)

        except FileNotFoundError as e:  #若目标文件还没有被生成
            if first_time:
                print(Fore.YELLOW + f"showmap子线程: 当前目标队列文件 {current_id} 还未被生成" + Style.RESET_ALL)
                first_time = False
            continue
        print(Fore.YELLOW+f"showmap子线程: 正在处理 {current_id} 文件"+Style.RESET_ALL)
        first_time = True
        #得到cmd路径
        cmd = get_showmap_cmd(showmap_path, showmap_out_path, current_id, full_testcase_path)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        showmap_content = get_showmap_content(showmap_out_path, current_id)
        testcase_now = ZrclTestcase(current_id, testcase_content, showmap_content)
        out_queue.put(testcase_now)
        print(Fore.YELLOW + f"showmap子线程: {current_id} 文件的showmap结果已放入队列" + Style.RESET_ALL)
        current_id += 1


#LLM工作者方法，用于根据sample发送prompt,并保存响应的结果进入目标文件夹
#work_id 即发送的第几个prompt,用于作为文件后缀
#samples应为一个数组，里面是测试用例样本的内容
#model 定义使用的LLM模型
def llm_worker(samples, api_key, base_url, model, save_queue,target_db,one_time_generete):
    thread_id = allocator.acquire_id()
    try:
        print(Fore.LIGHTBLUE_EX + f"主动式大语言模型工作线程_{thread_id}:已启动，目前共有{allocator.active_count()}个主动线程正在运行。历史总计{allocator.total_allocated()}个" + Style.RESET_ALL)
        prompt = get_prompt(samples,target_db,one_time_generete)    #根据给定样本获取提示词
        start_time = time.time()
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_response =  client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        #将测试用例保存进入目标
        end_time = time.time()
        print(Fore.LIGHTBLUE_EX + f"主动式大语言模型工作线程_{thread_id}:生成结束，目前共有{allocator.active_count()}个主动线程正在运行。历史总计{allocator.total_allocated()}个 用时：{end_time-start_time:.2f}" + Style.RESET_ALL)
        save_queue.put(llm_response.choices[0].message.content)
    finally:
        allocator.release_id(thread_id)

def passively_llm_worker(selection_queue, api_key, base_url, model, save_queue,target_db,one_time_generete):
    global passively_llm_generate
    while True:
        start_time = time.time()
        testcases,samples = selection_queue.pop_one_combo()
        output = ''
        for testcases in testcases:
            output += ' ' + str(testcases.id)
        if output == '':
            output = '无'
        print(Fore.LIGHTGREEN_EX + f"被动式大语言模型工作线程: 使用了{output}" + Style.RESET_ALL)
        prompt = get_prompt(samples,target_db,one_time_generete)    #根据给定样本获取提示词
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_response =  client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt},
            ]
        )
        #将测试用例保存进入保存队列
        end_time = time.time()
        print(Fore.LIGHTGREEN_EX + f"被动式大语言模型工作线程: 使用了{output}，生成了第{passively_llm_generate+1}个测试用例。用时：{end_time-start_time:.2f}" + Style.RESET_ALL)
        save_queue.put(llm_response.choices[0].message.content)
        with variable_lock:
            passively_llm_generate += 1

def save_testcase(testcase_queue,save_path):
    #首先从队列获取测试用例
    #拿到测试用例并分割
    #保存分割后的测试用例进入目标文件夹
    global saved_count
    print("保存子线程已启动")
    while True:
        need_slice_testcase = testcase_queue.get()

        # 拿到测试用例并分割
        sql_cases = re.findall(r'```sql(.*?)```', need_slice_testcase, re.DOTALL)
        with variable_lock:
            for testcase in sql_cases:
                with open(f'{save_path}LLM_G_{saved_count+1}.txt', 'w') as file:
                    file.write(f'-- LLM Generated {saved_count+1}\n'+testcase.strip())
                    print(Fore.CYAN + f"保存子线程:当前第 {saved_count+1} 个LLM测试用例已生成" + Style.RESET_ALL)
                    saved_count += 1

def main():
    #===================定义区===================
   #LLM-apikey
    model = 'gpt-3.5-turbo' #LLM-模型
    base_url = 'https://api.zhizengzeng.com/v1/'    #LLM所在的基本地址
    testcase_path = "/tmp/fuzz/default/queue/" #定义测试用例文件地址
    showmap_path = "/home/zrcl_db_fuzz/Squirrel/AFLplusplus/afl-showmap"   #定义showmap工具的路径
    showmap_out_path = '/home/showmap/' #定义showmap的输出路径
    generate_testcase_save_path = '/home/LLM_testcase/'
    log_save_path = '/home/CCLLM_log/'
    showmap_queue_max_size = 10 #定义showmap子线程队列长度
    llm_queue_max_size = 50 #llm队列的最长个数
    save_queue = multiprocessing.Queue()  #保存需要保存为文件的测试用例分割前的队列
    testcase_queue = multiprocessing.Queue(maxsize=showmap_queue_max_size)    #定义showmap线程通信队列
    process_count = 0   #处理数记录
    llm_count = 0   #记录发送LLM请求的数量，以及保存生成的测试用例的后缀
    process_now = None  #保存当前记录的测试用例用于处理
    showmap = ZrclMap() #实例化一个showmap
    select_testcase = ZrclSelectionQueue()  #实例化一个选择保存队列
    max_llm_workers = 5 #定义LLM线程池最大数量
    number_of_generate_testcase = 3 #定义每次调用生成多少个测试用例
    start_time = None #定义主过程阻塞开始时间
    end_time = None #定义主过程阻塞结束时间
    main_all_stop_time = 0  #主进程的阻塞总时间
    main_all_stop_num = 0   #主进程的阻塞总次数
    refresh_countdown = time.time() #记录上次发送时间
    last_save_time = time.time() #记录上次保存日志时间

    global passively_llm_generate
    global saved_count


    main_log_path = '/home/main_log/log.txt'
    main_count = 0
    #===================定义区===================
    parser = argparse.ArgumentParser(description="LLM生成器")
    parser.add_argument('-t', help='发送阈值设置', required=True)
    parser.add_argument('-db', help='目标数据库设置，可以是sqlite,mysql,postgresql,duckdb,mariadb', required=True)
    parser.add_argument('-o', help='单次请求生成的测试用例数',default=1)
    parser.add_argument('-k', help='LLM-apikey',required=True)
    parser.add_argument('-bu', help='LLM-baseurl',default='https://api.zhizengzeng.com/v1/')
    parser.add_argument('-mo', help='LLM-model',default='deepseek-reasoner')
    # 解析命令行参数
    args = parser.parse_args()
    
    threshold = args.t  #阈值设置
    target_db = args.db #目标数据库
    number_of_generate_testcase = args.o    #单次请求生成的测试用例数

    api_key = args.k    #定义LLM-apikey
    base_url = args.bu  #有默认值的基本url
    model = args.mo     #有默认值的模型
    #===================主过程区===================

    init()

    
    #初始化，判断各路径是否存在，若不存在则创建文件夹
    if not Path(generate_testcase_save_path).exists():
        Path(generate_testcase_save_path).mkdir(parents=True)

    if not Path(showmap_out_path).exists():
        Path(showmap_out_path).mkdir(parents=True)

    if not Path(log_save_path).exists():
        Path(log_save_path).mkdir(parents=True)

    with open(log_save_path+"ccllm_log.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['time', 'passively_llm_generate', 'active_llm_generate', 'now_active_llm_worker', 'all_active_llm_worker', 'saved_count','process_count','meets_threshold'])

    with open(log_save_path+"point.csv", 'w', newline='', encoding='utf-8') as point_file:
        writer = csv.writer(point_file)
        writer.writerow(['time', 'id', 'point'])

    #初始化，输出区域


    saver_thread = multiprocessing.Process(target=save_testcase, args=(save_queue, generate_testcase_save_path), daemon=True)
    saver_thread.start()  # 保存子线程启动

    #showmap子线程配置
    showmap_thread = multiprocessing.Process(target=to_showmap, args=(testcase_queue, testcase_path, showmap_path, showmap_out_path), daemon=True)
    showmap_thread.start()  #showmap子线程启动

    pa_llm_thread = threading.Thread(target=passively_llm_worker, args=(
        select_testcase, api_key, base_url, model, save_queue,target_db,number_of_generate_testcase), daemon=True)
    pa_llm_thread.start()  #被动llm生成线程启动



    while True:
        #1.不断的取出队列中的测试用例进行处理
        process_now = testcase_queue.get()
        print(f"主程序:正在处理新的showmap数据 第 {main_count} 个")
        showmap.from_zrclTestcase_get_vectorNow(process_now)
        #2.对新的覆盖向量计算覆盖率得分,并尝试加入选择队列
        now_point = showmap.calculate_now_cov_get_point()
        print(f"主程序:第 {main_count} 个的得分为{now_point}")
        select_testcase.append_in(process_now, now_point)
        #3.更新覆盖率向量
        showmap.recalculate_each_edgeCovPoint()

        with open(log_save_path+"point.csv", 'a', newline='', encoding='utf-8') as point_file:
            writer = csv.writer(point_file)
            writer.writerow([time.time(), process_now.id , now_point])

        #当选择了一个队列长度的测试用例后，开始选择前3个测试用例，并发送给子线程
        #逻辑修改为，当得分超过阈值后，直接启动子线程
        if now_point >= threshold:
            #这里就应该直接获取到指定id的测试用例
            now_content_list = [process_now.content]
            llm_thread = threading.Thread(target=llm_worker, args=(now_content_list, api_key, base_url, model ,save_queue,target_db,number_of_generate_testcase), daemon=True)
            llm_thread.start()
            llm_count += 1
        
        
        process_count += 1
        if (process_count % 5 == 0 ) or (time.time() - last_save_time > 10):
            with variable_lock:
                with open(log_save_path+"ccllm_log.csv", 'a', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([time.time(), passively_llm_generate, allocator.total_allocated()*number_of_generate_testcase, allocator.active_count(), allocator.total_allocated(), saved_count, process_count, llm_count])
                    last_save_time = time.time()
        

    #===================主过程区===================

if __name__ == '__main__':
    main()
    #main(1) #测试用