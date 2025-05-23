# Planner Agent Guide

## Purpose
The Planner agent decomposes user requirements into small, logical, testable waypoints that can be executed independently by other agents (CodeGen and TestWriter).

## Input/Output Specifications

### Input Context
- `user_prompt`: String containing the project requirements
- `model`: Optional LLM model name to use

### Output Format
Returns a dictionary with:
- `success`: Boolean indicating planning success
- `waypoints`: List of Waypoint objects
- `tokens_used`: Number of tokens consumed
- `cost`: API call cost

### Waypoint Structure
Each waypoint contains:
- `id`: Unique identifier (e.g., "wp_001", "wp_002")
- `description`: Clear description of what needs to be done
- `agent_type`: Either "CodeGen" or "TestWriter" (validated)
- `dependencies`: Array of waypoint IDs this depends on
- `status`: Current status (initially "PENDING")

## Response Parsing

### JSON Extraction
The agent can handle LLM responses in multiple formats:

1. **Raw JSON**: Direct JSON array
2. **Markdown Code Blocks**: JSON wrapped in ```json ... ``` blocks
3. **Mixed Content**: JSON embedded within explanatory text

The parser automatically:
- Detects and extracts JSON from markdown code blocks
- Strips markdown formatting (```json and ```)
- Handles multi-line JSON content
- Falls back to raw content if no code blocks found

Example of handled response:
```
Here's the waypoint plan:

```json
[
  {
    "id": "wp_001",
    "description": "Create main application",
    "agent_type": "CodeGen",
    "dependencies": []
  }
]
```

This creates a foundational structure...

### Agent Type Validation
The agent validates that `agent_type` is one of:
- `"CodeGen"`: For code generation tasks
- `"TestWriter"`: For test writing tasks

Invalid agent types are logged as warnings and default to `"CodeGen"` to ensure waypoint execution continues.

## Best Practices

### 1. Waypoint Decomposition
- **Single Responsibility**: Each waypoint should do one clear thing
- **Testable Units**: Every waypoint must be independently testable
- **Logical Sequence**: Build dependencies naturally (core → features → tests)
- **Size Limit**: Keep waypoints small enough to complete in one iteration

### 2. Agent Type Selection
- Use `CodeGen` for:
  - Creating new Python modules
  - Implementing business logic
  - Setting up project structure
  - Adding features and functionality
  
- Use `TestWriter` for:
  - Writing unit tests for existing code
  - Creating integration tests
  - Adding test fixtures and utilities

### 3. Dependency Management
- Always create code before tests that depend on it
- Consider natural build order (models → services → controllers)
- Avoid circular dependencies between waypoints
- Test waypoints should depend on the code they're testing

### 4. Description Quality
Write clear, specific descriptions that include:
- **What** to implement (specific feature/component)
- **Where** to place it (file structure guidance)
- **Why** it's needed (context within the project)
- **Success criteria** (what defines completion)

## Common Patterns

### Basic Project Structure
```
wp_001: Create main application entry point and basic project structure
wp_002: Implement core data models and basic validation
wp_003: Add business logic and service layer
wp_004: Create API endpoints or user interface
wp_005: Write comprehensive unit tests for all components
```

### Feature Addition Pattern
```
wp_xxx: Add [FeatureName] data model with required fields
wp_yyy: Implement [FeatureName] business logic and validation
wp_zzz: Create [FeatureName] API endpoints/UI components
wp_aaa: Write unit tests for [FeatureName] functionality
```

### Database/Persistence Pattern
```
wp_xxx: Set up database connection and basic configuration
wp_yyy: Create database schema and migration scripts
wp_zzz: Implement data access layer and repository pattern
wp_aaa: Add database integration tests
```

## Inter-Agent Communication

### To CodeGen Agent
Provide waypoints with:
- Clear implementation requirements
- File structure guidance
- Specific functionality to implement
- Dependencies and integration points

### To TestWriter Agent  
Provide waypoints with:
- Clear indication of what code to test
- Test coverage expectations
- Specific test scenarios to include
- Integration testing requirements

## Quality Checklist

Before finalizing a plan, verify:
- [ ] Each waypoint has a unique, descriptive ID
- [ ] Dependencies form a valid directed acyclic graph (no cycles)
- [ ] CodeGen waypoints come before related TestWriter waypoints
- [ ] Descriptions are specific and actionable
- [ ] Total number of waypoints is reasonable (typically 3-15)
- [ ] Plan builds toward the user's stated requirements
- [ ] Each waypoint can be completed independently given its dependencies

## Error Handling

Common planning failures and solutions:
- **Too broad waypoints**: Break down into smaller, more specific tasks
- **Missing dependencies**: Ensure proper build order (data → logic → interface → tests)
- **Unclear descriptions**: Add specific implementation details and success criteria
- **Invalid JSON**: Ensure proper JSON formatting in LLM response
- **Circular dependencies**: Restructure waypoint order and dependencies 