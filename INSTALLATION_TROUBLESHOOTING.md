# Installation Troubleshooting Guide

This guide helps resolve common installation issues with the LAN Video Calling Application.

## Common Issues and Solutions

### 1. Python 3.12 Compatibility Issues

**Problem**: `ModuleNotFoundError: No module named 'distutils'`

**Solution**: The `distutils` module was removed in Python 3.12. Use compatible package versions:

```bash
# Use the updated requirements.txt with compatible versions
pip install -r requirements.txt

# Or install manually with compatible versions
pip install "opencv-python>=4.8.0" "numpy>=1.26.0" "Pillow>=10.0.0" "pyaudio>=0.2.11"
```

### 2. PyAudio Installation Issues

**Problem**: PyAudio fails to install with compilation errors

**Solution**: Install system dependencies first:

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev
pip install pyaudio
```

#### CentOS/RHEL/Fedora:
```bash
sudo yum install python3-pyaudio portaudio-devel
# or for newer versions:
sudo dnf install python3-pyaudio portaudio-devel
pip install pyaudio
```

#### macOS:
```bash
brew install portaudio
pip install pyaudio
```

#### Windows:
```bash
# Usually works directly
pip install pyaudio

# If it fails, try:
pip install pipwin
pipwin install pyaudio
```

### 3. OpenCV Installation Issues

**Problem**: OpenCV fails to install or import

**Solution**: Try alternative installation methods:

```bash
# Method 1: Standard installation
pip install opencv-python

# Method 2: Headless version (no GUI support)
pip install opencv-python-headless

# Method 3: With contrib modules
pip install opencv-contrib-python

# Method 4: Specific version
pip install opencv-python==4.8.1.78
```

### 4. NumPy Installation Issues

**Problem**: NumPy compilation errors or version conflicts

**Solution**: Use pre-compiled wheels:

```bash
# Upgrade pip first
pip install --upgrade pip

# Install numpy with specific version
pip install "numpy>=1.26.0"

# If compilation fails, try:
pip install --only-binary=all numpy
```

### 5. Pillow Installation Issues

**Problem**: Pillow fails to install

**Solution**: Install system dependencies:

#### Ubuntu/Debian:
```bash
sudo apt-get install libjpeg-dev zlib1g-dev libpng-dev
pip install Pillow
```

#### CentOS/RHEL:
```bash
sudo yum install libjpeg-devel zlib-devel libpng-devel
pip install Pillow
```

#### macOS:
```bash
brew install libjpeg zlib libpng
pip install Pillow
```

### 6. Virtual Environment Issues

**Problem**: Packages installed in wrong environment

**Solution**: Ensure you're in the correct virtual environment:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Verify you're in the right environment
which python  # Should show path to venv
pip list      # Should show installed packages
```

### 7. Permission Issues

**Problem**: Permission denied errors during installation

**Solution**: Use user installation or fix permissions:

```bash
# Install for current user only
pip install --user -r requirements.txt

# Or fix permissions (Linux/macOS)
sudo chown -R $USER:$USER venv/
```

### 8. Network/Proxy Issues

**Problem**: Cannot download packages due to network restrictions

**Solution**: Configure pip for your network:

```bash
# Use different index
pip install -i https://pypi.org/simple/ -r requirements.txt

# Configure proxy (if needed)
pip install --proxy http://proxy.company.com:8080 -r requirements.txt

# Use trusted hosts
pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt
```

## Alternative Installation Methods

### Method 1: Minimal Installation

If you're having trouble with the full installation, try the minimal version:

```bash
pip install -r requirements-minimal.txt
```

This installs only the essential packages and skips PyAudio if it fails.

### Method 2: Manual Installation

Install packages one by one to identify problematic ones:

```bash
pip install numpy
pip install Pillow
pip install opencv-python
pip install pyaudio  # Optional
```

### Method 3: Conda Installation

If pip continues to fail, try using conda:

```bash
# Install conda first, then:
conda install numpy pillow opencv pyaudio
```

### Method 4: Docker Installation

Use Docker to avoid dependency issues:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "run_server.py"]
```

## Testing Installation

After installation, test that everything works:

```bash
# Test imports
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import numpy; print('NumPy:', numpy.__version__)"
python3 -c "import PIL; print('Pillow:', PIL.__version__)"
python3 -c "import pyaudio; print('PyAudio: OK')"

# Test application
python3 run_server.py --help
python3 run_client.py --help
```

## Getting Help

If you're still having issues:

1. **Check Python Version**: Ensure you're using Python 3.8 or higher
2. **Update pip**: `pip install --upgrade pip`
3. **Clear pip cache**: `pip cache purge`
4. **Check system dependencies**: Install required system packages
5. **Try different Python version**: Use Python 3.11 if 3.12 has issues
6. **Check error logs**: Look for specific error messages
7. **Search online**: Many installation issues have known solutions
8. **Open an issue**: Create a GitHub issue with your specific error

## Platform-Specific Notes

### Linux
- Most issues are related to missing system dependencies
- Use your package manager to install development headers
- Consider using virtual environments to avoid conflicts

### macOS
- Use Homebrew for system dependencies
- May need to install Xcode command line tools
- Some packages may require Rosetta on Apple Silicon

### Windows
- Usually the easiest platform for Python packages
- Use pre-compiled wheels when possible
- Consider using Windows Subsystem for Linux (WSL) if needed

## Performance Tips

After successful installation:

1. **Test with minimal setup first**
2. **Check camera/microphone permissions**
3. **Test network connectivity**
4. **Start with GUI versions for easier debugging**
5. **Check firewall settings**

Remember: The application is designed to work even with missing optional dependencies, so you can start with basic functionality and add features as you resolve installation issues.
