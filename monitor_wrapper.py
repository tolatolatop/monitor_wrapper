import os
import sys
import argparse
from datetime import datetime

# 获取当前脚本的父目录路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "monitor_logs")
TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")
BINARY_LIST_FILE = os.path.join(SCRIPT_DIR, "binaries_list.txt")

def create_directories():
    # 创建日志目录
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        print(f"Log directory created: {LOG_DIR}")

    # 创建tools目录
    if not os.path.exists(TOOLS_DIR):
        os.makedirs(TOOLS_DIR)
        print(f"Tools directory created: {TOOLS_DIR}")

def generate_wrapper_script(binary_path, log_prefix):
    # 提取二进制文件名，用于生成唯一的包装脚本
    binary_name = os.path.basename(binary_path)
    script_name = f"wrapper_{binary_name}.sh"
    script_path = os.path.join(os.path.dirname(binary_path), script_name)

    # 生成的wrapper脚本内容
    script_content = f"""#!/bin/bash
LOG_FILE="{log_prefix}.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Executing: {binary_path} $@" >> "$LOG_FILE"
echo "[$TIMESTAMP] Environment: $(env)" >> "$LOG_FILE"

# 执行原始二进制文件
"{binary_path}_real" "$@"
"""
    with open(script_path, 'w') as script_file:
        script_file.write(script_content)
    
    os.chmod(script_path, 0o755)  # 使脚本可执行
    print(f"Wrapper script created for {binary_path}: {script_path}")

    # 替换原始程序为wrapper脚本
    original_program_backup = binary_path + "_real"
    if not os.path.exists(original_program_backup):
        os.rename(binary_path, original_program_backup)
    os.symlink(script_path, binary_path)
    print(f"{binary_path} replaced with wrapper script {script_name}")

    # 在tools目录中创建符号链接
    tool_link = os.path.join(TOOLS_DIR, binary_name)
    if os.path.exists(tool_link):
        os.remove(tool_link)
    os.symlink(script_path, tool_link)
    print(f"Symbolic link created in tools directory: {tool_link}")

def uninstall_wrapper(binary_path):
    original_program_backup = binary_path + "_real"
    binary_name = os.path.basename(binary_path)
    script_name = f"wrapper_{binary_name}.sh"
    script_path = os.path.join(os.path.dirname(binary_path), script_name)

    if os.path.islink(binary_path) and os.path.exists(original_program_backup):
        os.remove(binary_path)  # 删除符号链接
        os.rename(original_program_backup, binary_path)  # 恢复原始二进制文件
        print(f"{binary_path} restored to its original state.")
    
    # 删除独立的 wrapper 脚本
    if os.path.exists(script_path):
        os.remove(script_path)
        print(f"Wrapper script {script_name} removed for {binary_path}.")

    # 删除tools目录中的符号链接
    tool_link = os.path.join(TOOLS_DIR, binary_name)
    if os.path.exists(tool_link):
        os.remove(tool_link)
        print(f"Symbolic link removed from tools directory: {tool_link}")

def install_wrappers():
    create_directories()

    if not os.path.exists(BINARY_LIST_FILE):
        print(f"Error: Binary list file '{BINARY_LIST_FILE}' not found!")
        sys.exit(1)

    with open(BINARY_LIST_FILE, 'r') as file:
        for line in file:
            binary_path = line.strip()
            if not binary_path or not os.path.exists(binary_path):
                print(f"Warning: Binary '{binary_path}' does not exist, skipping...")
                continue
            
            binary_name = os.path.basename(binary_path)
            log_prefix = os.path.join(LOG_DIR, binary_name)
            generate_wrapper_script(binary_path, log_prefix)

    print("Monitor wrapper setup completed.")

def uninstall_wrappers():
    if not os.path.exists(BINARY_LIST_FILE):
        print(f"Error: Binary list file '{BINARY_LIST_FILE}' not found!")
        sys.exit(1)

    with open(BINARY_LIST_FILE, 'r') as file:
        for line in file:
            binary_path = line.strip()
            if not binary_path or not os.path.exists(binary_path + "_real"):
                print(f"Warning: No backup found for '{binary_path}', skipping...")
                continue
            
            uninstall_wrapper(binary_path)

    print("Uninstallation of monitor wrapper completed.")

def main():
    parser = argparse.ArgumentParser(description="Monitor Wrapper Tool")
    parser.add_argument("action", choices=["install", "uninstall"],
                        help="Specify whether to install or uninstall the wrappers.")
    
    args = parser.parse_args()

    if args.action == "install":
        install_wrappers()
    elif args.action == "uninstall":
        uninstall_wrappers()

if __name__ == "__main__":
    main()
