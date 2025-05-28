# warifuri v0.1.0 Release Notes

🎉 **Initial Public Release** - 2025年5月28日

## 🚀 Overview

warifuri v0.1.0 marks the first public release of our production-ready CLI tool for intelligent task allocation between humans, AI, and machines. This release provides a comprehensive foundation for automated workflow management in GitHub repositories.

## ✨ Key Features

### 🎯 Core Functionality
- **Multi-Actor Task Execution**: Seamless coordination between machine, AI, and human tasks
- **Dependency Resolution**: Automatic execution order based on task dependencies
- **State Management**: File-based state tracking with `done.md` completion markers
- **Template System**: Reusable task patterns for common workflows

### 🤖 GitHub Integration
- **CI/CD Ready**: Complete GitHub Actions workflow integration
- **Auto-merge Support**: Conditional PR merging with validation checks
- **Security First**: Sandboxed execution with comprehensive logging

### 📊 Quality Metrics
- **246 Tests**: Comprehensive test suite with 77% code coverage
- **Type Safety**: Full MyPy compliance with strict mode
- **Security**: Bandit-scanned with zero high/medium vulnerabilities
- **Documentation**: 16-page Sphinx API documentation

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/f43a9a/warifuri.git

# Download from GitHub Releases
pip install warifuri-0.1.0-py3-none-any.whl
```

## 🛠️ What's Included

### Core Commands
- `warifuri init` - Project and task creation
- `warifuri run` - Task execution with dependency resolution
- `warifuri list` - Workspace status overview
- `warifuri validate` - Comprehensive workspace validation
- `warifuri graph` - Dependency visualization

### File Structure
- **Instruction-based**: YAML configuration for tasks and projects
- **Git-friendly**: All state stored in trackable files
- **Template-driven**: Reusable patterns across projects

### API Coverage
- **Core Modules**: Task management, dependency resolution, validation
- **CLI Interface**: Complete command-line functionality
- **GitHub Integration**: Actions, auto-merge, deployment workflows
- **Utilities**: Logging, configuration, schema validation

## 🔧 Technical Details

### Requirements
- **Python**: 3.11+ (tested on 3.11)
- **Dependencies**: PyYAML, Click, Pydantic, GitPython
- **Platform**: Cross-platform (Linux, macOS, Windows)

### Performance
- **Startup Time**: Sub-second CLI initialization
- **Memory Usage**: Minimal footprint (~50MB typical usage)
- **Concurrency**: Async-ready with proper resource management

## 🎯 Use Cases

### Development Workflows
- **Data Pipelines**: Extract, transform, validate workflows
- **CI/CD Automation**: Build, test, deploy sequences
- **Code Quality**: Linting, testing, security scanning

### Project Management
- **Task Tracking**: Dependency-aware task execution
- **Team Coordination**: Human, AI, machine task allocation
- **Progress Monitoring**: Real-time status and completion tracking

## 📚 Documentation

Complete documentation available at: https://f43a9a.github.io/warifuri/

- **User Guide**: Installation, quickstart, command reference
- **API Reference**: Full module documentation
- **Development**: Contributing guidelines and architecture

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details on:
- Development setup with Poetry
- Code style (Black, Ruff) and type checking (MyPy)
- Testing requirements and coverage expectations
- Pull request process

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

This project follows Python best practices and integrates seamlessly with the GitHub ecosystem. Special thanks to the open-source community for the excellent tools that make this possible.

---

**Next Release**: v0.2.0 planned for Q3 2025 with enhanced AI task capabilities and performance optimizations.
