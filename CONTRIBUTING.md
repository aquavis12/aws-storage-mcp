# Contributing to AWS Storage MCP Server

Thank you for your interest in contributing to the AWS Storage MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

1. A clear, descriptive title
2. A detailed description of the issue
3. Steps to reproduce the bug
4. Expected behavior
5. Actual behavior
6. Screenshots (if applicable)
7. Environment information (OS, Docker version, etc.)

### Suggesting Enhancements

We welcome suggestions for enhancements! Please create an issue with:

1. A clear, descriptive title
2. A detailed description of the proposed enhancement
3. Any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Clone the repository
2. Run `./setup.sh` to configure your environment
3. Start the server with `./start-docker.sh`
4. Make your changes
5. Test your changes

## Adding New AWS Services

To add support for a new AWS service:

1. Create a new file in `src/services/` (e.g., `new_service.py`)
2. Implement the service class extending `BaseService`
3. Add the service to `src/services/__init__.py`
4. Add appropriate actions in `src/server.py`
5. Update documentation

## Style Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Update documentation when adding new features

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
