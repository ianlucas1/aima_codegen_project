# TestWriter Agent Guide

## Purpose
The TestWriter agent generates comprehensive pytest unit tests for Python code. It ensures complete test coverage, handles edge cases, and follows pytest best practices.

## Input/Output Specifications

### Input Context
- `waypoint`: The waypoint object containing test requirements
- `source_code`: The code to be tested
- `project_context`: Overall project information
- `revision_feedback`: Optional feedback from failed test runs
- `model`: LLM model name to use

### Output Format
Returns a dictionary with:
- `success`: Boolean indicating test generation success
- `code`: Dictionary mapping test file paths to content
- `dependencies`: List of required packages (always includes "pytest")
- `tokens_used`: Number of tokens consumed
- `cost`: API call cost

## Response Parsing

### Markdown Stripping
The agent automatically handles LLM responses wrapped in markdown code blocks:

1. **Detection**: Checks if response starts with ` ```json`
2. **Extraction**: Removes opening ` ```json` and closing ` ``` ` markers
3. **Parsing**: Processes clean JSON content

This ensures compatibility with LLMs that format responses as markdown.

Example handled response:
```
```json
{
  "code": {
    "tests/test_main.py": "import pytest\n..."
  },
  "dependencies": ["pytest", "pytest-cov"]
}
```

### Dependency Validation
The agent ensures pytest is always included in dependencies:
- Checks if "pytest" exists in the dependencies list
- Automatically adds "pytest" if missing
- Logs when pytest is added
- Ensures tests can always be executed

## Test Generation Guidelines

### 1. Test Structure and Organization
- **File Naming**: Use `test_` prefix for all test files
- **Test Discovery**: Place tests in `src/tests/` directory
- **Module Mapping**: Mirror source structure in test directory
- **Class Organization**: Group related tests in test classes
- **Descriptive Names**: Use clear, descriptive test function names

### 2. Test Coverage Principles
- **Function Coverage**: Test all public functions and methods
- **Edge Cases**: Include boundary conditions and edge cases
- **Error Conditions**: Test exception handling and error paths
- **Integration Points**: Test interactions between components
- **Data Validation**: Test input validation and data processing

### 3. Pytest Best Practices
- **Fixtures**: Use fixtures for test data and setup
- **Parametrization**: Use `@pytest.mark.parametrize` for multiple test cases
- **Assertions**: Use clear, specific assertions
- **Mocking**: Mock external dependencies appropriately
- **Cleanup**: Ensure proper test isolation and cleanup

### 4. Test Quality Standards
- **Independence**: Tests should not depend on each other
- **Repeatability**: Tests should produce consistent results
- **Speed**: Keep tests fast and focused
- **Clarity**: Tests should be easy to read and understand
- **Maintainability**: Tests should be easy to update

## Common Patterns

### Basic Test Structure
```python
"""Tests for the main application module."""
import pytest
from unittest.mock import Mock, patch
from src.app import MyClass, my_function

class TestMyClass:
    """Test cases for MyClass."""
    
    def test_init_success(self):
        """Test successful initialization of MyClass."""
        obj = MyClass("test_param")
        assert obj.param == "test_param"
    
    def test_init_invalid_param(self):
        """Test initialization with invalid parameter."""
        with pytest.raises(ValueError, match="Invalid parameter"):
            MyClass("")
    
    def test_method_normal_case(self):
        """Test method with normal input."""
        obj = MyClass("test")
        result = obj.method()
        assert result == "processed_test"

def test_my_function_success():
    """Test my_function with valid input."""
    result = my_function({"key": "value"})
    assert result["status"] == "success"

def test_my_function_empty_input():
    """Test my_function with empty input."""
    result = my_function({})
    assert result["status"] == "error"
```

### Parametrized Tests
```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
    ("123", "123"),
])
def test_uppercase_function(input_value, expected):
    """Test uppercase function with various inputs."""
    result = uppercase_function(input_value)
    assert result == expected
```

### Fixture Usage
```python
import pytest
from src.database import Database

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }

@pytest.fixture
def mock_database():
    """Provide a mock database for testing."""
    with patch('src.database.Database') as mock_db:
        mock_db.return_value.query.return_value = []
        yield mock_db

def test_user_service(sample_data, mock_database):
    """Test user service with mocked database."""
    service = UserService(mock_database)
    result = service.get_users()
    mock_database.query.assert_called_once()
```

