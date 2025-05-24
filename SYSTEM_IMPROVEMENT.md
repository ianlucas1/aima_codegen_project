# System Self-Improvement Guide

You are improving the AIMA CodeGen system itself. Remember:

1. You are modifying `aima_codegen/` not a regular project `src/`
2. Preserve all existing functionality - only add, don't break
3. Run tests after changes: `python -m pytest aima_codegen/tests/`
4. Start with simple additions (markdown files) before code changes
5. Document every change clearly

## Current Improvement Priority:

### Phase 1: Agent Guides (Start Here!)
Create these files in `aima_codegen/agents/`:
- PLANNER.md - Planning best practices
- CODEGEN.md - Code generation patterns  
- TESTWRITER.md - Test writing standards
- REVIEWER.md - Review criteria
- EXPLAINER.md - Explanation guidelines

### Phase 2: Logging Infrastructure
Add to each agent's execute() method:
- Log all inputs and outputs
- Capture decision points
- Record confidence levels

### Phase 3: Debrief System
After each execute(), generate:
- Self-assessment JSON
- Lessons learned
- Improvement suggestions 