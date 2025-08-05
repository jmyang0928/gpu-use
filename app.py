from flask import Flask, render_template, jsonify, request
import subprocess
import threading
import time
import re
import json
import os
import logging
import uuid
from datetime import datetime

app = Flask(__name__)
gpu_info = {}
processes = []
disk_info = []

# 數據文件路徑
COMMANDS_FILE = "gpu_commands.json"
LOG_FILE = "gpu_monitor.log"
EXECUTION_LOG_DIR = "task_executions"  # 任務執行記錄目錄

# 確保執行記錄目錄存在
os.makedirs(EXECUTION_LOG_DIR, exist_ok=True)

# 設置日誌配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_commands():
    """從文件讀取指令表格數據"""
    try:
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, 'r', encoding='utf-8') as f:
                commands = json.load(f)
            
            # 數據遷移：將舊的 id 字段轉換為 uid
            migrated = False
            for cmd in commands:
                if 'id' in cmd and 'uid' not in cmd:
                    cmd['uid'] = str(uuid.uuid4())
                    del cmd['id']  # 移除舊的 id 字段
                    migrated = True
                    logger.info(f"Migrated command to UID: {cmd['uid']}")
            
            # 如果有遷移，保存更新後的數據
            if migrated:
                save_commands(commands)
                logger.info("Command data migration completed")
            
            return commands
        else:
            return []
    except Exception as e:
        logger.error(f"❌ Error loading commands: {e}")
        return []

