#注意，这里规定本脚本中使用的路径为绝对路径！并且无特殊情况路径的结尾是/如:/home'/'
import curses
import glob
import math
import os
import queue
import re
import threading
import concurrent.futures
import time
from pathlib import Path

from openai import OpenAI

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
            result_dict[key] = int(value)  # 假设值是数字，转换为整数
    return result_dict

def get_prompt(samples):
    prompt = """I want to perform fuzzy testing of SQLITE and need to generate test cases for it. Please forget all database application background and generate complex and out-of-the-way sqlite database test cases from the point of view of a fuzzy testing expert, generate test cases that are complex and try to trigger database crashes as much as possible. Each test case consists of several SQLs. Below I will give some sample test cases that can trigger more program coverage:"""

    for sample in samples:
        prompt += f"\n```sql\n{sample}\n```"

    prompt += """\nYou have to refer to the test cases I gave,add more contents base on the samples. And generate more test cases “randomly”. It is not only important to refer to the test cases I have given, but it is also important to think about the process of generating them according to the procedure I have given below.
    First of all, you need to make sure that the SQL syntax is correct when generating the test cases.
    Second, whether the generated test cases have sufficient statement diversity, there are no more statement types in the test cases, such as: MATCH, SELECT, INSERT, UPDATE, DELETE, CREATE DATABASE, CREATE TABLE, CREATE TEMPORARY TABLE, CREATE INDEX, CREATE VIEW, CREATE SEQUENCE, CREATE FUNCTION, CREATE PROCEDURE, CREATE TRIGGER, GRANT, REVOKE, BEGIN, COMMIT, ROLLBACK, MERGE, TRUNCATE. ANALYZE, EXPLAIN, SHOW, DESCRIBE and so on.
    Third, it is very important that the generated test cases test the functionality that the target database has and other databases do not. If not, it needs to be added to the test cases.
    Fourth, is the generated SQL complex enough, at least it's more complex than the structure of the sample I gave you.
    Fifth, check whether the SQL is semantically correct, and whether there is corresponding data in it to be manipulated, and if not, then create the insert data statement first to ensure that the statement can be successfully executed.
    Note that the generated statements must be very complex. Include multiple nesting with the use of functions, you can also create functions for testing!
    Based on the above description, you can start generating 3 test cases and start them with
    ```sql
    ```
    Separate the generated test cases. """
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
            self.vectorNow[key] = value

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
        self.selectTestcases=[0] * self.queueMaxLength #保存的前MAX个测试用例
        self.pointQueue = [0] * self.queueMaxLength    #得分队列

    def order_selectTestcases(self):
        had_zip = zip(self.selectTestcases,self.pointQueue) #将两个队列组合成为元组
        after_sorted = sorted(had_zip,reverse=True,key=lambda x:x[1])#使用元组的point进行排序
        self.selectTestcases,self.pointQueue = zip(*after_sorted)


    def append_in(self, testcase, point):
        #无论怎么添加，都需要进行排序
        if (self.lengthNow+1) == self.queueMaxLength:#当前队列已满 进行剔除处理

            #1.对比当前的与最小的哪个最小，若不如最小的则剔除
            if point <= self.pointQueue[self.lengthNow]:
                pass

            # 2.若比最小的大，则替换最小的，并排序
            else :
                self.pointQueue[self.lengthNow] = point
                self.selectTestcases[self.lengthNow] = testcase
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
        for i in range(0,3):
            selected_testcases.append(self.selectTestcases[i])  #将前3个加入数组
        return selected_testcases



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
def to_showmap(myqueue, testcase_path, showmap_path, showmap_out_path,stdscr):
    # ===================定义区===================
    current_id = 0  #记录当前的id
    cmd = ''    #保存需要执行的cmd
    showmap_stop_time = 0
    showmap_stop_num = 0
    # ===================定义区===================
    while True:
        try:    #尝试读取文件
            full_testcase_path, testcase_content = get_file_by_id(testcase_path,'id_',current_id)
            stdscr.addstr(10, 10, f"showmap处理信息：第{current_id}个正被读取")
            stdscr.refresh()
        except FileNotFoundError as e:  #若目标文件还没有被生成
            stdscr.addstr(10, 10, f"showmap处理信息：第{current_id}个还未被生成")
            stdscr.refresh()
            continue

        #得到cmd路径
        cmd = get_showmap_cmd(showmap_path, showmap_out_path, current_id, full_testcase_path)
        os.system(cmd)
        showmap_content = get_showmap_content(showmap_out_path, current_id)
        testcase_now = ZrclTestcase(current_id, testcase_content, showmap_content)
        try:
            myqueue.put(testcase_now, timeout=0.05)
        except queue.Full:
            start_time = time.time()
            stdscr.addstr(8, 10, "showmap过程状态：阻塞")
            stdscr.addstr(9, 10, "showmap过程信息：showmap子线程阻塞——showmap队列已满")
            stdscr.refresh()
            while True:
                try:
                    myqueue.put(testcase_now,block=False)
                    end_time = time.time()
                    showmap_stop_time += end_time - start_time
                    showmap_stop_num += 1
                    stdscr.addstr(7, 10, f"showmap过程总阻塞时长：{showmap_stop_time}s —— 阻塞次数：{showmap_stop_num}")
                    stdscr.addstr(8, 10, "showmap过程状态：正常")
                    stdscr.addstr(9, 10, f"showmap子线程结束阻塞，正常运行，本次阻塞时长：{end_time - start_time:.2f}s")
                    stdscr.refresh()
                    start_time = None
                    end_time = None
                    break
                except queue.Full:
                    continue

        current_id += 1


