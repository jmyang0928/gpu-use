# 🚀 NVIDIA GPU Monitor

A real-time GPU monitoring and task management web application built with Flask. Monitor your NVIDIA GPUs, system resources, and manage GPU task queues with an intuitive web interface.

## ✨ Features

- **Real-time GPU Monitoring**: Live monitoring of NVIDIA GPU usage, memory consumption, and temperature
- **Process Tracking**: View running processes on each GPU with detailed memory usage
- **Disk Usage Monitoring**: Monitor system disk usage across all mounted filesystems
- **Task Queue Management**: Add, delete, and reorder GPU tasks with a built-in command queue
- **Responsive Web Interface**: Clean, modern UI that works on desktop and mobile
- **Logging System**: Comprehensive logging with file output and console display
- **JSON Data Persistence**: Commands and settings are saved to JSON files

## 🖥️ Screenshots

The application provides:
- GPU status cards showing utilization, memory usage, and temperature
- Process list with PID, type, and memory consumption
- Disk usage visualization with progress bars
- Task queue management with drag-and-drop reordering
- Real-time log viewer

## 🛠️ Prerequisites

- **NVIDIA GPU** with drivers installed
- **nvidia-smi** command available in PATH
- **Python 3.11+**
- **pipenv** (recommended) or pip

## 📦 Installation

### Method 1: Using Pipenv (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
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
git clone <repository-url>
cd gpu-use
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
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
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Web interface template
├── gpu_commands.json     # Stored task commands (auto-generated)
├── gpu_monitor.log       # Application logs (auto-generated)
├── Pipfile              # Python dependencies
├── README.md            # This file
└── .gitignore          # Git ignore rules
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

### GPU Data
- `GET /gpu_data` - Returns current GPU status and processes
- `GET /disk_data` - Returns disk usage information

### Task Management
- `GET /commands` - Get all queued commands
- `POST /commands` - Add a new command
- `DELETE /commands/<id>` - Delete a command
- `PUT /commands/<id>/order` - Update command order

### Logs
- `GET /logs` - Get recent application logs

## 📊 Monitoring Features

### GPU Information
- GPU utilization percentage
- Memory usage (used/total)
- Temperature monitoring
- Process identification
- Real-time updates every 5 seconds

### Disk Monitoring
- Filesystem usage across all mounted drives
- Size filtering (shows drives ≥1GB only)
- Usage percentage with visual indicators
- Updates every 10 seconds

### Process Tracking
- GPU-specific process listing
- Process ID (PID) and type identification
- Memory consumption per process
- Process name and command path

## 🔒 Security Considerations

- The application runs with debug mode enabled by default
- Consider disabling debug mode in production environments
- The web interface is accessible on all network interfaces (0.0.0.0)
- No authentication is implemented - consider adding security measures for production use

## 🐛 Troubleshooting

### Common Issues

1. **nvidia-smi not found**
   - Ensure NVIDIA drivers are properly installed
   - Verify `nvidia-smi` is available in your PATH

2. **Permission denied errors**
   - Check file permissions for log files
   - Ensure the application has write access to the project directory

3. **Port already in use**
   - Change the port in `app.py` or kill the process using port 5000
   - Use: `lsof -ti:5000 | xargs kill -9`

### Debug Mode

The application runs in debug mode by default. To disable it:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

## 📝 Logging

Logs are written to both:
- `gpu_monitor.log` file with UTF-8 encoding
- Console output

Log levels include:
- INFO: General application events
- DEBUG: Detailed monitoring information
- ERROR: Error conditions and exceptions
- WARNING: Warning messages

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

- Built with Flask web framework
- Uses NVIDIA System Management Interface (nvidia-smi)
- Modern CSS styling with responsive design
- Real-time data updates with JavaScript

---

**Note**: This application is designed for development and monitoring purposes. For production environments, consider implementing proper authentication, security measures, and error handling enhancements.
