# 🚀 NVIDIA GPU Monitor & Task Manager

A comprehensive real-time GPU monitoring and task management web application built with Flask. Monitor your NVIDIA GPUs, system resources, and manage GPU task queues with an intuitive web interface featuring advanced execution tracking and history management.

## ✨ Features

### 🎯 Core Monitoring
- **Real-time GPU Monitoring**: Live monitoring of NVIDIA GPU usage, memory consumption, and temperature
- **Process Tracking**: View running processes on each GPU with detailed memory usage and process information
- **Disk Usage Monitoring**: Monitor system disk usage across all mounted filesystems with visual indicators
- **System Resource Tracking**: Comprehensive system resource monitoring with real-time updates

### 📋 Task Management
- **Task Queue Management**: Add, delete, and reorder GPU tasks with intelligent queue management
- **Auto Task Execution**: Automatically execute queued tasks when matching GPUs become available
- **Flexible GPU Assignment**: Support for specific GPU ID, "any available", or GPU type matching
- **Duplicate Prevention**: Advanced protection against duplicate task submissions
- **Keyboard Shortcuts**: Quick task submission with Ctrl+Enter

### 📊 Execution Tracking
- **Execution History**: Comprehensive tracking of all executed tasks with detailed logs and outputs
- **Detailed Execution Records**: Complete task metadata, timing information, and system context
- **Real-time Output Streaming**: Live output monitoring with auto-scroll functionality
- **Error Handling & Logging**: Comprehensive error tracking and failure analysis
- **Execution Statistics**: Task completion rates and performance metrics

### 🖥️ User Interface
- **Responsive Web Interface**: Modern, clean UI that works seamlessly on desktop and mobile
- **Real-time Updates**: Live data updates without page refresh
- **Interactive Task Management**: Intuitive controls for task manipulation
- **Advanced Filtering**: Search and filter execution history by command, GPU, and date
- **Status Indicators**: Clear visual feedback for task states and system status

## 🖥️ User Interface

The application provides a comprehensive dashboard with:

### Main Dashboard (`/`)
- **GPU Status Cards**: Real-time utilization, memory usage, temperature, and process information
- **System Resource Overview**: Disk usage visualization with progress bars and capacity indicators
- **Task Queue Panel**: Interactive task management with add, reorder, and delete capabilities
- **Real-time Process List**: Live view of GPU processes with PID, memory usage, and process details

### Task Execution History (`/executions`)
- **Paginated Execution List**: Browse through all task executions with filtering and search
- **Advanced Filtering**: Filter by command text, GPU assignment, and date ranges
- **Execution Statistics**: Total executions, completion rates, and aggregate metrics
- **Status Indicators**: Clear visual status badges (Completed, Running, Failed, Queued)

### Execution Detail Pages (`/execution/<id>`)
- **Comprehensive Task Information**: Status, Task UID, Directory, Required GPU, timing details
- **Real-time Output Streaming**: Live command output with intelligent auto-scroll
- **Execution Logs**: Complete command information, execution scripts, and error logs
- **Timing Analysis**: Created time, executed time, wait time, and total execution time

### Key Interface Features
- **Responsive Design**: Optimized for both desktop and mobile viewing
- **Real-time Updates**: Live data refresh without manual page reloads
- **Interactive Controls**: Drag-and-drop task reordering and intuitive button controls
- **Keyboard Shortcuts**: Ctrl+Enter for quick task submission
- **Visual Feedback**: Loading states, progress indicators, and status animations

## � Installation

### Prerequisites
- **NVIDIA GPU** with drivers installed
- **nvidia-smi** command available in system PATH
- **Python 3.11+**
- **pipenv** (recommended) or pip

