from flask import Flask, render_template, jsonify, request
import subprocess
import threading
import time
import re
import json
import os
import logging
from datetime import datetime

app = Flask(__name__)
gpu_info = {}
processes = []
disk_info = []

# 數據文件路徑
COMMANDS_FILE = "gpu_commands.json"
LOG_FILE = "gpu_monitor.log"

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
                return json.load(f)
        else:
            return []
    except Exception as e:
        print(f"❌ Error loading commands: {e}")
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
    
    # 生成新的ID（基於現有命令數量）
    new_id = len(commands) + 1
    while any(cmd['id'] == new_id for cmd in commands):
        new_id += 1
    
    new_command = {
        'id': new_id,
        'command': command_text,
        'required_gpu': required_gpu,
        'created_at': datetime.now().isoformat(),
        'order': len(commands) + 1
    }
    
    commands.append(new_command)
    
    if save_commands(commands):
        logger.info(f"Command added: ID={new_id}, GPU={required_gpu}")
        return new_command
    else:
        logger.error(f"Failed to add command: ID={new_id}")
        return None

def get_commands():
    """讀取所有指令（按順序排列）"""
    commands = load_commands()
    # 按order字段排序
    return sorted(commands, key=lambda x: x.get('order', 0))

def delete_command(command_id):
    """刪除指定ID的指令"""
    commands = load_commands()
    original_count = len(commands)
    
    # 過濾掉要刪除的指令
    commands = [cmd for cmd in commands if cmd['id'] != command_id]
    
    if len(commands) < original_count:
        # 重新排序order字段
        for i, cmd in enumerate(commands):
            cmd['order'] = i + 1
        
        if save_commands(commands):
            logger.info(f"Command deleted: ID={command_id}")
            return True
        else:
            logger.error(f"Failed to delete command: ID={command_id}")
    
    return False

def update_command_order(command_id, new_order):
    """更新指令的順序"""
    commands = load_commands()
    
    # 找到要移動的指令
    target_cmd = None
    for cmd in commands:
        if cmd['id'] == command_id:
            target_cmd = cmd
            break
    
    if not target_cmd:
        logger.warning(f"Command not found for order update: ID={command_id}")
        return False
    
    # 移除目標指令
    commands = [cmd for cmd in commands if cmd['id'] != command_id]
    
    # 確保new_order在有效範圍內
    new_order = max(1, min(new_order, len(commands) + 1))
    
    # 在新位置插入指令
    commands.insert(new_order - 1, target_cmd)
    
    # 重新排序所有指令的order字段
    for i, cmd in enumerate(commands):
        cmd['order'] = i + 1
    
    success = save_commands(commands)
    if success:
        logger.info(f"Command order updated: ID={command_id}, new_order={new_order}")
    else:
        logger.error(f"Failed to update command order: ID={command_id}")
    
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

            output = """Sun Aug  3 15:39:03 2025
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 570.133.07             Driver Version: 570.133.07     CUDA Version: 12.8     |
|-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4070        Off | 00000000:01:00.0  Off  |                  N/A |
|  0%   35C    P8              8W / 200W  |    15MiB / 12282MiB    |     0%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   1  NVIDIA GeForce RTX 4090        Off | 00000000:02:00.0  Off  |                  N/A |
| 12%   45C    P2            110W / 450W  |  8124MiB / 24576MiB    |    56%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   2  NVIDIA GeForce RTX 4080        Off | 00000000:03:00.0  Off  |                  N/A |
| 20%   49C    P2            85W / 320W   |  4200MiB / 16384MiB    |    70%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   3  NVIDIA GeForce RTX 4070 Ti     Off | 00000000:04:00.0  Off  |                  N/A |
|  5%   40C    P3            60W / 285W   |  300MiB / 12282MiB     |    12%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   4  NVIDIA GeForce RTX 4060        Off | 00000000:05:00.0  Off  |                  N/A |
|  0%   33C    P8             6W / 115W   |    10MiB / 8192MiB     |     0%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   5  NVIDIA GeForce RTX 4070        Off | 00000000:06:00.0  Off  |                  N/A |
| 45%   60C    P1           180W / 200W   | 12000MiB / 12282MiB    |    95%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   6  NVIDIA GeForce RTX 3080        Off | 00000000:07:00.0  Off  |                  N/A |
| 18%   51C    P2           210W / 320W   | 10000MiB / 10240MiB    |    88%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+
|   7  NVIDIA GeForce RTX 3060        Off | 00000000:08:00.0  Off  |                  N/A |
|  2%   37C    P8             9W / 170W   |   200MiB / 12288MiB    |     2%      Default  |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            1059      G   /usr/lib/xorg/Xorg                        4MiB |
|    1   N/A  N/A           23450      C   python3                                4096MiB |
|    1   N/A  N/A           23451      C   /usr/bin/jupyter-notebook               4028MiB |
|    2   N/A  N/A           24500      C   /usr/bin/python3                        4200MiB |
|    3   N/A  N/A           24800      C   /opt/render/render_worker               300MiB |
|    5   N/A  N/A           25333      C   /home/jimmy/train_model.py            12000MiB |
|    6   N/A  N/A           26000      C   /home/jimmy/stable_diffusion.py        8000MiB |
|    6   N/A  N/A           26001      C   /usr/lib/python3.11/tensorflow         2000MiB |
|    7   N/A  N/A           26200      C   /usr/lib/firefox                         200MiB |
+-----------------------------------------------------------------------------------------+
"""

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

@app.route('/commands/<int:command_id>', methods=['DELETE'])
def delete_command_api(command_id):
    """刪除指令"""
    try:
        success = delete_command(command_id)
        
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

@app.route('/commands/<int:command_id>/order', methods=['PUT'])
def update_command_order_api(command_id):
    """更新指令順序"""
    try:
        data = request.get_json()
        new_order = data.get('new_order')
        
        if new_order is None or not isinstance(new_order, int) or new_order < 1:
            return jsonify({
                'success': False,
                'error': '新順序必須是大於0的整數'
            }), 400
        
        success = update_command_order(command_id, new_order)
        
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

if __name__ == '__main__':
    logger.info("Starting GPU Monitor Application")
    logger.info(f"Commands file: {COMMANDS_FILE}")
    logger.info(f"Log file: {LOG_FILE}")
    
    # 啟動監控線程
    gpu_thread = threading.Thread(target=parse_nvidia_smi, daemon=True)
    disk_thread = threading.Thread(target=parse_disk_usage, daemon=True)
    
    gpu_thread.start()
    disk_thread.start()
    
    logger.info("Monitoring threads started")
    logger.info("Starting Flask web server on 0.0.0.0:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
