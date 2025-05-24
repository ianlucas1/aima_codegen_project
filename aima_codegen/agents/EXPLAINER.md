# Explainer Agent Guide

## Purpose
The Explainer agent generates clear, educational explanations of Python code for developers and learners. It can provide both natural language explanations and structured documentation formats, while ensuring sensitive information is redacted.

## Input/Output Specifications

### Input Context
- `file_path`: Path to the file being explained
- `code_content`: The actual code to explain
- `target`: Optional specific function/class name to focus on
- `structured_format`: Boolean flag for structured output format
- `model`: LLM model name to use

### Output Format
Returns a dictionary with:
- `success`: Boolean indicating explanation success
- `explanation`: The generated explanation text
- `redacted_secrets`: Boolean indicating if secrets were redacted
- `tokens_used`: Number of tokens consumed
- `cost`: API call cost

## Security Features

### Secret Redaction
The agent automatically detects and redacts potential secrets before processing:

**Detected Patterns:**
- API keys: `api_key="REDACTED"`
- Passwords: `password="REDACTED"`
- Secrets: `secret="REDACTED"`
- Tokens: `token="REDACTED"`
- Base64 strings (40+ chars): `REDACTED_BASE64`
- Hex strings (32+ chars): `REDACTED_HEX`

**Example:**
```python
# Original code
api_key = "sk-1234567890abcdef"
password = "super_secret_123"

# Processed code
api_key = "REDACTED"
password = "REDACTED"
```

This ensures explanations never expose sensitive information.

## Output Formats

### Natural Language Format (Default)
Provides conversational explanations suitable for learning:
- Clear, accessible language
- Step-by-step breakdowns
- Beginner-friendly terminology
- Context-aware focus

### Structured Format
When `structured_format=True`, provides organized documentation:

```markdown
## Overview
[Brief summary of what the code does]

## Key Components
[List and explain main functions/classes]

## How It Works
[Step-by-step explanation of the logic]

## Important Details
[Any special considerations, edge cases, or notable patterns]

## Usage Example
[How to use this code]
```

## Best Practices

### 1. Explanation Structure
- **Overview First**: Start with high-level purpose and functionality
- **Logical Flow**: Follow the natural execution order
- **Component Breakdown**: Explain individual functions and classes
- **Integration Points**: Show how components work together
- **Examples**: Include concrete usage examples when helpful

### 2. Audience Considerations
- **Beginner Friendly**: Assume minimal Python knowledge
- **Clear Terminology**: Define technical terms when first used
- **Visual Metaphors**: Use analogies to explain complex concepts
- **Progressive Detail**: Start simple, then add complexity
- **Practical Context**: Explain why code choices were made

### 3. Technical Accuracy
- **Correct Terminology**: Use precise Python and programming terms
- **Execution Order**: Accurately describe program flow
- **Error Handling**: Explain exception handling and edge cases
- **Performance**: Mention efficiency considerations when relevant
- **Best Practices**: Highlight good coding patterns

### 4. Clarity Guidelines
- **Short Sentences**: Keep explanations concise and readable
- **Active Voice**: Use active voice for clearer communication
- **Logical Paragraphs**: Group related concepts together
- **Transition Words**: Use connectors to show relationships
- **Summary Sections**: Provide key takeaways

## Common Explanation Patterns

### Overall File Structure
```
The [filename] module is responsible for [high-level purpose]. 

It consists of:
- [Number] main classes that handle [functionality]
- [Number] utility functions for [specific tasks]
- Configuration and setup code for [initialization]

The module follows [architectural pattern] to achieve [goals].
```

### Function Explanation Template
```
The [function_name] function [primary purpose]. 

Parameters:
- [param_name] ([type]): [description and purpose]
- [param_name] ([type], optional): [description and default behavior]

The function works by:
1. [First major step and why]
2. [Second major step and why]
3. [Final step and outcome]

It returns [return_type] representing [meaning of return value].

Example usage: [practical example]
```

### Class Explanation Framework
```
The [ClassName] class represents [conceptual model]. It's designed to [primary responsibility].

Key attributes:
- [attribute]: [purpose and data it holds]
- [attribute]: [purpose and data it holds]

Main methods:
- [method_name](): [what it does and when to use it]
- [method_name](): [what it does and when to use it]

The class follows [design pattern] to [achieve specific goal].
```

### Error Handling Explanation
```
The code includes error handling for [types of potential issues]:

- [ExceptionType]: Occurs when [conditions], handled by [response]
- [ExceptionType]: Triggered by [scenarios], resolved through [actions]

This defensive programming ensures [benefits and reliability aspects].
```

## Explanation Examples

### Simple Function Explanation
```python
def calculate_area(length: float, width: float) -> float:
    """Calculate the area of a rectangle."""
    if length <= 0 or width <= 0:
        raise ValueError("Length and width must be positive")
    return length * width
```

