# System Self-Improvement Guide

You are improving the AIMA CodeGen system itself. Remember:

1. You are modifying `aima_codegen/` not a regular project `src/`
2. Preserve all existing functionality - only add, don't break
3. Run tests after changes: `python -m pytest aima_codegen/tests/`
4. Start with simple additions (markdown files) before code changes
5. Document every change clearly

## Core Self-Improvement Infrastructure (Implemented):
The following foundational components have been successfully implemented and are active in the system. Self-improvement tasks will build upon this existing infrastructure.

### ✅ Phase 1: Agent Guidance System
Documentation in `aima_codegen/agents/` providing operational blueprints:
- **PLANNER.md**: Details waypoint decomposition and planning best practices.
- **CODEGEN.md**: Outlines code generation patterns, quality standards, and dependency management.
- **TESTWRITER.md**: Specifies test writing standards and pytest best practices.
- **REVIEWER.md**: Defines code review criteria and GitHub integration protocols.
- **EXPLAINER.md**: Sets guidelines for clear code explanations and communication strategies.

### ✅ Phase 2: Comprehensive Telemetry Logging
All agent `execute()` methods are enhanced with thorough telemetry logging:
- Integrated into `BaseAgent` for consistent data capture.
- Captures input context, LLM interactions (prompts, raw responses, token usage, cost).
- Tracks decision points with reasoning and alternatives considered.
- Records agent-assessed confidence levels for each execution.
- Telemetry logs are stored in structured JSONL format at `project_path/logs/agent_telemetry.jsonl`.
- The Orchestrator automatically ensures telemetry is active for all agents.

### ✅ Phase 3: Post-Task Debrief System
Agents perform a structured self-assessment after each task execution:
- Generates a comprehensive debrief analyzing the task's outcome.
- Includes self-assessment of confidence levels and identification of potential risks or ambiguities.
- Evaluates the quality of decisions made and suggests alternative approaches considered.
- Captures lessons learned, including successes, challenges faced, and opportunities for improvement.
- Provides recommendations for future similar tasks and potential follow-up actions.
- Debriefs are stored in structured JSON format in `project_path/logs/debriefs/`.

### ✅ Phase 4: Fault Tolerance & Hardening (COMPLETED)
Strengthened system resilience and error management:
- ✅ Introduced `ResilientOrchestrator` class with signal handling and partial failure isolation (circuit breaker pattern)
- ✅ Implemented `SymlinkAwarePathResolver` for safe symlinked project environments
- ✅ Implemented `TelemetryAwareErrorHandler` for centralized error tracking and recovery strategies
- ✅ Integrated graceful shutdown (SIGINT/SIGTERM) and execution checkpointing

**Status**: Core self-improvement and fault-tolerance infrastructure complete. The system now features comprehensive telemetry logging, post-execution debriefs, a fault-tolerant orchestrator, and a safe self-modification framework.

## New Infrastructure Added:

### Self-Improvement Commands
- `aima-codegen improve <feature>` - Self-improvement mode
- Available improvements: `agent-guides`, `basic-telemetry`, `debrief-system`
- Special project initialization for self-modification

### Enhanced Agent Capabilities
- **Telemetry Logging**: Comprehensive execution data capture
- **Decision Tracking**: Structured decision point recording with reasoning
- **Confidence Assessment**: Quantified confidence levels for all outputs
- **Self-Assessment**: Post-execution debriefs with improvement suggestions

### Data Structures
- **Agent Telemetry**: JSON logs with execution context and outcomes
- **Decision Points**: Timestamped choices with options and reasoning
- **Debriefs**: Structured self-assessments with lessons learned
- **Confidence Metrics**: Quantified assessment of task execution quality

## Usage Examples:

### Self-Improvement Mode
```bash
# Initialize self-improvement for a specific feature
aima-codegen improve agent-guides --budget 5.0

# The system will:
# 1. Create a special self-improvement project
# 2. Symlink src/ to the actual aima_codegen package
# 3. Run normal development process on the live system
```

### Telemetry Analysis
```bash
# View telemetry logs
cat ~/.AIMA_CodeGen/projects/SELF_IMPROVE_*/logs/agent_telemetry.jsonl

# View debriefs
ls ~/.AIMA_CodeGen/projects/SELF_IMPROVE_*/logs/debriefs/
```

## Architecture Benefits:

1. **Self-Awareness**: Agents now track their own decision-making process
2. **Continuous Learning**: Structured capture of lessons learned
3. **Quality Metrics**: Confidence levels provide execution quality indicators
4. **Process Improvement**: Debriefs suggest concrete improvements
5. **Transparency**: Full visibility into agent reasoning and choices
6. **Self-Modification**: Safe framework for system self-improvement
7. **Fault Tolerance**: Partial failures are contained and recovered without disrupting the overall process (no cascading errors)

## Next Steps for Future Improvements:

1. **Analytics Dashboard**: Visualization of telemetry and debrief data
2. **Adaptive Confidence**: Dynamic confidence thresholds based on performance
3. **Learning Integration**: Use historical data to improve future decisions
4. **Advanced Metrics**: More sophisticated quality and performance indicators
5. **Cross-Agent Learning**: Share insights between different agent types

---

**Status**: Core self-improvement infrastructure complete. System now has comprehensive logging, self-assessment, and safe self-modification capabilities. 