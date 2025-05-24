# Changelog

All notable changes to AIMA CodeGen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation suite
  - Enhanced README with new features
  - GUI Guide with detailed instructions
  - GitHub Integration Guide
  - Multi-Model Configuration Guide
  - API Reference for all new features

#### 🤖 Self-Improvement System
- **Bootstrap capability**: New `aima-codegen improve` command enables system self-modification
- **Agent guide documents**: Comprehensive markdown guides for all agents (PLANNER.md, CODEGEN.md, TESTWRITER.md, REVIEWER.md, EXPLAINER.md)
- **Telemetry infrastructure**: Complete agent execution logging with decision tracking
- **Self-assessment system**: Post-task debrief generation with confidence metrics
- **Safe self-modification**: Symlink-based approach for controlled system updates
- System successfully used this capability to implement all improvements autonomously
- Foundation for continuous self-improvement and learning

### Technical Enhancements
- Enhanced BaseAgent with telemetry logging and debrief generation
- Added decision point tracking with reasoning capture
- Implemented confidence level assessment for all agents
- Created structured JSON logging for agent telemetry
- Added SYSTEM_IMPROVEMENT.md guide for future enhancements

### Changed
- Updated model presets to use frontier models (Claude Opus 4, Gemini Flash, O3)
- Optimized default agent configurations for cost and performance

## [1.1.0] - 2025-01-24

### Added

#### 🎨 Professional GUI Application
- Full-featured Tkinter interface with three-panel layout
- Project management with visual waypoint tracking
- Real-time progress monitoring and colored logs
- Model strategy selection (Single/Multi-Model)
- Integrated configuration dialogs for API keys and settings
- Keyboard shortcuts for common operations
- Thread-safe message queue for background operations

#### 🤖 Multi-Model Configuration
- Per-agent model selection with individual dropdowns
- Support for mixing providers (OpenAI, Anthropic, Google)
- Model presets: Fast, Quality, and Balanced
- Dynamic configuration without restart
- Cost optimization through strategic model selection
- Configuration persistence in JSON format

#### 🔗 GitHub Integration
- ReviewerAgent for AI-powered code review
- Automated pull request creation
- Branch management and git operations
- PR lifecycle management (create, review, merge)
- GitHub CLI integration when available
- Webhook support for CI/CD integration

### Changed
- Orchestrator now supports multi-model configuration
- Enhanced error handling for all new features
- Improved logging with component-specific loggers

### Fixed
- Token counting for newer models
- Config file permissions on creation

## [1.0.0] - 2025-01-20

### Added

#### Core Features
- Multi-agent architecture (Planner, CodeGen, TestWriter, Explainer)
- Support for OpenAI, Anthropic, and Google AI models
- Budget management with pre-call checks and cost tracking
- Virtual environment management
- Project state persistence
- Rich CLI interface with Typer

#### Agents
- **PlannerAgent**: Decomposes requirements into waypoints
- **CodeGenAgent**: Generates Python code with dependency management
- **TestWriterAgent**: Creates comprehensive pytest suites
- **ExplainerAgent**: Provides plain English code explanations

#### Project Management
- Atomic state updates with temporary file strategy
- Lock file mechanism to prevent concurrent access
- Waypoint-based development tracking
- Revision loops with automatic error correction

#### LLM Integration
- Unified interface for multiple providers
- Automatic retry with exponential backoff
- Token counting for all providers
- Model-specific temperature and token settings

#### Testing & Verification
- Automated syntax checking
- Flake8 integration for code style
- Pytest execution with configurable arguments
- Revision feedback system

### Configuration
- Hierarchical configuration system
- Secure API key storage with keyring
- Model costs tracking
- Customizable agent parameters

### CLI Commands
- `init`: Create new project
- `develop`: Start development from requirements
- `load`: Load existing project
- `status`: Show project status
- `explain`: Get code explanations
- `config`: Manage settings

## Migration Guide

### Upgrading from 1.0.0 to 1.1.0

1. **New Dependencies**
   ```bash
   pip install -e .  # Will install new dependencies
   ```

2. **Configuration Updates**
   - New `[GitHub]` section in config.ini
   - New `multi_model_config.json` file
   - Model costs updated for 2025 models

3. **API Changes**
   - Orchestrator has new `enable_multi_model()` method
   - New `gui` CLI command available
   - ReviewerAgent added to agents module

4. **Breaking Changes**
   - None - fully backward compatible

### Using New Features

#### Launch GUI
```bash
aima-codegen gui
```

#### Enable Multi-Model
```python
orchestrator.enable_multi_model()
```

#### Configure GitHub
```bash
aima-codegen config --set GitHub.token --value YOUR_TOKEN
```

## Future Roadmap

### Planned Features
- [ ] Cloud deployment support
- [ ] Team collaboration features
- [ ] Custom agent creation framework
- [ ] Plugin system for extensions
- [ ] Web-based GUI option
- [ ] Advanced analytics dashboard
- [ ] Integration with more version control systems
- [ ] Support for more programming languages

### Under Consideration
- Real-time collaboration
- AI model fine-tuning
- Project templates marketplace
- Integration with IDEs
- Automated documentation generation
- Performance profiling tools

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Support

For issues and questions:
- Check the [documentation](docs/)
- Review [closed issues](https://github.com/ianlucas1/aima_codegen_project/issues?q=is%3Aissue+is%3Aclosed)
- Open a [new issue](https://github.com/ianlucas1/aima_codegen_project/issues/new)

## Acknowledgments

- AIMA (Artificial Intelligence: A Modern Approach) for multi-agent principles
- The open-source community for excellent libraries
- Early adopters for valuable feedback