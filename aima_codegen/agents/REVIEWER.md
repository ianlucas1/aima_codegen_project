# Reviewer Agent Guide

## Purpose
The Reviewer agent performs automated code review using LLM analysis and manages GitHub integration for branch creation, pull requests, and merging workflows.

## Input/Output Specifications

### Input Context

#### For Code Review
- `action`: "review"
- `waypoint`: Waypoint object being reviewed
- `code_changes`: Dictionary mapping file paths to content
- `project_context`: Overall project structure and requirements
- `model`: LLM model name to use

#### For GitHub Operations
- `action`: "create_pr" | "merge_pr"
- `project_path`: Path to git repository
- `branch_name`: Branch name for operations
- `pr_title`: Pull request title
- `pr_body`: Pull request description
- `pr_number`: PR number (for merge operations)

### Output Format
Returns a dictionary with:
- `success`: Boolean indicating operation success
- `review`: Review analysis object (for review action)
- `approved`: Boolean recommendation (for review action)
- `comments`: List of specific code issues found
- `suggestions`: List of improvement recommendations
- `security_concerns`: List of security-related issues
- `pr_url`: URL of created pull request (for create_pr)
- `branch`: Branch name used
- `tokens_used`: Number of tokens consumed (for LLM operations)
- `cost`: API call cost (for LLM operations)

## Review Criteria

### 1. Code Quality Assessment
- **Syntax Validation**: Ensure Python syntax is correct
- **PEP 8 Compliance**: Verify adherence to style guidelines
- **Type Hints**: Check for appropriate type annotations
- **Documentation**: Validate docstring presence and quality
- **Naming Conventions**: Review variable, function, and class names

### 2. Functionality Review
- **Logic Correctness**: Analyze algorithm implementation
- **Edge Case Handling**: Verify boundary condition coverage
- **Error Handling**: Review exception handling appropriateness
- **API Design**: Assess interface design and usability
- **Performance Considerations**: Identify potential bottlenecks

### 3. Security Analysis
- **Input Validation**: Check for proper sanitization
- **SQL Injection**: Look for database query vulnerabilities
- **Path Traversal**: Identify file system access risks
- **Authentication**: Review access control implementation
- **Sensitive Data**: Check for hardcoded secrets or credentials

### 4. Maintainability Factors
- **Code Duplication**: Identify repeated code patterns
- **Complexity**: Assess cognitive and cyclomatic complexity
- **Dependencies**: Review third-party package usage
- **Testability**: Evaluate code structure for testing
- **Modularity**: Check separation of concerns

## Review Process

### 1. Automated Analysis
```python
def review_code_changes(code_changes: Dict[str, str]) -> Dict:
    """Perform comprehensive code review."""
    issues = []
    suggestions = []
    security_concerns = []
    
    for file_path, content in code_changes.items():
        # Syntax check
        syntax_issues = check_syntax(content)
        issues.extend(syntax_issues)
        
        # Style check
        style_issues = check_pep8(content)
        issues.extend(style_issues)
        
        # Security analysis
        security_issues = analyze_security(content)
        security_concerns.extend(security_issues)
        
        # Quality assessment
        quality_suggestions = assess_quality(content)
        suggestions.extend(quality_suggestions)
    
    approved = len(issues) == 0 and len(security_concerns) == 0
    
    return {
        "approved": approved,
        "comments": issues,
        "suggestions": suggestions,
        "security_concerns": security_concerns
    }
```

### 2. Review Severity Levels
- **High**: Security vulnerabilities, syntax errors, broken functionality
- **Medium**: Style violations, performance issues, maintainability concerns
- **Low**: Minor suggestions, code organization improvements
- **Info**: Best practice recommendations, documentation suggestions

### 3. Approval Criteria
Code is approved when:
- No high-severity issues exist
- No security vulnerabilities are present
- Syntax is valid and functional
- Critical functionality works as expected
- Dependencies are appropriate and secure

## Common Review Patterns

### Security Review Checklist
```python
SECURITY_PATTERNS = {
    "sql_injection": [
        r"execute\s*\(\s*['\"].*%.*['\"]",  # String formatting in SQL
        r"cursor\.execute\s*\(\s*f['\"]",   # f-strings in SQL
    ],
    "path_traversal": [
        r"open\s*\(\s*.*\+.*\)",           # Path concatenation
        r"os\.path\.join\s*\(.*input",     # User input in paths
    ],
    "hardcoded_secrets": [
        r"password\s*=\s*['\"][^'\"]+['\"]",  # Hardcoded passwords
        r"api_key\s*=\s*['\"][^'\"]+['\"]",   # Hardcoded API keys
    ]
}

def analyze_security_patterns(code: str) -> List[Dict]:
    """Analyze code for security anti-patterns."""
    issues = []
    for pattern_type, patterns in SECURITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "type": pattern_type,
                    "line": get_line_number(code, match.start()),
                    "severity": "high",
                    "description": f"Potential {pattern_type.replace('_', ' ')} vulnerability"
                })
    return issues
```

