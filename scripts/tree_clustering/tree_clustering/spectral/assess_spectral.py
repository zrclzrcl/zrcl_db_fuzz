#层次聚类产出各距离分割评估方法图
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from gensim.models import Word2Vec
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from joblib import Parallel, delayed
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.cluster import SpectralClustering
from sklearn.metrics.pairwise import cosine_similarity


#定义节点数据结构
class Node:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

class ZRCL_testcase_tree:
    def __init__(self, testcase_id, ast_tree, tree_root, sub_tree_roots):
        self.testcase_id = testcase_id  # 测试用例编号
        self.ast_tree = ast_tree  # 对应AST语法大树
        self.tree_root = tree_root  # 根节点
        self.sub_tree_roots = sub_tree_roots #子树初始节点

#拆析出每一个AST
def read_trees_from_file(file_path):
    """从文件读取树形结构数据"""
    with open(file_path, 'r') as file:
        content = file.read()
    return content.split('---')  # 以分隔符拆分内容

def parse_sql_string(sql_string):
    """解析 SQL 字符串并构建有向图"""
    stack = []  # 用于存储节点的栈
    current_node = None
    node_count = {}  # 记录每个节点的数量
    G = nx.DiGraph()  # 创建有向图

    # 将 SQL 字符串分割为 token
    tokens = sql_string.replace('(', ' ( ').replace(')', ' ) ').split()

    for token in tokens:
        if token == '(':
            if current_node is not None:
                stack.append(current_node)  # 将当前节点入栈
        elif token == ')':
            if stack:
                current_node = stack.pop()  # 弹出栈顶节点
        else:
            if token not in node_count:
                node_count[token] = 0
            node_count[token] += 1
            unique_name = f"{token}_{node_count[token]}"  # 生成唯一节点名称

            new_node = Node(unique_name, parent=current_node)  # 创建新节点

            G.add_node(unique_name)  # 添加节点到图中
            if current_node is not None:
                G.add_edge(current_node.name, unique_name)  # 添加边

            current_node = new_node

    return G  # 返回构建的图

#通过多个测试用例子结构图组合为一个大树结构图
def build_large_tree(trees):
    """构建大树结构"""
    root = Node('root')  # 创建统一的根节点
    G = nx.DiGraph()  # 创建有向图
    G.add_node(root.name)  # 添加根节点
    tree_roots = []  # 存储子树根节点

    for tree_str in trees:
        if tree_str.strip():
            tree_graph = parse_sql_string(tree_str.strip())  # 解析每棵树
            for node in tree_graph.nodes():
                if node.startswith('sqlStatement_'):  # 找到 SQL 语句根节点
                    G.add_edge(root.name, node)  # 添加边连接到统一根节点
                    tree_roots.append(node)
                    break
            G = nx.compose(G, tree_graph)  # 合并当前树到大树

    return G, tree_roots, root  # 返回大树、子树根节点列表和统一根节点


def random_walk(graph, start_node, walk_length):
    """进行随机游走"""
    walk = [start_node]  # 初始化游走路径
    for _ in range(walk_length):
        neighbors = list(graph.neighbors(start_node))  # 获取当前节点的邻居
        start_node = np.random.choice(neighbors) if neighbors else start_node  # 随机选择邻居
        walk.append(start_node)  # 添加到游走路径
    return walk

def train_random_walk(target_tree, tree_root):
    # 生成随机游走并训练 Word2Vec
    walks = []
    for node in target_tree.nodes():
        for _ in range(10):  # 可以根据需要调整游走次数
            walks.append(random_walk(target_tree, node, 5))  # 进行多次随机游走

    model = Word2Vec(walks, vector_size=64, window=5, min_count=1, sg=1)  # 训练 Word2Vec 模型
    return model.wv[tree_root.name]  # 获取根节点嵌入

def do_spectral_clustering(n_cluster ,embedding):
    #计算相似度
    similarity_matrix = cosine_similarity(embedding)

    #配置参数
    spectral_clustering = SpectralClustering(n_clusters=n_cluster, affinity='precomputed')

    #执行
    labels = spectral_clustering.fit_predict(similarity_matrix)
    silhouette = silhouette_score(embedding, labels)
    db_index = davies_bouldin_score(embedding, labels)
    return silhouette, db_index

def do_walk_and_clustering(all_roots, n_cluster):

    all_silhouette_scores = []
    all_bouldin_scores = []
    #对大树群进行数遍历图嵌入的随机游走重复30次
    for i in range(0,30):
        all_root_embeddings = []
        for each_root in all_roots:
            all_root_embeddings.append(train_random_walk(each_root.ast_tree, each_root.tree_root))
        all_root_embeddings = np.array(all_root_embeddings)  # np化
        try:
            silhouette_scores, davies_bouldin_scores = do_spectral_clustering(n_cluster, all_root_embeddings)
            all_silhouette_scores.append(silhouette_scores)
            all_bouldin_scores.append(davies_bouldin_scores)
        except Exception as e:
            print(f"Error with max_d={n_cluster}: {e}")
            continue  # 跳过本次循环

    avg_silhouette_score = np.mean(all_silhouette_scores)
    avg_bouldin_score = np.mean(all_bouldin_scores)
    return avg_silhouette_score, avg_bouldin_score





#主过程
def main():
    file_paths = [f'F:\\Master\\DBMS_FUZZ\\after_parser\\{i}.txt' for i in range(100)]
    all_roots = []
    for index,file_path in enumerate(file_paths):
        ast_contents = read_trees_from_file(file_path)#分割---
        large_tree, tree_roots, root = build_large_tree(ast_contents)
        all_roots.append(ZRCL_testcase_tree(index,large_tree,root,tree_roots))  # 添加到嵌入列表

    #此时已得到了所有的测试用例的ZRCL数据结构，进行随机游走与层次聚类
    results = Parallel(n_jobs=-1)(
        delayed(do_walk_and_clustering)(all_roots, n )for n in np.arange(2,99)
    )
    avg_silhouette_scores, avg_davies_bouldin_scores = zip(*results)

    # 绘制图表
    plt.figure(figsize=(10, 6))
    plt.plot(np.arange(2,99), avg_silhouette_scores,label='Silhouette Score', color='blue')
    plt.plot(np.arange(2,99), avg_davies_bouldin_scores,label='Davies-Bouldin Index', color='red')

    plt.xlabel('Number of max_d')
    plt.ylabel('Score')
    plt.title('Clustering Performance: Silhouette vs Davies-Bouldin Index')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