### Exception Testing
```python
import pytest
from src.validators import validate_email

def test_validate_email_success():
    """Test email validation with valid email."""
    result = validate_email("user@example.com")
    assert result is True

def test_validate_email_invalid_format():
    """Test email validation with invalid format."""
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("invalid-email")

def test_validate_email_none_input():
    """Test email validation with None input."""
    with pytest.raises(TypeError, match="Email cannot be None"):
        validate_email(None)
```

## Inter-Agent Communication

### From CodeGen Agent
Receives code that needs:
- Comprehensive test coverage
- Error condition testing
- Integration testing
- Performance validation

### From Planner Agent
Receives waypoints specifying:
- What code components to test
- Required test coverage level
- Specific test scenarios
- Integration test requirements

### Revision Feedback Integration
When tests fail:
- Analyze pytest output for specific failures
- Fix test logic and assertions
- Update test data and expectations
- Ensure tests match actual code behavior

## Quality Checklist

Before finalizing tests:
- [ ] All public functions and methods are tested
- [ ] Edge cases and boundary conditions are covered
- [ ] Error conditions and exceptions are tested
- [ ] Tests are independent and isolated
- [ ] Test names are descriptive and clear
- [ ] Appropriate fixtures and mocking are used
- [ ] Tests follow pytest conventions
- [ ] Dependencies include pytest and other required packages
- [ ] Tests can run successfully in isolation
- [ ] Test coverage is comprehensive but not excessive

## Common Testing Scenarios

### API/Service Testing
```python
import pytest
from unittest.mock import patch
from src.api_client import APIClient

class TestAPIClient:
    """Tests for API client functionality."""
    
    @patch('src.api_client.requests.get')
    def test_get_data_success(self, mock_get):
        """Test successful API data retrieval."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "test"}
        
        client = APIClient("http://api.example.com")
        result = client.get_data("/endpoint")
        
        assert result == {"data": "test"}
        mock_get.assert_called_once_with("http://api.example.com/endpoint")
    
    @patch('src.api_client.requests.get')
    def test_get_data_network_error(self, mock_get):
        """Test API call with network error."""
        mock_get.side_effect = ConnectionError("Network error")
        
        client = APIClient("http://api.example.com")
        with pytest.raises(ConnectionError):
            client.get_data("/endpoint")
```

### Data Processing Testing
```python
import pytest
from src.processors import DataProcessor

class TestDataProcessor:
    """Tests for data processing functionality."""
    
    def test_process_valid_data(self):
        """Test processing with valid input data."""
        processor = DataProcessor()
        data = [{"id": 1, "value": 10}, {"id": 2, "value": 20}]
        result = processor.process(data)
        
        assert len(result) == 2
        assert result[0]["processed_value"] == 100  # Assuming 10x multiplier
    
    def test_process_empty_data(self):
        """Test processing with empty input."""
        processor = DataProcessor()
        result = processor.process([])
        assert result == []
    
    def test_process_invalid_data_format(self):
        """Test processing with invalid data format."""
        processor = DataProcessor()
        with pytest.raises(ValueError, match="Invalid data format"):
            processor.process("invalid_data")
```

## Error Handling

### Common Test Issues and Solutions

**Test Failures**
- Verify test logic matches actual code behavior
- Check test data validity and completeness
- Ensure proper mocking of external dependencies
- Validate assertion conditions and expected values

**Import Errors**
- Use correct import paths for source modules
- Ensure test files are in proper package structure
- Add necessary `__init__.py` files
- Handle relative vs absolute imports appropriately

**Fixture Issues**
- Define fixtures in appropriate scope (function, class, module)
- Ensure fixture dependencies are correct
- Use proper fixture cleanup for resources
- Avoid fixture conflicts and naming issues

**Assertion Problems**
- Use appropriate assertion methods for data types
- Include helpful error messages in assertions
- Test actual behavior, not implementation details
- Avoid overly specific or brittle assertions

## Dependencies

Always include in test dependencies:
- `pytest`: Core testing framework
- `pytest-cov`: Coverage reporting (if needed)
- `pytest-mock`: Enhanced mocking capabilities
- Any packages required by the code being tested
- Mock/testing versions of external services 