#LLM工作者方法，用于根据sample发送prompt,并保存响应的结果进入目标文件夹
#work_id 即发送的第几个prompt,用于作为文件后缀
#samples应为一个数组，里面是测试用例样本的内容
#model 定义使用的LLM模型
def llm_worker(work_id, samples, api_key, base_url, model, save_path, number_of_generate_testcase,manege_queue,stdscr):
    try:
        manege_queue.get(timeout=0.05)
    except queue.Empty:
        start_time = time.time()
        stdscr.addstr(12, 10, "llm过程消息1：llm子线程阻塞——llm队列为空")
        stdscr.refresh()
        while True:
            try:
                manege_queue.get(block=False)
                end_time = time.time()
                stdscr.addstr(12, 10, f"llm子线程结束阻塞，正常运行，本次阻塞时长：{end_time - start_time:.2f} s")
                stdscr.refresh()
                break
            except queue.Empty:
                continue
    prompt = get_prompt(samples)    #根据给定样本获取提示词
    start_id = work_id*number_of_generate_testcase - number_of_generate_testcase + 1
    start_time = time.time()
    client = OpenAI(api_key=api_key, base_url=base_url)
    llm_response =  client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ]
    )
    #将测试用例保存进入目标
    #1.使用正则表达式匹配 ```sql 和 ``` 之间的内容
    sql_cases = re.findall(r'```sql(.*?)```', llm_response.choices[0].message.content, re.DOTALL)
    for index,flag in enumerate(range(start_id, number_of_generate_testcase)):
        with open(f'{save_path}LLM_G_{flag}.txt', 'w') as file:
            file.write(sql_cases[index].strip())
    stop_time = time.time()
    stdscr.addstr(13, 10, f"llm消息2：目前已生成到{start_id + number_of_generate_testcase - 1}个测试用例,用时：{start_time - stop_time:.2f} s")
    stdscr.refresh()



