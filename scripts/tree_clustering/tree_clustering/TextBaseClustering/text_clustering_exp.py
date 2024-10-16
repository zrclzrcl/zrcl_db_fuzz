import os
import sys
import glob

import matplotlib.pyplot as plt
import pandas as pd
from numpy.array_api import arange
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from joblib import Parallel, delayed


def read_file_by_id(path, filename_prefix, current):
    # 构建文件名，假设文件名格式为 id_000000后接其他字符
    filename = f"{filename_prefix}{current:06d}*"  # 使用通配符匹配后缀
    file_path = os.path.join(path, filename)

    # 使用 glob 获取匹配的文件
    matched_files = glob.glob(file_path)

    # 如果找到匹配的文件，直接读取第一个文件
    if matched_files:
        with open(matched_files[0], 'r', encoding='utf-8') as file:
            content = file.read()
            return content
    else:
        print(f"没有找到匹配的文件以 {filename_prefix}{current:06d} 开头。")
        return None

def k_means(n_cluster):
    testcase_file_path = "I:\\Richard Zhang - zrcl\\BigLoong 备份\\2024-9-26\\Master\\DBMS_FUZZ\\实验数据\\变异生成文件保存\\docker_data_0_5"
    file_name_prefix = 'id_'
    testcases = []

    # 读取文件内容
    for current in range(0, 1000):
        file_content = read_file_by_id(testcase_file_path, file_name_prefix, current)
        if file_content:
            testcases.append(file_content)

    # 文本向量化
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(testcases)

    # KMeans 聚类
    kmeans = KMeans(n_clusters=n_cluster, random_state=42)
    kmeans.fit(X)
    clusters = kmeans.labels_

    # 打印聚类结果
    # for i, text in enumerate(testcases):
    #     print(f"Text: {text[:50]}, Cluster: {clusters[i]}")

    # 计算轮廓系数
    silhouette_avg = silhouette_score(X, clusters)
    print('*-*-'*20)
    print(f"轮廓系数 (Silhouette Coefficient)->1: {silhouette_avg} of cluster {n_cluster}")

    # 计算 Calinski-Harabasz 指数
    calinski_harabasz = calinski_harabasz_score(X.toarray(), clusters)
    print(f"Calinski-Harabasz 指数->big: {calinski_harabasz} of cluster {n_cluster}")

    # 计算 Davies-Bouldin 指数
    davies_bouldin = davies_bouldin_score(X.toarray(), clusters)
    print(f"Davies-Bouldin 指数->small: {davies_bouldin} of cluster {n_cluster}")
    # PCA 降维为 3 维
    pca = PCA(n_components=3)
    reduced_X = pca.fit_transform(X.toarray())

    # 绘制 3D 聚类结果
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(reduced_X[:, 0], reduced_X[:, 1], reduced_X[:, 2], c=clusters)
    ax.set_title(f"Text Clustering Visualization (3D) of cluster {n_cluster}")
    ax.set_xlabel("PCA Component 1")
    ax.set_ylabel("PCA Component 2")
    ax.set_zlabel("PCA Component 3")
    plt.show()
    return silhouette_avg,calinski_harabasz,davies_bouldin


def main(argv):
    # 并行计算
    results = Parallel(n_jobs=-1)(
        delayed(k_means)(n_cluster) for n_cluster in np.arange(2, 998)
    )
    silhouette_scores, calinski_harabasz_scores, davies_bouldin_scores = zip(*results)
    x_range = np.arange(2, 998)

    # Silhouette Score 图
    plt.figure(figsize=(10, 5))
    plt.plot(x_range, silhouette_scores, color='blue', label='Silhouette Score')
    plt.title('Silhouette Score')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Silhouette Score')
    plt.grid(True)
    plt.legend()
    plt.show()

    # Calinski-Harabasz Score 图
    plt.figure(figsize=(10, 5))
    plt.plot(x_range, calinski_harabasz_scores, color='green', label='Calinski-Harabasz Score')
    plt.title('Calinski-Harabasz Score')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Calinski-Harabasz Score')
    plt.grid(True)
    plt.legend()
    plt.show()

    # Davies-Bouldin Index 图
    plt.figure(figsize=(10, 5))
    plt.plot(x_range, davies_bouldin_scores, color='red', label='Davies-Bouldin Index')
    plt.title('Davies-Bouldin Index')
    plt.xlabel('Number of Clusters')
    plt.ylabel('Davies-Bouldin Index')
    plt.grid(True)
    plt.legend()
    plt.show()

    data = {
        'n_luster':arange(2,998),
        'Silhouette_Score': silhouette_scores,
        'Calinski-Harabasz_Score': calinski_harabasz_scores,
        'Davies-Bouldin_Index': davies_bouldin_scores
    }

    df = pd.DataFrame(data)
    df.to_csv('clustering_scores.csv', index=False)
if __name__ == '__main__':
    main(sys.argv)
