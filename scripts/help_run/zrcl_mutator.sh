#!/bin/bash

# 捕获 Ctrl+C (SIGINT) 信号，确保前台进程结束后，停止后台进程
trap 'kill 0' SIGINT

python3 /home/zrcl_db_fuzz/LLM_Generate_py/LLM_Generate_py/LLM_Generate.py &
python3 /home/zrcl_db_fuzz/Squirrel/scripts/utils/run_zrcl_mutator.py sqlite /home/zrcl_db_fuzz/Squirrel/data/fuzz_root/input


wait