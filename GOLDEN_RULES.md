# Golden Rules for AIMA CodeGen Agents

All development agents must follow these inviolable principles to ensure system stability and continuous improvement:

1. **Preserve Existing Functionality** – Never remove or degrade existing features without explicit user approval. All enhancements should be additive or strictly improve upon current behavior.
2. **Maintain or Improve Test Coverage** – Any code change must include appropriate tests. The overall test coverage should stay the same or increase; no new functionality is accepted without corresponding tests.
3. **Every Error Has a Recovery Path** – Anticipate failure modes and implement fallback actions for each. The system should handle errors gracefully (retry, skip, inject defaults) rather than simply halting on exceptions.
4. **Ensure Backwards Compatibility** – Changes should not break existing interfaces, workflows, or user expectations. If a breaking change is unavoidable, it must be clearly documented and feature-flagged or deferred until explicitly permitted.
5. **Document Decisions and Rationale** – For every significant change, update relevant documentation (code comments, READMEs, guides) and record the reasoning behind the change. This transparency helps future agents and developers understand why a change was made.

Adhering to these Golden Rules is mandatory. They serve as guardrails that keep the AIMA CodeGen system robust, prevent regressions, and ensure that each self-improvement cycle results in a net positive gain in quality and reliability. 