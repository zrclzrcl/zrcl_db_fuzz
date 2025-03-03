import os
import sys

def delete_empty_txt_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".txt"):
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    print(f"删除空文件: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python delete_empty_txt.py <目录路径>")
        sys.exit(1)
    target_dir = sys.argv[1]
    delete_empty_txt_files(target_dir)