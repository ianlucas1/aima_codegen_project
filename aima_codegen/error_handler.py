import logging
import time
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime

from aima_codegen.models import ProjectState

logger = logging.getLogger(__name__)


class TelemetryAwareErrorHandler:
    """Integrates telemetry with error recovery mechanisms"""
    
    def __init__(self, state: Optional[ProjectState] = None):
        """Initialize with optional project state."""
        self.state = state
        self.error_history: List[Dict[str, Any]] = []
        self.error_patterns = defaultdict(int)
        self.recovery_strategies = {}
        self.agent_error_counts = defaultdict(int)
        self.circuit_breaker_threshold = 5
    
    def handle_error(self, error: Exception, context: Dict[str, Any], agent: str) -> None:
        """Handle errors with telemetry integration and recovery."""
        # Log the error
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context.copy()
        }
        self.error_history.append(error_record)
        
        # Track error patterns
        error_key = f"{agent}:{type(error).__name__}"
        self.error_patterns[error_key] += 1
        self.agent_error_counts[agent] += 1
        
        # Handle specific error types
        if isinstance(error, KeyError) and str(error) == "'feedback_json'":
            # Inject default feedback_json
            context['feedback_json'] = {
                'error_type': 'KeyError',
                'recovery_action': 'injected_default',
                'message': 'Default feedback injected due to missing feedback_json'
            }
        
        # Log error
        logger.error(f"Error in {agent}: {type(error).__name__} - {str(error)}")
    
    def get_recovery_strategy(self, error: Exception) -> Dict[str, str]:
        """Select appropriate recovery strategy based on error type."""
        if isinstance(error, TimeoutError):
            return {
                'action': 'retry_with_extended_timeout',
                'description': 'Increase timeout and retry operation'
            }
        elif isinstance(error, KeyError):
            return {
                'action': 'inject_defaults',
                'description': 'Inject default values for missing keys'
            }
        elif isinstance(error, ValueError):
            return {
                'action': 'validation',
                'description': 'Validate and sanitize input data'
            }
        elif isinstance(error, RuntimeError):
            return {
                'action': 'runtime',
                'description': 'Handle runtime error with fallback'
            }
        else:
            return {
                'action': 'log_and_continue',
                'description': 'Log error and continue execution'
            }
    
    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Return telemetry summary of all errors."""
        error_types = defaultdict(int)
        errors_by_agent = defaultdict(int)
        
        for error in self.error_history:
            error_types[error['error_type']] += 1
            errors_by_agent[error['agent']] += 1
        
        return {
            'total_errors': len(self.error_history),
            'error_types': dict(error_types),
            'errors_by_agent': dict(errors_by_agent),
            'error_patterns': dict(self.error_patterns)
        }
    
    def should_circuit_break(self, agent: str) -> bool:
        """Check if circuit breaker should be triggered for an agent."""
        return self.agent_error_counts[agent] >= self.circuit_breaker_threshold
    
    def get_agent_error_count(self, agent: str) -> int:
        """Get error count for a specific agent."""
        return self.agent_error_counts[agent]
    
    def detect_error_patterns(self) -> List[Dict[str, Any]]:
        """Detect patterns in error occurrences."""
        patterns = []
        
        # Detect repeated errors
        for error_key, count in self.error_patterns.items():
            if count >= 2:  # Pattern threshold
                agent, error_type = error_key.split(':', 1)
                patterns.append({
                    'pattern_type': 'repeated_error',
                    'agent': agent,
                    'error_type': error_type,
                    'count': count,
                    'severity': 'high' if count >= 5 else 'medium'
                })
        
        # Detect agent-specific patterns
        for agent, error_count in self.agent_error_counts.items():
            if error_count >= 3:
                patterns.append({
                    'pattern_type': 'agent_failure',
                    'agent': agent,
                    'total_errors': error_count,
                    'recommendation': 'Consider reviewing agent implementation'
                })
        
        return patterns
    
    def handle_agent_error(self, agent_id: str, error: Exception, context: dict):
        """Handle agent errors (backward compatibility method)."""
        self.handle_error(error, context, agent_id)
        
        # Get recovery strategy
        strategy = self.get_recovery_strategy(error)
        
        # Apply recovery based on strategy
        if strategy['action'] == 'inject_defaults' and isinstance(error, KeyError):
            if 'feedback_json' in str(error):
                context.setdefault('feedback_json', '{}')
        
        return context


# Legacy recovery strategy classes for backward compatibility
class FeedbackJsonRecoveryStrategy:
    def __init__(self, telemetry):
        self.telemetry = telemetry
    
    def execute(self, context: dict):
        context.setdefault('feedback_json', '{}')
        if self.telemetry:
            try:
                self.telemetry.record_event('recovery_feedback_json', {'status': 'placeholder_inserted'})
            except AttributeError:
                pass
        return context


class TimeoutRecoveryStrategy:
    def __init__(self, telemetry):
        self.telemetry = telemetry
    
    def execute(self, context: dict):
        if self.telemetry:
            try:
                self.telemetry.record_event('recovery_timeout', {'status': 'retry'})
            except AttributeError:
                pass
        return context


class CodeQualityRecoveryStrategy:
    def __init__(self, telemetry):
        self.telemetry = telemetry
    
    def execute(self, context: dict):
        if self.telemetry:
            try:
                self.telemetry.record_event('recovery_code_quality', {'status': 'adjusted'})
            except AttributeError:
                pass
        return context


class DefaultRecoveryStrategy:
    def __init__(self, telemetry):
        self.telemetry = telemetry
    
    def execute(self, context: dict):
        if self.telemetry:
            try:
                self.telemetry.record_event('recovery_default', {'status': 'no_action'})
            except AttributeError:
                pass
        return context 