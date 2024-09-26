import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

#读取文件内容
def read_file_contents(file_path):
    with open(file_path, 'r') as file:
        return file.read()

#计算相似度



def calculate_similarity(contents):
    # 计算内容之间的相似度
    vectorized = np.array([list(map(ord, content)) for content in contents])  # 将字符转换为ASCII值
    similarities = cosine_similarity(vectorized)
    return similarities

def main(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)  # 创建输出文件夹
    files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]
    read_files = []

    while True:
        if len(read_files) >= 20 or len(files) == 0:
            if len(read_files) == 0:
                break

            # 计算相似度
            similarities = calculate_similarity(read_files)
            diff = np.abs(similarities - np.eye(len(similarities)))  # 获取差异
            max_diff_indices = np.unravel_index(np.argsort(diff, axis=None)[-2:], diff.shape)

            # 保存相似度差异最大的两个文件内容
            with open(os.path.join(output_folder, '1.txt'), 'w') as f:
                f.write(read_files[max_diff_indices[0][0]])
            with open(os.path.join(output_folder, '2.txt'), 'w') as f:
                f.write(read_files[max_diff_indices[0][1]])

            # 清空读取的文件内容
            read_files = []

        # 读取下一个文件
        if files:
            file_name = files.pop(0)
            file_path = os.path.join(input_folder, file_name)
            read_files.append(read_file_contents(file_path))

if __name__ == "__main__":
    input_folder = 'AFL++'  # 输入文件夹路径
    output_folder = 'output'  # 输出文件夹路径
    main(input_folder, output_folder)