### Method 1: Using Pipenv (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/jmyang0928/gpu-use.git
cd gpu-use
```

2. Install dependencies with pipenv:
```bash
pipenv install flask
```

3. Activate the virtual environment:
```bash
pipenv shell
```

### Method 2: Using pip

1. Clone the repository:
```bash
git clone https://github.com/jmyang0928/gpu-use.git
cd gpu-use
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install flask
```

## 🚀 Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. The application will automatically start monitoring your GPUs and system resources.

## 📁 Project Structure

```
gpu-use/
├── app.py                    # Main Flask application with API endpoints
├── templates/
│   ├── index.html           # Main dashboard interface
│   ├── executions.html      # Task execution history page
│   └── execution_detail.html # Individual execution detail page
├── task_executions/         # Task execution records (auto-generated)
│   └── YYYYMMDD_HHMMSS_task_<uuid>/  # Individual execution directories
│       ├── command.txt      # Complete task information and metadata
│       ├── execute.sh       # Generated execution script
│       ├── output.log       # Command execution output with headers
│       ├── status.json      # Task execution status and process info
│       ├── nohup.out       # Background process output
│       └── error.log       # Error log (if execution fails)
├── gpu_commands.json        # Stored task commands (auto-generated)
├── gpu_monitor.log         # Application logs (auto-generated)
├── Pipfile                 # Python dependencies configuration
├── .gitignore             # Git ignore rules
└── README.md              # This documentation
```

## ⚙️ Configuration

### Environment Variables

You can customize the application behavior using environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 5000)
- `DEBUG`: Enable debug mode (default: True)

### File Paths

The application uses these files for data persistence:
- `gpu_commands.json`: Stores task queue commands
- `gpu_monitor.log`: Application logs with UTF-8 encoding

## 🔧 API Endpoints

### System Monitoring
- `GET /gpu_data` - Returns current GPU status, utilization, and running processes
- `GET /disk_data` - Returns disk usage information across all filesystems
- `GET /logs` - Get recent application logs with filtering options

### Task Queue Management
- `GET /commands` - Get all queued commands with ordering
- `POST /commands` - Add a new command to the queue
- `DELETE /commands/<uid>` - Delete a command by UID
- `PUT /commands/<uid>/order` - Update command execution order by UID

### Execution History & Monitoring
- `GET /api/executions` - Get paginated task execution history
- `GET /api/executions/<dir>/info` - Get complete execution information
- `GET /api/executions/<dir>/command` - Get command file content
- `GET /executions/<dir>/output` - Get complete execution output
- `GET /executions/<dir>/status` - Get execution status and process info

### Task Execution
- `POST /execute_task` - Manually trigger task execution
- Background execution monitoring runs automatically every 10 seconds

## 📊 Advanced Features

### GPU Monitoring & Process Tracking
- **Real-time GPU Metrics**: Utilization percentage, memory usage (used/total), temperature monitoring
- **Process Identification**: GPU-specific process listing with PID, type, memory consumption
- **Process Details**: Process name, command path, and resource allocation
- **Live Updates**: Automatic refresh every 5 seconds for GPU data

### Intelligent Task Execution
- **Smart GPU Matching**: Flexible assignment to specific GPU ID, "any available", or by GPU type
- **Availability Monitoring**: Real-time GPU availability detection for automatic task scheduling
- **Non-blocking Execution**: Background task execution with comprehensive logging and monitoring
- **Automatic Queue Management**: Tasks are automatically removed after successful execution
- **Duplicate Prevention**: Advanced protection against duplicate task submissions with visual feedback

### Comprehensive Execution Tracking
- **UUID-based Identification**: Unique task identification system preventing conflicts
- **Timestamped Records**: Creates detailed execution directories with complete metadata
- **Execution Metadata**: Includes creation time, wait time, execution time, system info, and GPU details
- **Live Output Streaming**: Real-time command output with intelligent auto-scroll functionality
- **Error Analysis**: Detailed error logging and failure analysis for troubleshooting
- **Performance Metrics**: Execution duration tracking and completion statistics

### Data Management & Persistence
- **JSON Data Storage**: Commands and settings persisted in structured JSON format
- **Automatic Migration**: Seamless migration from legacy ID-based system to UUID system
- **Execution History**: Permanent record keeping with searchable and filterable history
- **Log Management**: Comprehensive logging with UTF-8 encoding and rotation
- **File Organization**: Structured directory layout for easy navigation and maintenance

### User Experience Enhancements
- **Keyboard Shortcuts**: Ctrl+Enter for quick task submission
- **Visual Status Indicators**: Color-coded status badges for quick task state identification
- **Interactive Elements**: Hover effects, loading states, and responsive button feedback
- **Search & Filtering**: Advanced filtering by command text, GPU assignment, and date ranges
- **Pagination**: Efficient handling of large execution histories with page navigation
- **Auto-scroll Intelligence**: Smart scrolling that respects user behavior and context

## 🔒 Security & Production Considerations

### Development vs Production

**Development Mode (Default)**
- Debug mode enabled for detailed error messages
- Accessible on all network interfaces (0.0.0.0)
- Detailed logging and error reporting
- No authentication required

**Production Recommendations**
```python
# Disable debug mode
app.run(host='127.0.0.1', port=5000, debug=False)

