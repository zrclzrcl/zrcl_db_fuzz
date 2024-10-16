#层次聚类产出结果
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from gensim.models import Word2Vec
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from sklearn.metrics import silhouette_score, davies_bouldin_score

#定义节点数据结构
class Node:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent

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


#主过程
def main():
    file_paths = [f'F:\\Master\\DBMS_FUZZ\\after_parser\\{i}.txt' for i in range(100)]
    all_root_embeddings = []
    for file_path in file_paths:
        ast_contents = read_trees_from_file(file_path)#分割---
        large_tree, tree_roots, root = build_large_tree(ast_contents)
        all_root_embeddings.append(train_random_walk(large_tree,root))  # 添加到嵌入列表

    #此时已得到了所有的测试用例的图嵌入结果

    #下一步使用图嵌入结果进行聚类
    all_root_embeddings = np.array(all_root_embeddings) #np化

    Z = linkage(all_root_embeddings, method='ward')  # 使用 Ward 方法
    # 绘制树状图
    plt.figure(figsize=(10, 7))
    dendrogram(Z, labels=[f'Point {i}' for i in range(len(all_root_embeddings))])
    plt.title('Hierarchical Clustering Dendrogram')
    plt.xlabel('Data Points')
    plt.ylabel('Distance')
    plt.show()

    # 提取聚类
    max_d = 0.05  # 根据树状图设定距离阈值
    clusters = fcluster(Z, max_d, criterion='distance')

    # 输出聚类结果
    print("Cluster assignments:", clusters)

    silhouette = silhouette_score(all_root_embeddings, clusters)
    db_index = davies_bouldin_score(all_root_embeddings, clusters)
    print("Silhouette Score:", silhouette)
    print("Davies-Bouldin Index:", db_index)


if __name__ == "__main__":
    main()
