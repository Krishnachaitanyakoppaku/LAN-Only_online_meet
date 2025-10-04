# Contributing to LAN Video Calling Application

Thank you for your interest in contributing to the LAN Video Calling Application! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic understanding of Python, networking, and GUI development

### Setting Up Development Environment

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/your-username/LAN-Video-Call.git
   cd LAN-Video-Call
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   python3 setup.py
   # or manually:
   pip install -r requirements.txt
   ```

4. **Test Installation**
   ```bash
   python3 run_server.py --help
   python3 run_client.py --help
   ```

## Development Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused
- Use type hints where appropriate

### Project Structure
```
LAN-Video-Call/
├── server/          # Server-side components
├── client/          # Client-side components
├── shared/          # Shared utilities and protocol
├── gui/             # GUI components
├── tests/           # Test files (to be added)
├── docs/            # Documentation (to be added)
└── examples/        # Example configurations (to be added)
```

### Testing
- Write unit tests for new features
- Test both server and client components
- Ensure cross-platform compatibility
- Test with different network conditions

### Documentation
- Update README.md for new features
- Add docstrings to all new functions
- Update USAGE.md for new user-facing features
- Include examples in documentation

## Submitting Changes

### Pull Request Process

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   # Test server
   python3 run_server.py --host 127.0.0.1 --port 8888
   
   # Test client (in another terminal)
   python3 run_client.py --host 127.0.0.1 --port 8888 --username TestUser
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: Brief description of your changes"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format
Use clear, descriptive commit messages:
- `Add: New feature description`
- `Fix: Bug description`
- `Update: Change description`
- `Remove: Removed feature description`
- `Docs: Documentation update`

## Areas for Contribution

### High Priority
- **Testing**: Add comprehensive test suite
- **Documentation**: Improve user guides and API documentation
- **Performance**: Optimize video/audio processing
- **Security**: Enhance authentication and encryption
- **Mobile Support**: Add mobile client support

### Medium Priority
- **UI/UX**: Improve GUI design and user experience
- **Platform Support**: Better cross-platform compatibility
- **Configuration**: Add configuration file support
- **Logging**: Enhanced logging and debugging features
- **Plugins**: Plugin system for extensibility

### Low Priority
- **Themes**: Customizable UI themes
- **Advanced Features**: Advanced video effects, filters
- **Integration**: Integration with other applications
- **Analytics**: Usage analytics and reporting

## Bug Reports

When reporting bugs, please include:

1. **Environment Information**
   - Operating System and version
   - Python version
   - Dependencies versions

2. **Steps to Reproduce**
   - Clear, numbered steps
   - Expected vs actual behavior
   - Screenshots if applicable

3. **Error Information**
   - Full error messages
   - Log files
   - Stack traces

## Feature Requests

When requesting features, please include:

1. **Use Case**
   - Why is this feature needed?
   - How would it be used?

2. **Proposed Solution**
   - How should it work?
   - Any design considerations?

3. **Alternatives**
   - Other ways to solve the problem?

## Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors.

### Expected Behavior
- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards other community members

### Unacceptable Behavior
- Harassment, trolling, or inappropriate comments
- Personal attacks or political discussions
- Spam or off-topic discussions
- Any other unprofessional conduct

## Getting Help

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and general discussion
- **Documentation**: Check README.md and USAGE.md first

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the LAN Video Calling Application!