def save_commands(commands):
    """保存指令表格數據到文件"""
    try:
        with open(COMMANDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(commands, f, ensure_ascii=False, indent=2)
        logger.info(f"Commands saved successfully. Total: {len(commands)}")
        return True
    except Exception as e:
        logger.error(f"Error saving commands: {e}")
        return False

def add_command(command_text, required_gpu):
    """新增指令到表格"""
    commands = load_commands()
    
    # 生成新的UUID作為唯一ID
    new_uid = str(uuid.uuid4())
    
    new_command = {
        'uid': new_uid,
        'command': command_text,
        'required_gpu': required_gpu,
        'created_at': datetime.now().isoformat(),
        'order': len(commands) + 1
    }
    
    commands.append(new_command)
    
    if save_commands(commands):
        logger.info(f"Command added: UID={new_uid}, GPU={required_gpu}")
        return new_command
    else:
        logger.error(f"Failed to add command: UID={new_uid}")
        return None

def get_commands():
    """讀取所有指令（按順序排列）"""
    commands = load_commands()
    # 按order字段排序
    return sorted(commands, key=lambda x: x.get('order', 0))

def delete_command(command_uid):
    """刪除指定UID的指令"""
    commands = load_commands()
    original_count = len(commands)
    
    logger.info(f"Attempting to delete command with UID: {command_uid}")
    logger.info(f"Total commands before deletion: {original_count}")
    
    # 檢查是否存在該 UID
    found_command = None
    for cmd in commands:
        if cmd.get('uid') == command_uid:
            found_command = cmd
            break
    
    if not found_command:
        logger.warning(f"Command with UID {command_uid} not found")
        logger.info(f"Available UIDs: {[cmd.get('uid') for cmd in commands]}")
        return False
    
    # 過濾掉要刪除的指令
    commands = [cmd for cmd in commands if cmd.get('uid') != command_uid]
    
    if len(commands) < original_count:
        # 重新排序order字段
        for i, cmd in enumerate(commands):
            cmd['order'] = i + 1
        
        if save_commands(commands):
            logger.info(f"Command deleted: UID={command_uid}")
            return True
        else:
            logger.error(f"Failed to delete command: UID={command_uid}")
    
    return False

def execute_task(command_text, required_gpu, task_uid, actual_gpu_ids=None):
    """執行任務並記錄結果"""
    try:
        # 創建以時間命名的執行記錄資料夾 - 時間在前，UUID在後
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 使用絕對路徑確保腳本執行時能找到正確位置
        abs_execution_log_dir = os.path.abspath(EXECUTION_LOG_DIR)
        execution_dir = os.path.join(abs_execution_log_dir, f"{timestamp}_task_{task_uid}")
        os.makedirs(execution_dir, exist_ok=True)
        
        # 獲取完整的任務資訊
        commands = load_commands()
        task_info = None
        for cmd in commands:
            if cmd.get('uid') == task_uid:
                task_info = cmd
                break
        
        # 處理GPU IDs
        cuda_visible_devices = None
        gpu_ids_str = "Not specified"
        if actual_gpu_ids is not None and len(actual_gpu_ids) > 0:
            cuda_visible_devices = ','.join(map(str, actual_gpu_ids))
            gpu_ids_str = str(actual_gpu_ids)
        
        # 保存執行的指令到 command.txt
        command_file = os.path.join(execution_dir, "command.txt")
        with open(command_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Task Information ===\n")
            f.write(f"Task UID: {task_uid}\n")
            f.write(f"Required GPU: {required_gpu}\n")
            f.write(f"Actual GPU IDs: {gpu_ids_str}\n")
            f.write(f"CUDA_VISIBLE_DEVICES: {cuda_visible_devices if cuda_visible_devices is not None else 'Not set'}\n")
            f.write(f"Execution Time: {datetime.now().isoformat()}\n")
            
            if task_info:
                f.write(f"Task Created At: {task_info.get('created_at', 'Unknown')}\n")
                f.write(f"Task Order: {task_info.get('order', 'Unknown')}\n")
                
                # 計算任務等待時間
                try:
                    created_time = datetime.fromisoformat(task_info.get('created_at', ''))
                    wait_time = datetime.now() - created_time
                    f.write(f"Wait Time: {str(wait_time).split('.')[0]} (HH:MM:SS)\n")
                except:
                    f.write(f"Wait Time: Unable to calculate\n")
            
            # 系統資訊
            f.write(f"\n=== System Information ===\n")
            f.write(f"Execution Directory: {execution_dir}\n")
            f.write(f"Working Directory: {execution_dir}\n")
            f.write(f"Python PID: {os.getpid()}\n")
            f.write(f"User: {os.environ.get('USER', 'Unknown')}\n")
            f.write(f"Host: {os.environ.get('HOSTNAME', 'Unknown')}\n")
            
            f.write(f"\n=== Command to Execute ===\n")
            f.write(f"{command_text}\n")
            f.write(f"\n" + "="*50 + "\n")

        # 保存純指令到 command.sh
        simple_command_file = os.path.join(execution_dir, "command.sh")
        with open(simple_command_file, 'w', encoding='utf-8') as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"# Task UID: {task_uid}\n")
            f.write(f"# Command executed on: {datetime.now().isoformat()}\n\n")
            f.write(f"{command_text}\n")
        
        # 準備輸出記錄檔案
        output_file = os.path.join(execution_dir, "output.log")
        
        logger.info(f"Executing task {task_uid} for GPU {required_gpu}")
        logger.info(f"Execution directory: {execution_dir}")
        
        # 創建獨立的執行腳本
        script_file = os.path.join(execution_dir, "execute.sh")
        abs_output_file = os.path.join(execution_dir, "output.log")
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated execution script\n")
            f.write(f"# Task UID: {task_uid}\n")
            f.write(f"# Required GPU: {required_gpu}\n")
            f.write(f"# Actual GPU IDs: {gpu_ids_str}\n")
            f.write(f"# Start Time: {datetime.now().isoformat()}\n")
            f.write("\n")
            f.write("# 設置嚴格模式\n")
            f.write("set -u\n")
            f.write("\n")
            
            # 設置環境變量
            if cuda_visible_devices is not None:
                f.write(f"export CUDA_VISIBLE_DEVICES={cuda_visible_devices}\n")
            
            f.write("# 設置工作目錄\n")
            f.write(f"cd '{execution_dir}'\n")
            f.write("\n")
            f.write("# 創建輸出文件\n")
            f.write(f"touch '{abs_output_file}'\n")
            f.write("\n")
            f.write("# 記錄執行開始\n")
            f.write(f"echo '=== Task Execution Log ===' >> '{abs_output_file}'\n")
            f.write(f"echo 'Task UID: {task_uid}' >> '{abs_output_file}'\n")
            f.write(f"echo 'Required GPU: {required_gpu}' >> '{abs_output_file}'\n")
            f.write(f"echo 'Actual GPU IDs: {gpu_ids_str}' >> '{abs_output_file}'\n")
            if cuda_visible_devices is not None:
                f.write(f"echo 'CUDA_VISIBLE_DEVICES: {cuda_visible_devices}' >> '{abs_output_file}'\n")
            else:
                f.write(f"echo 'CUDA_VISIBLE_DEVICES: Not set' >> '{abs_output_file}'\n")
            f.write(f"echo 'Start Time: {datetime.now().isoformat()}' >> '{abs_output_file}'\n")
            f.write(f"echo 'Execution Directory: {execution_dir}' >> '{abs_output_file}'\n")
            f.write(f"echo 'Working Directory: '$(pwd) >> '{abs_output_file}'\n")
            
            if task_info:
                f.write(f"echo 'Task Created: {task_info.get('created_at', 'Unknown')}' >> '{abs_output_file}'\n")
                f.write(f"echo 'Task Order: {task_info.get('order', 'Unknown')}' >> '{abs_output_file}'\n")
            
            f.write(f"echo 'Command: {command_text}' >> '{abs_output_file}'\n")
            f.write(f"echo 'Shell: /bin/bash' >> '{abs_output_file}'\n")
            f.write(f"echo '============================================================' >> '{abs_output_file}'\n")
            f.write(f"echo 'EXECUTION OUTPUT BEGINS:' >> '{abs_output_file}'\n")
            f.write(f"echo '============================================================' >> '{abs_output_file}'\n")
            f.write("\n")
            f.write("# 執行實際指令並捕獲退出碼\n")
            f.write("{\n")
            f.write(f"  {command_text}\n")
            f.write(f"}} >> '{abs_output_file}' 2>&1\n")
            f.write("command_exit_code=$?\n")
            f.write("\n")
            f.write("# 記錄執行結束\n")
            f.write(f"echo '' >> '{abs_output_file}'\n")
            f.write(f"echo '============================================================' >> '{abs_output_file}'\n")
            f.write(f"echo 'Task completed at: '$(date -Iseconds) >> '{abs_output_file}'\n")
            f.write(f"echo 'Exit code: '$command_exit_code >> '{abs_output_file}'\n")
            f.write(f"echo '============================================================' >> '{abs_output_file}'\n")
            f.write("\n")
            f.write("# 以指令的退出碼退出腳本\n")
            f.write("exit $command_exit_code\n")
        
        # 讓腳本可執行
        os.chmod(script_file, 0o755)
        
        # 準備環境變量
        env = os.environ.copy()
        if cuda_visible_devices is not None:
            env['CUDA_VISIBLE_DEVICES'] = cuda_visible_devices
            logger.info(f"Setting CUDA_VISIBLE_DEVICES={cuda_visible_devices} for task {task_uid}")
        
        # 使用絕對路徑執行腳本，並等待一小段時間確保啟動
        abs_script_path = os.path.abspath(script_file)
        nohup_cmd = f"nohup bash {abs_script_path} &"
        
        logger.info(f"Executing command: {nohup_cmd}")
        logger.info(f"Working directory: {execution_dir}")
        
        process = subprocess.Popen(
            nohup_cmd,
            shell=True,
            executable="/bin/bash",
            cwd=execution_dir,
            env=env,
            preexec_fn=os.setsid  # 創建新的程序群組，完全脫離父程序
        )
        
        # 等待一小段時間確保腳本開始執行
        time.sleep(0.1)
        
        # 創建一個任務狀態文件
        status_file = os.path.join(execution_dir, "status.json")
        status_data = {
            "task_uid": task_uid,
            "required_gpu": required_gpu,
            "actual_gpu_ids": actual_gpu_ids,
            "cuda_visible_devices": cuda_visible_devices,
            "start_time": datetime.now().isoformat(),
            "execution_method": "nohup_independent",
            "script_file": script_file,
            "execution_directory": execution_dir,
            "command": command_text
        }
        
        if task_info:
            status_data.update({
                "created_at": task_info.get('created_at'),
                "order": task_info.get('order')
            })
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Task {task_uid} started independently using nohup")
        logger.info(f"Script file: {script_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error executing task {task_uid}: {e}")
        
        # 如果執行失敗，記錄錯誤
        try:
            error_file = os.path.join(execution_dir, "error.log")
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Task Execution Error ===\n")
                f.write(f"Task UID: {task_uid}\n")
                f.write(f"Error Time: {datetime.now().isoformat()}\n")
                f.write(f"Error Message: {str(e)}\n")
                f.write(f"Required GPU: {required_gpu}\n")
                f.write(f"Command: {command_text}\n")
        except:
            pass
        
        return False

def check_gpu_availability(required_gpu):
    """檢查指定的GPU是否可用"""
    try:
        # 解析 required_gpu 字串，支援多種格式
        if required_gpu.lower() == 'any':
            # 尋找任何可用的GPU
            for gpu_id, gpu_data in gpu_info.items():
                if not gpu_data.get('in_use', True):
                    return True, [gpu_id]
            return False, None
        
        # 檢查多GPU格式 (例如 "0,1,2" 或 "0,2")
        if ',' in required_gpu:
            gpu_ids = []
            try:
                for gpu_str in required_gpu.split(','):
                    gpu_id = int(gpu_str.strip())
                    if gpu_id in gpu_info:
                        gpu_data = gpu_info[gpu_id]
                        if gpu_data.get('in_use', True):
                            # 有任何一個GPU被佔用就不能執行
                            return False, None
                        gpu_ids.append(gpu_id)
                    else:
                        # GPU不存在
                        return False, None
                # 所有GPU都可用
                return len(gpu_ids) > 0, gpu_ids
            except ValueError:
                # 解析失敗
                return False, None
        
        # 檢查特定GPU ID
        if required_gpu.isdigit():
            gpu_id = int(required_gpu)
            if gpu_id in gpu_info:
                gpu_data = gpu_info[gpu_id]
                return not gpu_data.get('in_use', True), [gpu_id]
        
        # 檢查GPU類型或名稱 (部分匹配)
        for gpu_id, gpu_data in gpu_info.items():
            if required_gpu.lower() in gpu_data.get('name', '').lower():
                return not gpu_data.get('in_use', True), [gpu_id]
        
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking GPU availability: {e}")
        return False, None

def auto_execute_tasks():
    """自動檢查並執行可用的任務"""
    try:
        commands = get_commands()
        if not commands:
            return
        
        for command in commands:
            command_uid = command.get('uid')
            command_text = command.get('command')
            required_gpu = command.get('required_gpu')
            
            if not all([command_uid, command_text, required_gpu]):
                continue
            
            # 檢查GPU是否可用
            is_available, available_gpu_ids = check_gpu_availability(required_gpu)
            
            if is_available:
                logger.info(f"GPU {available_gpu_ids} is available for task {command_uid}")
                
                # 執行任務，傳遞實際使用的GPU ID列表
                if execute_task(command_text, required_gpu, command_uid, available_gpu_ids):
                    # 執行成功，移除任務
                    if delete_command(command_uid):
                        logger.info(f"Task {command_uid} executed and removed from queue")
                    else:
                        logger.error(f"Task {command_uid} executed but failed to remove from queue")
                    
                    # 只執行一個任務，避免同時執行太多任務
                    break
                else:
                    logger.error(f"Failed to execute task {command_uid}")
    
    except Exception as e:
        logger.error(f"Error in auto_execute_tasks: {e}")

def update_command_order(command_uid, new_order):
    """更新指令的順序"""
    commands = load_commands()
    
    # 找到要移動的指令
    target_cmd = None
    for cmd in commands:
        if cmd.get('uid') == command_uid:
            target_cmd = cmd
            break
    
    if not target_cmd:
        logger.warning(f"Command not found for order update: UID={command_uid}")
        return False
    
    # 移除目標指令
    commands = [cmd for cmd in commands if cmd.get('uid') != command_uid]
    
    # 確保new_order在有效範圍內
    new_order = max(1, min(new_order, len(commands) + 1))
    
    # 在新位置插入指令
    commands.insert(new_order - 1, target_cmd)
    
    # 重新排序所有指令的order字段
    for i, cmd in enumerate(commands):
        cmd['order'] = i + 1
    
    success = save_commands(commands)
    if success:
        logger.info(f"Command order updated: UID={command_uid}, new_order={new_order}")
    else:
        logger.error(f"Failed to update command order: UID={command_uid}")
    
    return success

def parse_disk_usage():
    global disk_info
    logger.info("Starting disk usage monitoring thread")
    while True:
        try:
            result = subprocess.run(["df", "-h"], capture_output=True, text=True)
            output = result.stdout
            
            lines = output.strip().split('\n')
            disk_info = []
            
            # 跳過標題行
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    filesystem = parts[0]
                    size = parts[1]
                    used = parts[2]
                    available = parts[3]
                    use_percent = parts[4].rstrip('%')
                    mounted_on = parts[5]
                    
                    # 過濾掉一些系統檔案系統，只顯示主要磁碟
                    if not filesystem.startswith(('tmpfs', 'udev', 'devpts', 'sysfs', 'proc', 'cgroup')):
                        # 解析容量大小並過濾小於1GB的磁碟
                        def parse_size_to_gb(size_str):
                            """將容量字符串轉換為GB數值"""
                            try:
                                if size_str.endswith('G'):
                                    return float(size_str[:-1])
                                elif size_str.endswith('T'):
                                    return float(size_str[:-1]) * 1024
                                elif size_str.endswith('M'):
                                    return float(size_str[:-1]) / 1024
                                elif size_str.endswith('K'):
                                    return float(size_str[:-1]) / (1024 * 1024)
                                else:
                                    # 如果沒有單位，假設是字節
                                    return float(size_str) / (1024 * 1024 * 1024)
                            except:
                                return 0
                        
                        size_gb = parse_size_to_gb(size)
                        
                        # 只保留容量大於等於1GB的磁碟
                        if size_gb >= 1.0:
                            try:
                                use_percent_int = int(use_percent)
                            except ValueError:
                                use_percent_int = 0
                            
                            disk_info.append({
                                'filesystem': filesystem,
                                'size': size,
                                'used': used,
                                'available': available,
                                'use_percent': use_percent_int,
                                'mounted_on': mounted_on
                            })
            
            logger.debug(f"Disk usage updated: {len(disk_info)} disks")
                        
        except Exception as e:
            logger.error(f"Error running df -h: {e}")
            disk_info = []
        
        time.sleep(10)  # 磁碟資訊更新頻率較低

def parse_nvidia_smi():
    global gpu_info, processes
    logger.info("Starting NVIDIA SMI monitoring thread")
    while True:
        try:
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            output = result.stdout

#             output = """Sun Aug  3 15:39:03 2025
# +-----------------------------------------------------------------------------------------+
# | NVIDIA-SMI 570.133.07             Driver Version: 570.133.07     CUDA Version: 12.8     |
# |-----------------------------------------+------------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
# |                                         |                        |               MIG M. |
# |=========================================+========================+======================|
# |   0  NVIDIA GeForce RTX 4070        Off | 00000000:01:00.0  Off  |                  N/A |
# |  0%   35C    P8              8W / 200W  |    15MiB / 12282MiB    |     0%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   1  NVIDIA GeForce RTX 4090        Off | 00000000:02:00.0  Off  |                  N/A |
# | 12%   45C    P2            110W / 450W  |  8124MiB / 24576MiB    |    56%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   2  NVIDIA GeForce RTX 4080        Off | 00000000:03:00.0  Off  |                  N/A |
# | 20%   49C    P2            85W / 320W   |  4200MiB / 16384MiB    |    70%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   3  NVIDIA GeForce RTX 4070 Ti     Off | 00000000:04:00.0  Off  |                  N/A |
# |  5%   40C    P3            60W / 285W   |  300MiB / 12282MiB     |    12%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   4  NVIDIA GeForce RTX 4060        Off | 00000000:05:00.0  Off  |                  N/A |
# |  0%   33C    P8             6W / 115W   |    10MiB / 8192MiB     |     0%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   5  NVIDIA GeForce RTX 4070        Off | 00000000:06:00.0  Off  |                  N/A |
# | 45%   60C    P1           180W / 200W   | 12000MiB / 12282MiB    |    95%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   6  NVIDIA GeForce RTX 3080        Off | 00000000:07:00.0  Off  |                  N/A |
# | 18%   51C    P2           210W / 320W   | 10000MiB / 10240MiB    |    88%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
# |   7  NVIDIA GeForce RTX 3060        Off | 00000000:08:00.0  Off  |                  N/A |
# |  2%   37C    P8             9W / 170W   |   200MiB / 12288MiB    |     2%      Default  |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+

# +-----------------------------------------------------------------------------------------+
# | Processes:                                                                              |
# |  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
# |        ID   ID                                                               Usage      |
# |=========================================================================================|
# |    0   N/A  N/A            1059      G   /usr/lib/xorg/Xorg                        4MiB |
# |    1   N/A  N/A           23450      C   python3                                4096MiB |
# |    1   N/A  N/A           23451      C   /usr/bin/jupyter-notebook               4028MiB |
# |    2   N/A  N/A           24500      C   /usr/bin/python3                        4200MiB |
# |    3   N/A  N/A           24800      C   /opt/render/render_worker               300MiB |
# |    5   N/A  N/A           25333      C   /home/jimmy/train_model.py            12000MiB |
# |    6   N/A  N/A           26000      C   /home/jimmy/stable_diffusion.py        8000MiB |
# |    6   N/A  N/A           26001      C   /usr/lib/python3.11/tensorflow         2000MiB |
# |    7   N/A  N/A           26200      C   /usr/lib/firefox                         200MiB |
# +-----------------------------------------------------------------------------------------+
# """

            lines = output.strip().split('\n')

            gpu_info = {}
            processes = []

            # ---------- Parse GPU summary ----------
            for i, line in enumerate(lines):
                if re.match(r"\|\s+\d+\s+", line):
                    try:
                        idx = int(line.split()[1])
                        next_line = lines[i + 1] if i + 1 < len(lines) else ""
                        mem_info_match = re.search(r"(\d+)MiB\s*/\s*(\d+)MiB", next_line)
                        util_match = re.search(r"(\d+)%", next_line)

                        if mem_info_match:
                            mem_used = int(mem_info_match.group(1))
                            mem_total = int(mem_info_match.group(2))
                            mem_percent = round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0.0
                            util = int(util_match.group(1)) if util_match else 0

                            gpu_info[idx] = {
                                'name': f'GPU {idx}',
                                'mem_total': mem_total,
                                'mem_used': mem_used,
                                'mem_percent': mem_percent,
                                'util': util,
                                'in_use': False
                            }
                    except Exception as e:
                        logger.error(f"GPU summary parse error: {e}")

            # ---------- Parse Processes block (new format) ----------
            # 找到 Processes 區塊
            processes_block = output.split("Processes:")[1].strip()

            # 每行為一筆 process，跳過表頭與分隔線
            lines = processes_block.splitlines()
            process_lines = [
                line for line in lines if re.match(r"\|\s+\d+", line)
            ]

            parsed_processes = []
            for line in process_lines:
                # 用正則表達式擷取欄位資料
                match = re.match(
                    r"\|\s*(\d+)\s+N/A\s+N/A\s+(\d+)\s+(\w)\s+(.+?)\s+(\d+MiB)\s*\|", line
                )
                if match:
                    gpu_id, pid, ptype, pname, mem_usage = match.groups()
                    parsed_processes.append({
                        "gpu_id": int(gpu_id),
                        "pid": int(pid),
                        "type": ptype,
                        "process_name": pname.strip(),
                        "gpu_memory": mem_usage
                    })

            # 將解析結果轉換為原有的格式並標記 GPU 使用狀態
            for proc in parsed_processes:
                processes.append({
                    'gpu': proc['gpu_id'],
                    'pid': proc['pid'],
                    'type': proc['type'],
                    'name': proc['process_name'],
                    'mem': proc['gpu_memory']
                })

                if proc['gpu_id'] in gpu_info:
                    gpu_info[proc['gpu_id']]['in_use'] = True

            logger.debug(f"GPU data updated: {len(gpu_info)} GPUs, {len(processes)} processes")
            
            # 自動檢查並執行可用的任務
            auto_execute_tasks()

        except Exception as e:
            logger.error(f"Error running nvidia-smi: {e}")
            gpu_info = {
                0: {
                    'name': f"GPU error - {str(e)}",
                    'mem_total': 0,
                    'mem_used': 0,
                    'mem_percent': 0,
                    'util': 0,
                    'in_use': False
                }
            }
            processes = []

        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/executions')
def executions_page():
    """Execution history page"""
    return render_template('executions.html')

@app.route('/api/executions')
def api_executions():
    """API endpoint to get execution list"""
    try:
        executions = []
        executions_dir = EXECUTION_LOG_DIR  # 使用正確的執行目錄
        
        if not os.path.exists(executions_dir):
            return jsonify({'success': True, 'executions': []})
        
        for dir_name in os.listdir(executions_dir):
            dir_path = os.path.join(executions_dir, dir_name)
            if os.path.isdir(dir_path):
                execution_info = {
                    'directory': dir_name,
                    'created_time': 0,
                    'command_file': '',
                    'output_size': 0,
                    'output_preview': '',
                    'has_error_log': False
                }
                
                # Get creation time
                try:
                    execution_info['created_time'] = os.path.getctime(dir_path)
                except:
                    execution_info['created_time'] = 0
                
                # Read command file
                command_file_path = os.path.join(dir_path, 'command.txt')
                if os.path.exists(command_file_path):
                    try:
                        with open(command_file_path, 'r', encoding='utf-8') as f:
                            execution_info['command_file'] = f.read()
                    except Exception as e:
                        execution_info['command_file'] = f'Error reading command file: {str(e)}'
                
                # Check for error log
                error_file_path = os.path.join(dir_path, 'error.log')
                if os.path.exists(error_file_path):
                    execution_info['has_error_log'] = True

                # Calculate output size and get preview
                output_file_path = os.path.join(dir_path, 'output.log')
                if os.path.exists(output_file_path):
                    try:
                        size = os.path.getsize(output_file_path)
                        execution_info['output_size'] = size
                        with open(output_file_path, 'r', encoding='utf-8') as f:
                            # Read last 500 chars for status check
                            f.seek(0, os.SEEK_END)
                            end_pos = f.tell()
                            f.seek(max(0, end_pos - 500))
                            execution_info['output_preview'] = f.read()
                    except:
                        pass
                
                executions.append(execution_info)        # Sort by creation time (newest first)
        executions.sort(key=lambda x: x['created_time'], reverse=True)
        
        return jsonify({'success': True, 'executions': executions})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/execution/<execution_dir>')
def execution_detail_page(execution_dir):
    """Individual execution detail page"""
    return render_template('execution_detail.html')

@app.route('/api/executions/<execution_dir>/info')
def api_execution_info(execution_dir):
    """API endpoint to get detailed execution information"""
    try:
        executions_dir = EXECUTION_LOG_DIR  # 使用正確的執行目錄
        dir_path = os.path.join(executions_dir, execution_dir)
        
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return jsonify({'success': False, 'error': 'Execution directory not found'})
        
        execution_info = {
            'directory': execution_dir,
            'created_time': 0,
            'command_file': '',
            'output_log': '',
            'output_preview': '',
            'output_truncated': False,
            'error_log': '',
            'script_file': '',
            'output_size': 0
        }
        
        # Get creation time
        try:
            execution_info['created_time'] = os.path.getctime(dir_path)
        except Exception as e:
            execution_info['created_time'] = 0
        
        # Read command file
        command_file_path = os.path.join(dir_path, 'command.txt')
        if os.path.exists(command_file_path):
            try:
                with open(command_file_path, 'r', encoding='utf-8') as f:
                    execution_info['command_file'] = f.read()
            except Exception as e:
                execution_info['command_file'] = f'Error reading command file: {str(e)}'
        
        # Read output log (with preview option)
        output_file_path = os.path.join(dir_path, 'output.log')
        if os.path.exists(output_file_path):
            try:
                execution_info['output_size'] = os.path.getsize(output_file_path)
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    # 讀取前2000個字符作為預覽
                    preview = f.read(2000)
                    execution_info['output_preview'] = preview
                    execution_info['output_truncated'] = len(preview) == 2000;
                    
                    # 如果檔案不大，也提供完整內容
                    if execution_info['output_size'] <= 10000:  # 10KB以下提供完整內容
                        f.seek(0)
                        execution_info['output_log'] = f.read()
            except Exception as e:
                execution_info['output_preview'] = f'Error reading output file: {str(e)}'
        
        # Read error log  
        error_file_path = os.path.join(dir_path, 'error.log')
        if os.path.exists(error_file_path):
            try:
                with open(error_file_path, 'r', encoding='utf-8') as f:
                    execution_info['error_log'] = f.read()
            except Exception as e:
                execution_info['error_log'] = f'Error reading error file: {str(e)}'
        
        # Read script file
        script_file_path = os.path.join(dir_path, 'execute.sh')
        if os.path.exists(script_file_path):
            try:
                with open(script_file_path, 'r', encoding='utf-8') as f:
                    execution_info['script_file'] = f.read()
            except Exception as e:
                execution_info['script_file'] = f'Error reading script file: {str(e)}'
        
        # 目錄資訊
        execution_info['directory_info'] = {
            'path': dir_path,
            'created_time': execution_info['created_time'],
            'modified_time': 0,
            'size': 0
        }
        
        try:
            execution_info['directory_info']['modified_time'] = os.path.getmtime(dir_path)
            execution_info['directory_info']['size'] = sum(
                os.path.getsize(os.path.join(dir_path, f)) 
                for f in os.listdir(dir_path) 
                if os.path.isfile(os.path.join(dir_path, f))
            )
        except:
            pass
        
        return jsonify({'success': True, 'info': execution_info})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/executions/<execution_dir>/output')
def api_execution_output(execution_dir):
    """API endpoint to get full execution output"""
    try:
        output_file = os.path.join(EXECUTION_LOG_DIR, execution_dir, 'output.log')
        
        if not os.path.isfile(output_file):
            return jsonify({
                'success': False,
                'error': '輸出檔案不存在'
            }), 404
        
        with open(output_file, 'r', encoding='utf-8') as f:
            output_content = f.read()
        
        return jsonify({
            'success': True,
            'output': output_content,
            'size': len(output_content)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/gpu_data')
def gpu_data():
    return jsonify({
        'gpus': gpu_info,
        'processes': processes
    })

@app.route('/disk_data')
def disk_data():
    return jsonify({
        'disks': disk_info
    })

@app.route('/logs')
def get_logs():
    """獲取最近的日誌記錄"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return jsonify({
                'success': True,
                'logs': lines[-100:]  # 返回最近100行日誌
            })
        else:
            return jsonify({
                'success': True,
                'logs': []
            })
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ========== 指令管理 API ==========

@app.route('/commands', methods=['GET'])
def get_commands_api():
    """獲取所有指令"""
    commands = get_commands()
    return jsonify({
        'success': True,
        'commands': commands
    })

@app.route('/commands', methods=['POST'])
def add_command_api():
    """新增指令"""
    try:
        data = request.get_json()
        command_text = data.get('command', '').strip()
        required_gpu = data.get('required_gpu', '').strip()
        
        if not command_text:
            return jsonify({
                'success': False,
                'error': '指令內容不能為空'
            }), 400
        
        if not required_gpu:
            return jsonify({
                'success': False,
                'error': '所需GPU不能為空'
            }), 400
        
        new_command = add_command(command_text, required_gpu)
        
        if new_command:
            return jsonify({
                'success': True,
                'command': new_command,
                'message': '指令新增成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '指令新增失敗'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }), 500

@app.route('/commands/<command_uid>', methods=['DELETE'])
def delete_command_api(command_uid):
    """刪除指令"""
    try:
        success = delete_command(command_uid)
        
        if success:
            return jsonify({
                'success': True,
                'message': '指令刪除成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '指令不存在或刪除失敗'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }), 500

@app.route('/commands/<command_uid>/order', methods=['PUT'])
def update_command_order_api(command_uid):
    """更新指令順序"""
    try:
        data = request.get_json()
        new_order = data.get('new_order')
        
        if new_order is None or not isinstance(new_order, int) or new_order < 1:
            return jsonify({
                'success': False,
                'error': '新順序必須是大於0的整數'
            }), 400
        
        success = update_command_order(command_uid, new_order)
        
        if success:
            return jsonify({
                'success': True,
                'message': '指令順序更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '指令不存在或更新失敗'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'服務器錯誤: {str(e)}'
        }), 500

@app.route('/api/executions/<execution_dir>/command')
def api_execution_command(execution_dir):
    """API endpoint to get the content of command.sh"""
    try:
        command_file_path = os.path.join(EXECUTION_LOG_DIR, execution_dir, 'command.sh')

        if not os.path.isfile(command_file_path):
            return jsonify({'success': False, 'error': 'Command file not found'})

        with open(command_file_path, 'r', encoding='utf-8') as f:
            command_content = f.read()

        return command_content, 200, {'Content-Type': 'text/plain; charset=utf-8'}

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/executions/<execution_dir>/run', methods=['POST'])
def run_execution_with_error_handling(execution_dir):
    """Run the execution and handle errors gracefully"""
    try:
        execution_path = os.path.join(EXECUTION_LOG_DIR, execution_dir)
        command_file = os.path.join(execution_path, 'command.sh')

        if not os.path.isfile(command_file):
            return jsonify({'success': False, 'error': 'Command file not found'})

        # Run the command and capture output and errors
        result = subprocess.run(
            ['/bin/bash', command_file],
            cwd=execution_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Save the output and error logs
        with open(os.path.join(execution_path, 'output.log'), 'w', encoding='utf-8') as output_log:
            output_log.write(result.stdout)

        with open(os.path.join(execution_path, 'error.log'), 'w', encoding='utf-8') as error_log:
            error_log.write(result.stderr)

        # Check for errors in the command execution
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Command failed with return code {result.returncode}',
                'stderr': result.stderr
            })

        return jsonify({'success': True, 'message': 'Command executed successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# 重複的路由已移除，保留原有的路由定義

if __name__ == '__main__':
    logger.info("Starting GPU Monitor Application")
    logger.info(f"Commands file: {COMMANDS_FILE}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Task execution directory: {EXECUTION_LOG_DIR}")
    
    # 啟動監控線程
    gpu_thread = threading.Thread(target=parse_nvidia_smi, daemon=True)
    disk_thread = threading.Thread(target=parse_disk_usage, daemon=True)
    
    gpu_thread.start()
    disk_thread.start()
    
    logger.info("Monitoring threads started")
    logger.info("Auto task execution system enabled")
    logger.info("Starting Flask web server on 0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
