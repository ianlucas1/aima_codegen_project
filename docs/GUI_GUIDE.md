# AIMA CodeGen GUI Guide

This guide provides a comprehensive walkthrough of the AIMA CodeGen graphical user interface.

## Table of Contents
- [Launching the GUI](#launching-the-gui)
- [Main Window Overview](#main-window-overview)
- [Project Management](#project-management)
- [Development Workflow](#development-workflow)
- [Model Configuration](#model-configuration)
- [Code Review Features](#code-review-features)
- [Settings and Configuration](#settings-and-configuration)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Tips and Best Practices](#tips-and-best-practices)

## Launching the GUI

To start the GUI application, simply run:

```bash
aima-codegen gui
```

The GUI will open in a new window with the default size of 1200x800 pixels.

## Main Window Overview

The main window is divided into three primary panels:

### 1. Project Panel (Left)
The project management area contains:
- **Project Name**: Displays the currently loaded project
- **Budget Tracker**: Shows current spending vs. total budget
- **Action Buttons**:
  - New Project: Create a new project
  - Load Project: Load an existing project
- **Waypoints Tree**: Visual representation of project waypoints with status indicators

#### Waypoint Status Symbols
- ✓ SUCCESS (Green) - Waypoint completed successfully
- ✗ FAILED (Red) - Waypoint failed
- ▶ RUNNING (Yellow) - Waypoint currently executing
- ◯ PENDING (Cyan) - Waypoint waiting to be executed

### 2. Development Panel (Center)
The main work area includes:
- **Requirements Text Area**: Enter your project requirements here
- **Control Buttons**:
  - Start Development: Begin the development process
  - Stop: Halt the current operation
- **Model Strategy Selection**:
  - Single Model: Use one model for all agents
  - Multi-Model: Configure different models per agent
- **Code Review Options**:
  - Enable automatic code review
  - GitHub integration toggle
  - Manual Review button
- **Agent Model Configuration**: Dropdowns for each agent when Multi-Model is selected

### 3. Status Panel (Right)
Real-time monitoring area with:
- **Progress Bar**: Visual progress indicator
- **Current Task**: Shows what the system is currently doing
- **Log Output**: Color-coded logs with:
  - Blue: Info messages
  - Green: Success messages
  - Red: Error messages
  - Orange: Warning messages

### Status Bar (Bottom)
Displays:
- Current status message
- Active provider and model information

## Project Management

### Creating a New Project

1. Click **New Project** in the Project Panel
2. Enter a project name in the dialog
3. Set your budget in USD (default: 10.0)
4. Click **Create**

The system will:
- Create project directory structure
- Initialize virtual environment
- Set up project state management
- Create empty requirements.txt

### Loading an Existing Project

1. Click **Load Project** in the Project Panel
2. Select a project from the list
3. Click **Load**

The system will:
- Load project state
- Restore waypoint progress
- Initialize managers
- Display current budget usage

## Development Workflow

### Starting Development

1. Enter your requirements in the Requirements text area
2. Select your model strategy:
   - **Single Model**: Faster, uses default model for all agents
   - **Multi-Model**: Allows optimization per agent
3. Configure code review options as needed
4. Click **Start Development**

### During Development

The system will:
1. Plan waypoints using the Planner agent
2. Display waypoints in the tree view
3. Execute each waypoint sequentially
4. Update progress in real-time
5. Show logs in the Status Panel

### Stopping Development

Click the **Stop** button to halt execution. The system will:
- Complete the current operation
- Save project state
- Preserve completed waypoints

## Model Configuration

### Single Model Mode
Uses the default model configured in settings for all agents.

### Multi-Model Mode

When Multi-Model is selected, configure each agent individually:

1. **Planner Agent**: Best with creative models
   - Recommended: GPT-4 or Claude-3-Opus
   
2. **CodeGen Agent**: Requires high accuracy
   - Recommended: GPT-4-Turbo or Claude-3-Opus
   
3. **TestWriter Agent**: Needs comprehensive coverage
   - Recommended: GPT-4 or GPT-4-Turbo
   
4. **Reviewer Agent**: Excellent at finding issues
   - Recommended: Claude-3-Opus

### Model Presets

Access via Model Settings dialog:
- **Fast**: Economical models for rapid development
- **Quality**: Premium models for production code
- **Balanced**: Optimal cost/performance ratio

## Code Review Features

### Automatic Code Review
When enabled, the Reviewer agent will:
- Analyze code for bugs and issues
- Check security vulnerabilities
- Suggest performance improvements
- Verify best practices

### GitHub Integration
When enabled with a valid GitHub token:
- Creates feature branches automatically
- Generates pull requests
- Posts review comments
- Manages PR lifecycle

### Manual Review
Click **Manual Review** to:
- Review current waypoint code
- See AI suggestions
- Make manual adjustments
- Approve or request changes

## Settings and Configuration

### API Key Configuration

Access via **Tools → Configure API Keys**:

1. **OpenAI Tab**
   - Enter your OpenAI API key
   - Test connection
   
2. **Anthropic Tab**
   - Enter your Anthropic API key
   - Test connection
   
3. **Google AI Tab**
   - Enter your Google AI API key
   - Test connection

Keys are stored securely using the system keyring.

### Model Settings

Access via **Tools → Model Settings**:

1. **Default Settings**
   - Set default provider
   - Set default model
   
2. **Multi-Model Configuration**
   - Configure each agent separately
   - Set temperature values
   - Choose optimal models

### GitHub Settings

Access via **Tools → GitHub Settings**:

1. Enter your GitHub Personal Access Token
2. Configure automation options:
   - Auto-create pull requests
   - Auto-merge approved PRs
3. Test connection

Required token scopes: `repo`, `workflow`

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Load Project |
| Ctrl+D | Start Development |
| Ctrl+S | Stop Development |
| Ctrl+R | Manual Review |
| Ctrl+Q | Quit Application |
| F5 | Refresh Status |

## Tips and Best Practices

### 1. Requirements Writing
- Be specific and detailed
- Break down complex features
- Include technical constraints
- Mention desired libraries

### 2. Budget Management
- Start with smaller budgets for testing
- Monitor spending in real-time
- Use Multi-Model to optimize costs
- Review waypoint costs in status

### 3. Model Selection
- Use cheaper models for planning
- Invest in quality for code generation
- Claude excels at code review
- Test different combinations

### 4. Development Strategy
- Start with Single Model for prototypes
- Switch to Multi-Model for production
- Enable code review for critical projects
- Use GitHub integration for team projects

### 5. Troubleshooting
- Check logs for detailed errors
- Verify API keys are valid
- Ensure sufficient API credits
- Monitor rate limits

### 6. Performance Tips
- Close unnecessary applications
- Ensure stable internet connection
- Use local Git repository
- Keep projects organized

## Common Issues and Solutions

### GUI Won't Open
- Verify tkinter installation: `python -m tkinter`
- Check Python version (3.10+ required)
- Try running with elevated permissions

### Models Not Loading
- Verify API keys in configuration
- Check internet connectivity
- Ensure model names are correct
- Review model costs configuration

### Development Stalls
- Check budget hasn't been exceeded
- Verify API rate limits
- Review error logs
- Try stopping and resuming

### GitHub Integration Issues
- Verify token has correct scopes
- Ensure Git is installed
- Check repository permissions
- Verify branch naming conflicts

## Advanced Features

### Custom Waypoint Editing
Right-click on a waypoint to:
- View details
- Edit description
- Retry execution
- Skip waypoint

### Log Filtering
In the Status Panel:
- Filter by log level
- Search for specific terms
- Export logs to file
- Clear log display

### Project Templates
Save and reuse project configurations:
- Export current settings
- Create project templates
- Share configurations
- Import templates

## Getting Help

1. **In-App Help**: Access via Help menu
2. **Tooltips**: Hover over controls
3. **Status Messages**: Monitor status bar
4. **Error Details**: Check log panel
5. **Documentation**: Refer to this guide

For additional support, visit the GitHub repository or check the main documentation.