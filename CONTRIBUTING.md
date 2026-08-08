# Contributing to Thalor

Thank you for your interest in contributing to Thalor! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When filing an issue, include:**
- Clear descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Docker version, etc.)
- Logs or screenshots if applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:
- Use case description
- Proposed solution
- Alternative approaches considered
- Potential impact on existing users

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

### Prerequisites

- Docker Desktop
- Git
- Python 3.13+ (for local development)
- Node.js 20+ (for frontend development)

### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Thalor.git
cd Thalor

# Copy environment file
cp .env.example .env

# Start development stack
docker compose up -d

# Access dashboard
open http://localhost:9999
```

### Running Tests

```bash
# Run skill tests
docker exec thalor-agent bash -c "python3 -m pytest /opt/data/skills/*/tests/"

# Run integration tests
docker exec thalor-agent bash -c "python3 -m pytest /opt/data/tests/"
```

## Coding Standards

### Python

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Maximum line length: 100 characters
- Use f-strings for formatting

**Example:**
```python
def calculate_metric(value: float, weight: float = 1.0) -> float:
    """
    Calculate weighted metric.
    
    Args:
        value: Input value
        weight: Weight multiplier (default: 1.0)
    
    Returns:
        Weighted result
    """
    return value * weight
```

### JavaScript/TypeScript

- Use ES6+ features
- Prefer const over let
- Use async/await over callbacks
- Maximum line length: 100 characters

### YAML

- Use 2-space indentation
- Use block style for mappings
- Add comments for complex configurations

### Markdown

- Use ATX-style headers (# Header)
- Use fenced code blocks with language
- One sentence per line (for better diffs)

## Documentation

### Updating Documentation

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for structural changes
- Update docs/ for detailed guides
- Update CHANGELOG.md for all changes

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Test all code examples

## Creating Skills

### Skill Structure

```
skills/your-skill/
├── README.md          # User documentation
├── SKILL.md           # Deterministic criteria (if applicable)
├── your_skill.py      # Implementation
├── examples.md        # Usage examples
└── tests/
    └── test_skill.py  # Tests
```

### Skill Requirements

- Clear README with usage instructions
- Deterministic invocation criteria (if auto-triggered)
- Error handling and fallback
- Examples showing real usage
- Tests covering main scenarios

### Skill Best Practices

- Fail gracefully (never crash the agent)
- Provide clear error messages
- Log important events
- Respect rate limits
- Handle edge cases

## Testing

### Unit Tests

```python
def test_skill_criteria():
    """Test deterministic invocation criteria."""
    # Test repeated error loop
    assert should_invoke_expert(error_count=2, same_error=True)
    
    # Test broken dependency
    assert should_invoke_expert(dependency_broken=True)
```

### Integration Tests

```python
def test_expert_consultation():
    """Test full expert consultation flow."""
    # Setup
    agent = create_test_agent()
    
    # Trigger expert invocation
    result = agent.solve_problem("complex problem")
    
    # Verify
    assert "expert consulted" in result.logs
    assert result.solved
```

### Manual Testing

- Test on Windows, Linux, macOS
- Test with different LLM providers
- Test edge cases (network failures, timeouts)
- Test multi-agent scenarios

## Review Process

### Pull Request Review

1. Automated checks must pass
2. At least one maintainer approval required
3. All comments addressed
4. Documentation updated
5. CHANGELOG.md updated

### Review Criteria

- Code quality and readability
- Test coverage
- Documentation completeness
- Backward compatibility
- Security considerations

## Release Process

### Versioning

- **Major** (x.0.0): Breaking changes
- **Minor** (0.x.0): New features, backward compatible
- **Patch** (0.0.x): Bug fixes, backward compatible

### Release Checklist

- [ ] All PRs merged to main
- [ ] Tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in package files
- [ ] Git tag created
- [ ] GitHub release created
- [ ] Docker image built and pushed
- [ ] Announcement posted

## Getting Help

- Open an issue for bugs
- Use discussions for questions
- Join our Discord (if available)
- Email maintainers (for sensitive issues)

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to Thalor! 🚀
