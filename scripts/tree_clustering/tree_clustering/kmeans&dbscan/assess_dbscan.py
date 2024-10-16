#评估k means聚类方法的有效性并画图
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from gensim.models import Word2Vec
from joblib import Parallel, delayed
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score


class Node:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

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

def random_walk(graph, start_node, walk_length):
    """进行随机游走"""
    walk = [start_node]  # 初始化游走路径
    for _ in range(walk_length):
        neighbors = list(graph.neighbors(start_node))  # 获取当前节点的邻居
        start_node = np.random.choice(neighbors) if neighbors else start_node  # 随机选择邻居
        walk.append(start_node)  # 添加到游走路径
    return walk

def read_trees_from_file(file_path):
    """从文件读取树形结构数据"""
    with open(file_path, 'r') as file:
        content = file.read()
    return content.split('---')  # 以分隔符拆分内容

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

def dbscan_clustering(all_root_embeddings, eps, min_samples):
    """ DBSCAN 聚类方法 """
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(all_root_embeddings)

    # 计算评估指标
    try:
        silhouette = silhouette_score(all_root_embeddings, labels)
    except Exception as e:
        print(f"Error with eps={eps}: {e}")
        silhouette = -1

    try:
        db_index = davies_bouldin_score(all_root_embeddings, labels)
    except Exception as e:
        print(f"Error with eps={eps}: {e}")
        db_index = -1

    return silhouette, db_index

def process_file(file_path):
    tree_strings = read_trees_from_file(file_path)  # 读取树数据
    large_tree, tree_roots, root = build_large_tree(tree_strings)  # 构建大树

    # 生成随机游走并训练 Word2Vec
    walks = []
    for node in large_tree.nodes():
        for _ in range(10):  # 可以根据需要调整游走次数
            walks.append(random_walk(large_tree, node, 5))  # 进行多次随机游走

    model = Word2Vec(walks, vector_size=64, window=5, min_count=1, sg=1)  # 训练 Word2Vec 模型
    return model.wv[root.name]  # 获取根节点嵌入


def evaluate_dbscan(eps,min_samples, file_paths):
    silhouettes = []
    db_indexes = []

    for _ in range(20):
        all_root_embeddings = Parallel(n_jobs=-1)(
            delayed(process_file)(file_path) for file_path in file_paths
        )

        all_root_embeddings = np.array(all_root_embeddings)  # 转换为 NumPy 数组

        # KMeans 聚类
        silhouette, db_index = dbscan_clustering(all_root_embeddings, eps , min_samples)

        silhouettes.append(silhouette)
        db_indexes.append(db_index)

    avg_silhouette = np.mean(silhouettes)
    avg_db_index = np.mean(db_indexes)

    return avg_silhouette, avg_db_index

def main():
    file_paths = [f'F:\\Master\\DBMS_FUZZ\\after_parser\\{i}.txt' for i in range(100)]

    # 并行处理不同聚类数量
    results = Parallel(n_jobs=-1)(
        delayed(evaluate_dbscan)(eps,5, file_paths) for eps in np.arange(0.025,1.2,0.025)
    )

    avg_silhouette_scores, avg_davies_bouldin_scores = zip(*results)

    # 绘制图表
    plt.figure(figsize=(10, 6))
    plt.plot(np.arange(0.025,1.2,0.025), avg_silhouette_scores, label='Silhouette Score', color='blue')
    plt.plot(np.arange(0.025,1.2,0.025), avg_davies_bouldin_scores, label='Davies-Bouldin Index', color='red')

    plt.xlabel('Number of Clusters')
    plt.ylabel('Score')
    plt.title('Clustering Performance: Silhouette vs Davies-Bouldin Index')
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