def main(stdscr):
    #===================定义区===================
    api_key = 'sk-zk24aba6ad3b8fd4a0e90ad7e28e19c0e046712507bcc931'    #LLM-apikey
    model = 'gpt-3.5-turbo' #LLM-模型
    base_url = 'https://api.zhizengzeng.com/v1/'    #LLM所在的基本地址
    testcase_path = "/tmp/fuzz/default/queue/" #定义测试用例文件地址
    showmap_path = "/home/zrcl_db_fuzz/Squirrel/AFLplusplus/afl-showmap"   #定义showmap工具的路径
    showmap_out_path = '/home/showmap/' #定义showmap的输出路径
    generate_testcase_save_path = '/home/LLM_testcase/'
    showmap_queue_max_size = 10 #定义showmap子线程队列长度
    llm_queue_max_size = 50
    testcase_queue = queue.Queue(maxsize=showmap_queue_max_size)    #定义showmap线程通信队列
    llm_manege_queue = queue.Queue(maxsize=llm_queue_max_size)  #管理LLM输出数量，最多堆积20个
    process_count = 0   #处理数记录
    llm_count = 1   #记录发送LLM请求的数量，以及保存生成的测试用例的后缀
    process_now = None  #保存当前记录的测试用例用于处理
    showmap = ZrclMap() #实例化一个showmap
    select_testcase = ZrclSelectionQueue()  #实例化一个选择保存队列
    max_llm_workers = 5 #定义LLM线程池最大数量
    number_of_generate_testcase = 3 #定义每次调用生成多少个测试用例
    start_time = None #定义主过程阻塞开始时间
    end_time = None #定义主过程阻塞结束时间
    main_all_stop_time = 0
    main_all_stop_num = 0
    #===================定义区===================

    #===================主过程区===================
    #初始化，判断各路径是否存在，若不存在则创建文件夹
    if not Path(generate_testcase_save_path).exists():
        Path(generate_testcase_save_path).mkdir(parents=True)

    #初始化，输出区域
    curses.curs_set(0)  # 隐藏光标
    stdscr.nodelay(1)  # 设置为非阻塞模式
    stdscr.clear()
    height, width = stdscr.getmaxyx()  # 获取窗口的高度和宽度
    stdscr.addstr(1, 10, "cov覆盖LLM生成情况:")
    stdscr.addstr(2, 10, "="*20)
    stdscr.addstr(3, 10, "主过程总阻塞时长：0s —— 阻塞次数：0")
    stdscr.addstr(4, 10, "主过程状态：正常")
    stdscr.addstr(5, 10, "主过程信息：正常")
    stdscr.addstr(6, 10, "=" * 20)
    stdscr.addstr(7, 10, "showmap过程总阻塞时长：0s —— 阻塞次数：0")
    stdscr.addstr(8, 10, "showmap过程状态：正常")
    stdscr.addstr(9, 10, "showmap过程信息：正常")
    stdscr.addstr(10, 10, "showmap处理信息：正常")
    stdscr.addstr(11, 10, "=" * 20)
    stdscr.addstr(12, 10, "llm过程：")
    stdscr.addstr(13, 10, "llm消息1：")
    stdscr.addstr(14, 10, "llm消息2：")
    stdscr.refresh()

    #启动一个线程池，用于给LLM发送请求，并保存返回的测试用例
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_llm_workers) as llm_executor:

        #showmap子线程配置
        showmap_thread = threading.Thread(target=to_showmap, args=(testcase_queue, testcase_path, showmap_path, showmap_out_path,stdscr), daemon=True)
        showmap_thread.start()  #showmap子线程启动

        while True:
            #1.不断的取出队列中的测试用例进行处理
            try:
                process_now = testcase_queue.get(timeout=0.05)
            except queue.Empty:
                start_time = time.time()
                stdscr.addstr(4, 10, "主过程状态：阻塞")
                stdscr.addstr(5, 10, "主过程信息：主过程被showmap线程阻塞——showmap队列为空")
                stdscr.refresh()
                while True:
                    try:
                        process_now = testcase_queue.get(block=False)  # 尝试非阻塞地获取
                        end_time = time.time()
                        main_all_stop_time += end_time - start_time
                        main_all_stop_num += 1
                        stdscr.addstr(3, 10, f"主过程总阻塞时长：{main_all_stop_time:.2f}s —— 阻塞次数：{main_all_stop_num}")
                        stdscr.addstr(4, 10, "主过程状态：正常")
                        stdscr.addstr(5, 10,f"主线程结束showmap阻塞，正常运行，本次阻塞时长：{end_time - start_time:.2f}s")
                        stdscr.refresh()
                        start_time = None
                        end_time = None
                        break
                    except queue.Empty:
                        continue

            showmap.from_zrclTestcase_get_vectorNow(process_now)
            #2.对新的覆盖向量计算覆盖率得分,并尝试加入选择队列
            now_point = showmap.calculate_now_cov_get_point()
            select_testcase.append_in(process_now, now_point)
            #3.更新覆盖率向量
            showmap.recalculate_each_edgeCovPoint()

            #当选择了一个队列长度的测试用例后，开始选择前3个测试用例，并发送给子线程
            if process_count % showmap_queue_max_size == 0:
                #选择选择队列中前三个值，传递给子线程池进行处理
                selected_testcases = select_testcase.pop_one_combo()
                #子线程池发送请求并等待结果，结果保存进入
                try:
                    llm_manege_queue.put(1,timeout=0.05) #尝试向队列里放入一个值，用于管理队列缓冲区不超过限定的指标
                except queue.Full:
                    start_time = time.time()
                    stdscr.addstr(4, 10, "主过程状态：阻塞")
                    stdscr.addstr(5, 10, f"主过程被LLM线程池阻塞——LLM等待发送队列超过：{llm_queue_max_size}")
                    stdscr.refresh()
                    while True:
                        try:
                            llm_manege_queue.put(1,block=False) # 尝试非阻塞地插入
                            end_time = time.time()
                            main_all_stop_time += end_time - start_time
                            main_all_stop_num += 1
                            stdscr.addstr(3, 10,
                                          f"主过程总阻塞时长：{main_all_stop_time:.2f}s —— 阻塞次数：{main_all_stop_num}")
                            stdscr.addstr(4, 10, "主过程状态：正常")
                            stdscr.addstr(5, 10,
                                          f"主线程结束LLM阻塞，正常运行，本次阻塞时长：{end_time - start_time:.2f}s")
                            stdscr.refresh()
                            break
                        except queue.Full:
                            continue

                llm_executor.submit(llm_worker, llm_count, selected_testcases, api_key, base_url, model, generate_testcase_save_path, number_of_generate_testcase, llm_manege_queue,stdscr)

                llm_count += 1


            process_count += 1
    #===================主过程区===================


if __name__ == '__main__':
    curses.wrapper(main)