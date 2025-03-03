import os
import shutil


def extract_sql_files(source_dir, output_dir):
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 遍历源目录及其子目录
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.test'):
                # 构建源文件的完整路径
                source_file = os.path.join(root, file)
                # 构建目标文件的完整路径，扩展名改为.txt
                target_file = os.path.join(output_dir, os.path.splitext(file)[0] + '.txt')
                # 复制并重命名文件
                shutil.copyfile(source_file, target_file)
                print(f'已提取：{source_file} 到 {target_file}')


if __name__ == '__main__':
    source_path = input('请输入源路径：')
    output_path = input('请输入输出路径：')
    extract_sql_files(source_path, output_path)
