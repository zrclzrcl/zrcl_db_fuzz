import networkx as nx
from gensim.models import Word2Vec
from sklearn.cluster import KMeans, DBSCAN
import matplotlib.pyplot as plt
import numpy as np
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.neighbors import kneighbors_graph

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

def kmeans_clustering(all_root_embeddings, n_clusters):
    """ KMeans 聚类方法 """
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(all_root_embeddings)

    # 获取聚类中心
    cluster_centers = kmeans.cluster_centers_

    # 找到每个聚类中心最近的数据点
    closest_points = []
    for center in cluster_centers:
        distances = np.linalg.norm(all_root_embeddings - center, axis=1)
        closest_point_idx = np.argmin(distances)
        closest_points.append(closest_point_idx)

    # 计算评估指标
    silhouette = silhouette_score(all_root_embeddings, labels)
    db_index = davies_bouldin_score(all_root_embeddings, labels)

    return labels, closest_points, silhouette, db_index

def dbscan_clustering(all_root_embeddings, eps, min_samples):
    """ DBSCAN 聚类方法 """
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(all_root_embeddings)

    # 找到每个聚类的最近点
    unique_labels = set(labels)
    closest_points = []
    if -1 in unique_labels:  # 如果存在噪声
        unique_labels.remove(-1)

    for label in unique_labels:
        cluster_points = all_root_embeddings[labels == label]
        center = np.mean(cluster_points, axis=0)
        distances = np.linalg.norm(cluster_points - center, axis=1)
        closest_point_idx = np.argmin(distances)
        closest_points.append(np.where(labels == label)[0][closest_point_idx])

    # 计算评估指标
    silhouette = silhouette_score(all_root_embeddings, labels) if len(unique_labels) > 1 else -1
    db_index = davies_bouldin_score(all_root_embeddings, labels) if len(unique_labels) > 1 else -1

    return labels, closest_points, silhouette, db_index

def plot_knn_graph(all_root_embeddings, n_neighbors):
    """绘制 K 近邻图"""
    # 使用 KNN 构建邻接矩阵
    knn_graph = kneighbors_graph(all_root_embeddings, n_neighbors, mode='connectivity', include_self=False)

    # 使用 edges 方法从邻接矩阵创建图
    G_knn = nx.Graph(knn_graph)  # 直接用 knn_graph 创建图

    # 使用 Spring 布局可视化 KNN 图
    pos = nx.spring_layout(G_knn)
    plt.figure(figsize=(10, 8))
    nx.draw(G_knn, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold', edge_color='gray')
    plt.title('K Nearest Neighbors Graph')
    plt.show()


def main():
    # 读取多个文件并构建大树
    file_paths = [f'F:\\Master\\DBMS_FUZZ\\after_parser\\{i}.txt' for i in range(100)]
    all_root_embeddings = []  # 存储根节点嵌入

    # 进行20次聚类
    n_trials = 20
    kmeans_results = []
    dbscan_results = []

    for _ in range(n_trials):
        all_root_embeddings = []  # 重新初始化嵌入列表

        for file_path in file_paths:
            tree_strings = read_trees_from_file(file_path)  # 读取树数据
            large_tree, tree_roots, root = build_large_tree(tree_strings)  # 构建大树

            # 生成随机游走并训练 Word2Vec
            walks = []
            for node in large_tree.nodes():
                for _ in range(10):  # 可以根据需要调整游走次数
                    walks.append(random_walk(large_tree, node, 5))  # 进行多次随机游走

            model = Word2Vec(walks, vector_size=64, window=5, min_count=1, sg=1)  # 训练 Word2Vec 模型
            root_embedding = model.wv[root.name]  # 获取根节点嵌入
            all_root_embeddings.append(root_embedding)  # 添加到嵌入列表

        all_root_embeddings = np.array(all_root_embeddings)  # 转换为 NumPy 数组

        # KMeans 聚类
        kmeans_labels, kmeans_closest, kmeans_silhouette, kmeans_db_index = kmeans_clustering(all_root_embeddings, n_clusters=8)
        kmeans_results.append((kmeans_labels, kmeans_closest, kmeans_silhouette, kmeans_db_index))

        # DBSCAN 聚类
        eps = 0.5  # 示例参数
        min_samples = 5  # 示例参数
        dbscan_labels, dbscan_closest, dbscan_silhouette, dbscan_db_index = dbscan_clustering(all_root_embeddings, eps, min_samples)
        dbscan_results.append((dbscan_labels, dbscan_closest, dbscan_silhouette, dbscan_db_index))

    # 显示 KMeans 聚类结果和平均值
    print("KMeans Results (20 Trials):")
    for i, (labels, closest, silhouette, db_index) in enumerate(kmeans_results):
        print(f"Trial {i + 1}:")
        print("Labels:", labels)
        print("Closest Points:", closest)
        print("Silhouette Score:", silhouette)
        print("Davies-Bouldin Index:", db_index)
        print("-" * 40)

    # 计算并显示平均评估标准
    avg_kmeans_silhouette = np.mean([result[2] for result in kmeans_results])
    avg_kmeans_db_index = np.mean([result[3] for result in kmeans_results])
    print("Average KMeans Silhouette Score:", avg_kmeans_silhouette)
    print("Average KMeans Davies-Bouldin Index:", avg_kmeans_db_index)

    # 显示 DBSCAN 聚类结果和平均值
    print("\nDBSCAN Results (20 Trials):")
    for i, (labels, closest, silhouette, db_index) in enumerate(dbscan_results):
        print(f"Trial {i + 1}:")
        print("Labels:", labels)
        print("Closest Points:", closest)
        print("Silhouette Score:", silhouette)
        print("Davies-Bouldin Index:", db_index)
        print("-" * 40)

    # 计算并显示平均评估标准
    avg_dbscan_silhouette = np.mean([result[2] for result in dbscan_results if result[2] != -1])  # 排除 -1
    avg_dbscan_db_index = np.mean([result[3] for result in dbscan_results if result[3] != -1])  # 排除 -1
    print("Average DBSCAN Silhouette Score:", avg_dbscan_silhouette)
    print("Average DBSCAN Davies-Bouldin Index:", avg_dbscan_db_index)

if __name__ == "__main__":
    main()
