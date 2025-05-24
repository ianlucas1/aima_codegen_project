# CodeGen Agent Guide

## Purpose
The CodeGen agent generates clean, PEP 8 compliant Python code based on waypoint requirements and project context, while identifying necessary dependencies.

## Input/Output Specifications

### Input Context
- `waypoint`: Waypoint object with task description and metadata
- `project_context`: Current project files and structure
- `revision_feedback`: Optional feedback from failed verification attempts
- `model`: LLM model name to use

### Output Format
Returns a dictionary with:
- `success`: Boolean indicating if code generation succeeded
- `code`: Dictionary mapping file paths to content (if successful)
- `dependencies`: List of required Python packages
- `tokens_used`: Number of tokens consumed
- `cost`: API call cost
- `error`: Error message if failed
- `raw_content`: Raw LLM response (if JSON parsing failed)

## Best Practices

### 1. Code Quality Standards
- **PEP 8 Compliance**: Follow Python style guidelines strictly
- **Type Hints**: Use Python 3.10+ type annotations
- **Documentation**: Include docstrings for all functions and classes
- **Error Handling**: Implement appropriate exception handling
- **Clean Architecture**: Separate concerns and maintain modularity

### 2. File Organization
- Place files in logical locations within `src/` directory
- Follow Python package structure conventions
- Use meaningful file and module names
- Create `__init__.py` files for package structure
- Organize related functionality into modules

### 3. Dependency Management
- Identify all required third-party packages
- Specify version constraints when needed (e.g., `pandas>=1.3.0`)
- Prefer standard library when possible
- Group dependencies logically (core, dev, testing)
- Avoid unnecessary or heavy dependencies

### 4. Context Integration
- Review existing project files before generating new code
- Maintain consistency with existing code style and patterns
- Respect existing interfaces and API contracts
- Import and use existing components appropriately
- Avoid code duplication across files

## Common Patterns

### Module Structure
```python
"""Module docstring describing purpose."""
import standard_library_imports
import third_party_imports
from local_imports import LocalClass

# Constants
CONSTANT_VALUE = "value"

# Main classes and functions
class MainClass:
    """Class docstring."""
    
    def __init__(self, param: str) -> None:
        """Initialize with parameter."""
        self.param = param
    
    def method(self) -> str:
        """Method docstring."""
        return self.param

# Helper functions
def helper_function(data: list) -> dict:
    """Helper function docstring."""
    return {}

if __name__ == "__main__":
    # Optional main execution block
    pass
```

### Error Handling Pattern
```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def robust_function(data: str) -> Optional[dict]:
    """Function with proper error handling."""
    try:
        # Main logic here
        result = process_data(data)
        return result
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in robust_function: {e}")
        raise
```

### Configuration Pattern
```python
from pathlib import Path
from typing import Dict, Any
import json

class Config:
    """Application configuration management."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
```

## Inter-Agent Communication

### From Planner Agent
Receives waypoints with:
- Clear task descriptions
- File placement guidance
- Integration requirements
- Success criteria

### To TestWriter Agent
Produces code that:
- Has clear, testable interfaces
- Includes proper error handling
- Follows consistent patterns
- Has adequate documentation for test writing

### With Revision Feedback
When receiving feedback:
- Analyze all error types (syntax, lint, test failures)
- Fix identified issues systematically
- Maintain existing functionality while fixing problems
- Ensure changes don't introduce new issues

## Quality Checklist

Before finalizing generated code:
- [ ] All files have proper Python syntax
- [ ] Code follows PEP 8 style guidelines
- [ ] Type hints are used appropriately
- [ ] Docstrings are present for all public functions/classes
- [ ] Error handling is implemented where needed
- [ ] Dependencies are correctly identified and listed
- [ ] File paths are appropriate for the project structure
- [ ] Code integrates well with existing project context
- [ ] No obvious security vulnerabilities
- [ ] Performance considerations are addressed

## Error Handling

### Common Issues and Solutions

**JSON Parsing Failures**
- Ensure response is valid JSON format
- Escape special characters in code strings
- Use proper quoting for all dictionary keys
- Handle multiline strings correctly

**Syntax Errors**
- Validate Python syntax before output
- Check indentation consistency
- Ensure proper import statements
- Verify function/class definitions

**Import Errors**
- Use correct import paths relative to project structure
- Import only what exists or will be created
- Handle circular imports appropriately
- Use absolute imports when possible

**Dependency Issues**
- Research actual package names (e.g., `beautifulsoup4` not `beautifulsoup`)
- Specify compatible versions for critical dependencies
- Consider Python version compatibility
- Group related dependencies logically

## Revision Strategies

When revisions are needed:
1. **Analyze Feedback**: Understand all reported issues
2. **Prioritize Fixes**: Address syntax errors first, then logic
3. **Maintain Scope**: Fix issues without changing working code
4. **Test Integration**: Ensure fixes work with existing code
5. **Document Changes**: Update docstrings if behavior changes 