# Or use environment variables
import os
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', 5000))
```

### Security Measures to Consider

1. **Authentication**: Implement user authentication for production use
2. **Network Access**: Restrict access to trusted networks only
3. **Input Validation**: Commands are executed with system privileges
4. **File Permissions**: Ensure proper file system permissions
5. **Logging**: Consider log rotation and sensitive data filtering

### Environment Variables

```bash
# Production configuration
export DEBUG=false
export HOST=127.0.0.1
export PORT=8080
export FLASK_ENV=production
```

## 🐛 Troubleshooting

### Common Issues

1. **nvidia-smi not found**
   ```bash
   # Check if nvidia-smi is available
   nvidia-smi --version
   
   # If not found, ensure NVIDIA drivers are properly installed
   # Ubuntu/Debian: sudo apt install nvidia-driver-<version>
   # Add to PATH if necessary: export PATH=/usr/bin:$PATH
   ```

2. **Permission denied errors**
   ```bash
   # Check file permissions for project directory
   ls -la
   
   # Fix permissions if needed
   chmod 755 .
   chmod 644 *.json *.log
   ```

3. **Port already in use**
   ```bash
   # Check what's using port 5000
   lsof -ti:5000
   
   # Kill the process
   lsof -ti:5000 | xargs kill -9
   
   # Or change port in app.py
   ```

4. **Task execution failures**
   - Check GPU availability: `nvidia-smi`
   - Review error logs in `task_executions/<task_dir>/error.log`
   - Verify command syntax and permissions
   - Check disk space availability

5. **Web interface not loading**
   - Verify Flask is running: check console output
   - Check firewall settings
   - Try accessing via `http://127.0.0.1:5000` instead of localhost

### Debug Information

To enable detailed debugging:
```python
# In app.py, modify the run configuration
app.run(host='0.0.0.0', port=5000, debug=True)
```

### Log Analysis

Check logs for troubleshooting:
```bash
# View recent application logs
tail -f gpu_monitor.log

# Check specific task execution
cat task_executions/<task_dir>/output.log
cat task_executions/<task_dir>/error.log
```

## 📝 Logging & Monitoring

### Application Logs
- **File Output**: `gpu_monitor.log` with UTF-8 encoding and automatic rotation
- **Console Output**: Real-time logging to terminal/console
- **Log Levels**: INFO, DEBUG, ERROR, WARNING with appropriate filtering
- **Structured Logging**: Timestamped entries with detailed context information

### Log Categories
- **System Events**: Application startup, shutdown, and configuration changes
- **GPU Monitoring**: GPU status changes, availability detection, and performance metrics
- **Task Management**: Task creation, execution, completion, and error tracking
- **API Access**: HTTP request logging and response tracking
- **Error Handling**: Detailed error traces and exception information

### Execution Logs
Each task execution creates comprehensive logs:
- **command.txt**: Complete task metadata and system context
- **output.log**: Real-time command execution output with headers
- **error.log**: Detailed error information and stack traces
- **status.json**: Task status, process information, and timing data
- **nohup.out**: Background process output and system messages

### Monitoring Capabilities
- **Real-time Status**: Live task status monitoring with automatic updates
- **Performance Metrics**: Execution duration, success rates, and resource usage
- **Historical Analysis**: Complete execution history with searchable records
- **Error Tracking**: Comprehensive error analysis and failure pattern detection

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add some feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is open source. Please check the repository for license details.

## 🙏 Acknowledgments

- **Flask Web Framework**: Robust Python web framework for rapid development
- **NVIDIA System Management Interface**: `nvidia-smi` for comprehensive GPU monitoring
- **Modern Web Technologies**: HTML5, CSS3, and JavaScript for responsive user experience
- **UUID System**: Python's UUID library for unique task identification
- **Real-time Updates**: JavaScript-based live data streaming and auto-refresh capabilities

## 📋 Changelog

### Recent Improvements
- ✅ **Duplicate Task Prevention**: Advanced protection against duplicate submissions
- ✅ **Enhanced UI/UX**: Improved visual feedback and user interaction
- ✅ **Auto-scroll Intelligence**: Smart output scrolling with user behavior tracking
- ✅ **Execution Statistics**: Accurate completion tracking and performance metrics
- ✅ **Keyboard Shortcuts**: Ctrl+Enter for quick task submission
- ✅ **Error Handling**: Comprehensive error detection and user-friendly messages
- ✅ **Mobile Responsiveness**: Optimized interface for mobile and tablet devices

### Technical Enhancements
- ✅ **UUID Migration**: Automatic migration from legacy ID system
- ✅ **Status Color Coding**: Consistent visual status indicators
- ✅ **Real-time Output**: Live command output streaming with auto-scroll
- ✅ **Advanced Filtering**: Multi-criteria search and filtering capabilities
- ✅ **Execution Detail**: Comprehensive task information and timing analysis

---

**Note**: This application is designed for development, research, and monitoring purposes. For production environments, implement proper authentication, security measures, and consider using a production WSGI server like Gunicorn or uWSGI.