**Explanation:**
"The `calculate_area` function computes the area of a rectangle by multiplying its length and width. 

It takes two parameters:
- `length` (float): The length of the rectangle in any unit of measurement
- `width` (float): The width of the rectangle in the same unit

Before performing the calculation, the function validates that both measurements are positive numbers. If either value is zero or negative, it raises a `ValueError` with a helpful message, preventing mathematical errors and ensuring the result makes sense.

The function returns a float representing the area in square units. For example, if you call `calculate_area(5.0, 3.0)`, it returns `15.0` square units."

### Class Explanation Example
```python
class BankAccount:
    def __init__(self, account_number: str, initial_balance: float = 0.0):
        self.account_number = account_number
        self.balance = initial_balance
        self.transaction_history = []
    
    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        self.transaction_history.append(f"Deposited ${amount:.2f}")
```

**Explanation:**
"The `BankAccount` class models a simple bank account with basic deposit functionality.

When you create a new account using `BankAccount('12345', 100.0)`, the constructor (`__init__`) sets up three key pieces of information:
- `account_number`: A unique identifier for the account (stored as text)
- `balance`: The current amount of money in the account (starts at the initial balance or $0.00)
- `transaction_history`: An empty list that will track all deposits and withdrawals

The `deposit` method allows you to add money to the account. It first checks that you're trying to deposit a positive amount - you can't deposit zero or negative money! If the amount is valid, it adds the money to your balance and records the transaction in the history list.

This design ensures account integrity by preventing invalid operations while maintaining a clear record of all account activity."

## Inter-Agent Communication

### From CLI Interface
Receives requests for:
- File-level code explanations
- Function-specific explanations
- Class-specific explanations
- Code concept clarification

### To End Users
Provides:
- Educational explanations for learning
- Code documentation for teams
- Onboarding materials for new developers
- Technical communication for stakeholders

### Integration with Development Workflow
- Supports code review processes
- Enhances documentation efforts
- Facilitates knowledge transfer
- Aids in debugging and troubleshooting

## Quality Checklist

Before finalizing explanations:
- [ ] Explanation is technically accurate
- [ ] Language is appropriate for the target audience
- [ ] Code execution flow is clearly described
- [ ] Key concepts are properly defined
- [ ] Examples are relevant and helpful
- [ ] Structure is logical and easy to follow
- [ ] All major components are covered
- [ ] Benefits and purposes are explained
- [ ] Error cases and edge conditions are addressed
- [ ] Overall explanation is comprehensive but not overwhelming

## Specialized Explanation Types

### Algorithm Explanations
```
The [algorithm_name] algorithm solves [problem] by [approach].

Step-by-step process:
1. [Initial setup and data preparation]
2. [Main processing loop with logic]
3. [Result compilation and return]

Time complexity: [Big O notation] because [reasoning]
Space complexity: [Big O notation] because [reasoning]

This approach is chosen because [advantages over alternatives].
```

### Design Pattern Explanations
```
This code implements the [Pattern Name] design pattern, which [pattern purpose].

Key components:
- [Component]: [role in pattern]
- [Component]: [role in pattern]

The pattern helps with [benefits] and makes the code [qualities].

Real-world analogy: [relatable comparison]
```

### API Integration Explanations
```
This module handles communication with [external service/API].

The integration works by:
1. [Authentication/setup process]
2. [Request formatting and sending]
3. [Response handling and error management]
4. [Data transformation and return]

Error handling covers [scenarios] to ensure [reliability aspects].
```

## Common Pitfalls to Avoid

### Technical Pitfalls
- **Inaccurate execution order**: Misrepresenting how code actually runs
- **Incorrect terminology**: Using wrong technical terms
- **Missing edge cases**: Not explaining error conditions
- **Oversimplification**: Losing important technical details
- **Exposing secrets**: Avoid revealing any sensitive credentials or keys present in the code beyond what is necessary for understanding

### Communication Pitfalls
- **Too technical**: Using jargon without explanation
- **Too vague**: Providing unhelpful generalities
- **Poor organization**: Jumping between concepts randomly
- **Missing context**: Not explaining why code exists

### Audience Pitfalls
- **Wrong level**: Explaining too simply or too complexly
- **Missing motivation**: Not explaining the "why" behind code
- **No examples**: Failing to provide concrete usage cases
- **Intimidating language**: Using unnecessarily complex explanations

## Continuous Improvement

### Learning from Feedback
- Incorporate user questions to improve explanations
- Identify commonly misunderstood concepts
- Refine explanation templates based on effectiveness
- Adapt to different learning styles and preferences

### Domain-Specific Adaptations
- Develop specialized explanations for different fields (web, data science, etc.)
- Create context-aware explanations based on project type
- Adjust technical depth based on codebase complexity
- Provide industry-specific analogies and examples 