# Multi-Model Configuration Guide

This guide explains how to configure and optimize different LLM models for each agent in AIMA CodeGen, enabling cost-effective and high-quality code generation.

## Table of Contents
- [Overview](#overview)
- [Why Multi-Model?](#why-multi-model)
- [Configuration Methods](#configuration-methods)
- [Model Selection Strategy](#model-selection-strategy)
- [Provider Comparison](#provider-comparison)
- [Cost Optimization](#cost-optimization)
- [Presets](#presets)
- [Advanced Configuration](#advanced-configuration)
- [Examples](#examples)
- [Best Practices](#best-practices)

## Overview

Multi-Model configuration allows you to:
- **Optimize Costs**: Use cheaper models for simple tasks
- **Maximize Quality**: Deploy premium models where it matters
- **Leverage Strengths**: Each provider excels at different tasks
- **Balance Performance**: Find the sweet spot between speed and quality

## Why Multi-Model?

### Traditional Single-Model Approach
```
All Agents → GPT-4 → High Cost, Consistent Quality
```

### Multi-Model Approach
```
Planner → Claude Opus 4 / O3 → Deep Reasoning
CodeGen → Gemini Flash → Large Context, Low Cost
TestWriter → Claude Sonnet 4 → Balanced Quality  
Reviewer → Claude Opus 4 → Excellent Bug Detection
```

### Benefits

1. **Cost Reduction**: Up to 70% savings on simple tasks
2. **Quality Improvement**: Specialized models for specific tasks
3. **Faster Development**: Parallel processing with different providers
4. **Risk Mitigation**: Not dependent on a single provider

## Configuration Methods

### 1. GUI Configuration

The easiest way to configure multi-model:

1. Launch GUI: `aima-codegen gui`
2. Select **Multi-Model** radio button
3. Configure each agent's dropdown:
   - Choose provider
   - Select model
   - Apply changes

### 2. Configuration File

Edit `~/.AIMA_CodeGen/multi_model_config.json`:

```json
{
  "Planner": {
    "provider": "Anthropic",
    "model": "claude-opus-4-20250514",
    "temperature": 0.5,
    "max_tokens": 3000
  },
  "CodeGen": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "temperature": 0.2,
    "max_tokens": 8000
  },
  "TestWriter": {
    "provider": "Anthropic",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.2,
    "max_tokens": 4000
  },
  "Reviewer": {
    "provider": "Anthropic",
    "model": "claude-opus-4-20250514",
    "temperature": 0.3,
    "max_tokens": 2000
  },
  "Explainer": {
    "provider": "Anthropic",
    "model": "claude-sonnet-4-20250514",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### 3. Programmatic Configuration

```python
from aima_codegen.multi_model import MultiModelManager, AgentModelConfig

# Initialize manager
manager = MultiModelManager()

# Configure specific agent
manager.set_agent_config(
    "CodeGen",
    AgentModelConfig(
        provider="OpenAI",
        model="gpt-4-turbo-preview",
        temperature=0.2,
        max_tokens=4000
    )
)

# Save configuration
manager.save_configurations()
```

### 4. CLI Configuration

```bash
# Enable multi-model
aima-codegen config --set General.use_multi_model --value true

# Set specific agent model
aima-codegen config --set MultiModel.CodeGen.model --value "gemini-2.5-flash-preview-05-20"
aima-codegen config --set MultiModel.CodeGen.provider --value "Google"
```

## Model Selection Strategy

### Agent-Specific Requirements

#### Planner Agent
**Primary Needs**: Deep reasoning, understanding complex requirements
- **Recommended Models**: 
  - claude-opus-4-20250514 (excellent reasoning)
  - o3-2025-04-16 (advanced reasoning)
- **Temperature**: 0.5-0.7 (balanced creativity)

#### CodeGen Agent
**Primary Needs**: Large context window, cost-effectiveness, decent quality
- **Recommended Models**:
  - gemini-2.5-flash-preview-05-20 (large context, very cost-effective)
  - claude-sonnet-4-20250514 (when higher quality needed)
- **Temperature**: 0.2 (more deterministic)

#### TestWriter Agent
**Primary Needs**: Comprehensive coverage, edge cases
- **Recommended Models**:
  - claude-sonnet-4-20250514 (thorough testing)
  - gemini-2.5-flash-preview-05-20 (cost-effective tests)
- **Temperature**: 0.2 (consistent tests)

#### Reviewer Agent
**Primary Needs**: Bug detection, security awareness
- **Recommended Models**:
  - claude-opus-4-20250514 (best at finding issues)
  - claude-sonnet-4-20250514 (cost-effective alternative)
- **Temperature**: 0.3 (balanced analysis)

#### Explainer Agent
**Primary Needs**: Clear communication, teaching ability
- **Recommended Models**:
  - claude-sonnet-4-20250514 (clear explanations)
  - gemini-2.5-pro-preview-05-06 (good summaries)
- **Temperature**: 0.7 (natural language)

## Provider Comparison

### OpenAI
**Strengths**:
- Advanced reasoning capabilities (o3)
- Wide model selection
- Good for experimentation

**Best For**:
- Planner Agent (o3 for complex reasoning)
- Experimental testing

**Models**:
- o3-2025-04-16: Advanced reasoning model
- gpt-4.1-2025-04-14: General purpose (experimental)
- o4-mini-2025-04-16: Cost-effective (experimental)

### Anthropic
**Strengths**:
- Superior reasoning and planning
- Excellent code review
- Strong at finding bugs
- Clear explanations

**Best For**:
- Planner Agent (Opus for deep reasoning)
- Reviewer Agent
- TestWriter Agent (Sonnet)

**Models**:
- claude-opus-4-20250514: Best reasoning, planning, and review
- claude-sonnet-4-20250514: Balanced for tests and review

### Google
**Strengths**:
- Very large context window
- Extremely cost-effective
- Fast processing
- Good code generation quality

**Best For**:
- CodeGen Agent (primary choice)
- TestWriter Agent (cost-effective option)
- Fast prototyping

**Models**:
- gemini-2.5-flash-preview-05-20: Very fast, large context, extremely cheap
- gemini-2.5-pro-preview-05-06: Higher capability when needed

## Cost Optimization

### Cost Comparison Table

| Model | Provider | Input $/1M | Output $/1M | Quality | Speed |
|-------|----------|------------|-------------|---------|-------|
| o4-mini-2025-04-16 | OpenAI | $1.10 | $4.40 | Very Good | Fast |
| gpt-4.1-2025-04-14 | OpenAI | $2.00 | $8.00 | Excellent | Fast |
| o3-2025-04-16 | OpenAI | $10.00 | $40.00 | Superior | Moderate |
| claude-sonnet-4-20250514 | Anthropic | $3.00 | $15.00 | Very Good | Fast |
| claude-opus-4-20250514 | Anthropic | $15.00 | $75.00 | Excellent | Moderate |
| gemini-2.5-flash-preview-05-20 | Google | $0.15 | $0.60 | Good | Very Fast |
| gemini-2.5-pro-preview-05-06 | Google | $1.25 | $10.00 | Very Good | Fast |

### Optimization Strategies

#### 1. Task-Based Selection
```python
# Simple tasks → Cheapest model
CodeGen: gemini-2.5-flash-preview-05-20 ($0.15/$0.60)

# Complex reasoning → Premium models  
Planner: claude-opus-4-20250514 ($15/$75)

# Balanced quality → Mid-tier
TestWriter: claude-sonnet-4-20250514 ($3/$15)
```

#### 2. Budget-Aware Configuration
```python
# Low Budget (<$2)
{
  "Planner": "gemini-2.5-flash-preview-05-20",
  "CodeGen": "gemini-2.5-flash-preview-05-20",
  "TestWriter": "gemini-2.5-flash-preview-05-20",
  "Reviewer": "gemini-2.5-flash-preview-05-20"
}

# Medium Budget ($2-$10)
{
  "Planner": "claude-sonnet-4-20250514",
  "CodeGen": "gemini-2.5-flash-preview-05-20",
  "TestWriter": "claude-sonnet-4-20250514",
  "Reviewer": "claude-sonnet-4-20250514"
}

# High Budget (>$10)
{
  "Planner": "claude-opus-4-20250514",
  "CodeGen": "claude-sonnet-4-20250514",
  "TestWriter": "claude-sonnet-4-20250514",
  "Reviewer": "claude-opus-4-20250514"
}
```

#### 3. Development Phase Optimization
```python
# Prototyping: Speed over quality
use_preset("fast")

# Production: Quality over cost
use_preset("quality")

# Normal development: Balanced
use_preset("balanced")
```

## Presets

### Fast Development Preset
**Goal**: Rapid prototyping, minimize costs
```json
{
  "Planner": {"model": "gemini-2.5-flash-preview-05-20", "provider": "Google"},
  "CodeGen": {"model": "gemini-2.5-flash-preview-05-20", "provider": "Google"},
  "TestWriter": {"model": "gemini-2.5-flash-preview-05-20", "provider": "Google"},
  "Reviewer": {"model": "gemini-2.5-flash-preview-05-20", "provider": "Google"}
}
```
**Cost**: ~$0.05-0.20 per waypoint
**Use Case**: Prototypes, experiments, learning

### High Quality Preset
**Goal**: Production-ready code, maximum quality
```json
{
  "Planner": {"model": "claude-opus-4-20250514", "provider": "Anthropic"},
  "CodeGen": {"model": "claude-sonnet-4-20250514", "provider": "Anthropic"},
  "TestWriter": {"model": "claude-sonnet-4-20250514", "provider": "Anthropic"},
  "Reviewer": {"model": "claude-opus-4-20250514", "provider": "Anthropic"}
}
```
**Cost**: ~$10-20 per waypoint
**Use Case**: Production code, critical systems

### Balanced Preset
**Goal**: Optimal quality/cost ratio
```json
{
  "Planner": {"model": "o3-2025-04-16", "provider": "OpenAI"},
  "CodeGen": {"model": "gemini-2.5-flash-preview-05-20", "provider": "Google"},
  "TestWriter": {"model": "claude-sonnet-4-20250514", "provider": "Anthropic"},
  "Reviewer": {"model": "gemini-2.5-pro-preview-05-06", "provider": "Google"}
}
```
**Cost**: ~$2-5 per waypoint
**Use Case**: Most development tasks

## Multi-Model Configuration

The system defaults use specific models optimized for each agent's role:

```python
# Default configurations in code
self.agent_configs = {
    "Planner": AgentModelConfig(
        provider="OpenAI",
        model="gpt-4.1-2025-04-14",  # Note: Consider using claude-opus-4 or o3
        temperature=0.7,
        max_tokens=2000
    ),
    "CodeGen": AgentModelConfig(
        provider="OpenAI",
        model="gpt-4.1-2025-04-14",  # Note: Consider using gemini-flash
        temperature=0.2,
        max_tokens=4000
    ),
    # ... etc
}
```

**Important**: The actual code in `aima_codegen/multi_model/config.py` contains default presets that use OpenAI models. You may want to update these presets to match your preferred configuration using Anthropic for planning/review and Google for code generation.

## Advanced Configuration

### Custom Temperature Settings

Different tasks benefit from different temperature values:

```python
# Creative tasks (planning)
"Planner": {
  "temperature": 0.7,  # More creative
  "top_p": 0.9
}

# Deterministic tasks (code)
"CodeGen": {
  "temperature": 0.2,  # More focused
  "top_p": 0.5
}
```

### Provider Fallbacks

Configure fallback models for reliability:

```json
{
  "CodeGen": {
    "primary": {
      "provider": "OpenAI",
      "model": "gpt-4"
    },
    "fallback": {
      "provider": "Anthropic",
      "model": "claude-3-sonnet"
    }
  }
}
```

### Rate Limit Management

Distribute load across providers:

```python
# Morning: Use OpenAI
if datetime.now().hour < 12:
    config["provider"] = "OpenAI"
# Afternoon: Use Anthropic
else:
    config["provider"] = "Anthropic"
```

### A/B Testing Models

Compare model performance:

```python
# 50/50 split for testing
import random
if random.random() < 0.5:
    model = "gpt-4"
else:
    model = "claude-3-opus"
```

## Examples

### Example 1: Web Application Project

**Requirements**: Build a Flask web app with authentication

```json
{
  "Planner": {
    "provider": "Anthropic",
    "model": "claude-opus-4-20250514",
    "reasoning": "Complex architecture needs deep reasoning"
  },
  "CodeGen": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "reasoning": "Large context for app code, cost-effective"
  },
  "TestWriter": {
    "provider": "Anthropic",
    "model": "claude-sonnet-4-20250514",
    "reasoning": "Security tests need thoroughness"
  },
  "Reviewer": {
    "provider": "Anthropic",
    "model": "claude-opus-4-20250514",
    "reasoning": "Security review is paramount"
  }
}
```

### Example 2: Data Science Project

**Requirements**: Build ML pipeline with data preprocessing

```json
{
  "Planner": {
    "provider": "OpenAI",
    "model": "o3-2025-04-16",
    "reasoning": "Complex ML workflow planning"
  },
  "CodeGen": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "reasoning": "Handles large data processing code well"
  },
  "TestWriter": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "reasoning": "Simple data validation tests"
  },
  "Reviewer": {
    "provider": "Anthropic",
    "model": "claude-sonnet-4-20250514",
    "reasoning": "Good balance for ML code review"
  }
}
```

### Example 3: CLI Tool Project

**Requirements**: Command-line utility with file processing

```json
{
  "Planner": {
    "provider": "Anthropic",
    "model": "claude-sonnet-4-20250514",
    "reasoning": "Simple project, mid-tier planning sufficient"
  },
  "CodeGen": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "reasoning": "Simple code, very cost-effective"
  },
  "TestWriter": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "reasoning": "Basic unit tests sufficient"
  },
  "Reviewer": {
    "provider": "Google",
    "model": "gemini-2.5-flash-preview-05-20",
    "reasoning": "Fast, cheap review for simple code"
  }
}
```

## Best Practices

### 1. Start Simple
- Begin with single-model mode
- Test your workflow
- Gradually introduce multi-model

### 2. Monitor Performance
- Track costs per agent
- Measure quality improvements
- Adjust based on results

### 3. Use Presets
- Start with balanced preset
- Customize as needed
- Save custom presets

### 4. Consider Context
- Project complexity
- Budget constraints
- Quality requirements
- Time sensitivity

### 5. Test Combinations
- Try different providers
- Compare outputs
- Find optimal mix

### 6. Update Regularly
- New models release frequently
- Prices change
- Capabilities improve

### 7. Document Choices
- Record why you chose specific models
- Track performance metrics
- Share learnings with team

### 8. Ensure Reliability
- Monitor agent errors and adjust models if needed (if a particular model struggles with a task, consider switching that agent to a more reliable model or using single-model mode for critical steps)

## Troubleshooting

### Model Not Available
```
Error: Model 'claude-opus-4-20250514' not found
```
**Solution**: 
- Verify API access to Anthropic
- Check model name spelling
- Ensure account has access to Claude Opus 4

### Inconsistent Output Quality
**Solution**:
- Adjust temperature settings
- Try different models
- Increase max_tokens

### Budget Exceeded Quickly
**Solution**:
- Review model costs
- Use cheaper models for simple tasks
- Set agent-specific budgets

### Slow Response Times
**Solution**:
- Use turbo/flash variants
- Distribute across providers
- Enable parallel processing

## Conclusion

Multi-Model configuration is a powerful feature that enables:
- Significant cost savings
- Improved code quality
- Faster development cycles
- Provider diversity

Start with presets, experiment with combinations, and find the perfect balance for your projects!