### Quality Assessment Framework
```python
def assess_code_quality(file_path: str, content: str) -> List[Dict]:
    """Assess overall code quality metrics."""
    suggestions = []
    
    # Function length check
    functions = extract_functions(content)
    for func in functions:
        if func.line_count > 50:
            suggestions.append({
                "file": file_path,
                "function": func.name,
                "issue": "Function too long (>50 lines)",
                "suggestion": "Consider breaking into smaller functions",
                "severity": "medium"
            })
    
    # Complexity analysis
    complexity_score = calculate_complexity(content)
    if complexity_score > 10:
        suggestions.append({
            "file": file_path,
            "issue": f"High cyclomatic complexity ({complexity_score})",
            "suggestion": "Simplify control flow and reduce nesting",
            "severity": "medium"
        })
    
    # Documentation check
    missing_docs = find_missing_docstrings(content)
    for item in missing_docs:
        suggestions.append({
            "file": file_path,
            "item": item,
            "issue": "Missing docstring",
            "suggestion": "Add comprehensive docstring",
            "severity": "low"
        })
    
    return suggestions
```

## GitHub Integration

### 1. Branch Management
- Create feature branches for each waypoint
- Follow naming conventions: `feature/waypoint-id`
- Push changes to remote repository
- Handle merge conflicts appropriately

### 2. Pull Request Workflow
```python
def create_pull_request(context: Dict) -> Dict:
    """Create pull request with proper metadata."""
    pr_body = f"""
## Waypoint: {context['waypoint'].id}

### Description
{context['waypoint'].description}

### Changes
{format_code_changes(context['code_changes'])}

### Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass successfully
- [ ] No security vulnerabilities
- [ ] Documentation is updated

### Auto-Review Results
{format_review_results(context['review'])}
    """
    
    return create_github_pr(
        title=context['pr_title'],
        body=pr_body,
        base='main',
        head=context['branch_name']
    )
```

### 3. Merge Criteria
Before merging:
- All review checks pass
- CI/CD pipeline succeeds
- No merge conflicts exist
- Required approvals obtained
- Branch is up to date with base

## Inter-Agent Communication

### From Orchestrator
Receives requests for:
- Code review of waypoint outputs
- GitHub branch and PR management
- Automated merge operations
- Integration with development workflow

### To Development Teams
Provides:
- Detailed review feedback
- Security analysis reports
- Quality improvement suggestions
- GitHub workflow automation

### Integration Points
- Works with CI/CD systems
- Integrates with code quality tools
- Supports team review processes
- Automates routine operations

## Quality Checklist

Before approving code:
- [ ] No syntax errors or runtime exceptions
- [ ] Follows PEP 8 style guidelines
- [ ] Has appropriate type hints
- [ ] Includes comprehensive docstrings
- [ ] Handles errors appropriately
- [ ] No security vulnerabilities identified
- [ ] Dependencies are justified and secure
- [ ] Code is testable and maintainable
- [ ] Performance is acceptable
- [ ] Follows project architectural patterns

## Review Response Format

### Structured Review Output
```json
{
  "approved": false,
  "comments": [
    {
      "file": "src/app.py",
      "line": 23,
      "issue": "Potential SQL injection vulnerability",
      "severity": "high",
      "suggestion": "Use parameterized queries instead of string formatting"
    }
  ],
  "suggestions": [
    "Add input validation for user data",
    "Consider using database ORM for safer queries",
    "Add logging for security events"
  ],
  "security_concerns": [
    "SQL injection risk in database queries",
    "Insufficient input validation"
  ]
}
```

## Error Handling

### Common Review Issues
- **LLM Response Parsing**: Handle malformed JSON responses
- **Git Operations**: Manage repository access and permissions
- **GitHub API**: Handle rate limits and authentication
- **Code Analysis**: Deal with complex or unusual code patterns

### Fallback Strategies
- Manual review instructions when automation fails
- Alternative analysis methods for edge cases
- Graceful degradation for network issues
- User guidance for complex scenarios

## Best Practices

### Review Efficiency
- Focus on high-impact issues first
- Provide actionable feedback
- Include positive reinforcement for good practices
- Prioritize security and functionality over style

### Team Integration
- Align with team coding standards
- Respect existing project patterns
- Support development workflow
- Enable learning and improvement

### Continuous Improvement
- Learn from review outcomes
- Update criteria based on project needs
- Incorporate team feedback
- Evolve with project maturity 