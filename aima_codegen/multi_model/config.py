"""Multi-model configuration for AIMA CodeGen.
Allows different agents to use different LLM models and providers.
"""
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

from ..config import config
from ..models import LLMRequest, LLMResponse
from ..llm import OpenAIAdapter, AnthropicAdapter, GoogleAdapter, LLMServiceInterface
from ..exceptions import InvalidAPIKeyError

logger = logging.getLogger(__name__)

@dataclass
class AgentModelConfig:
    """Configuration for a specific agent's model."""
    provider: str
    model: str
    temperature: float
    max_tokens: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentModelConfig':
        return cls(**data)


class MultiModelManager:
    """Manages multiple LLM configurations for different agents."""
    
    def __init__(self):
        self.default_provider = config.get("General", "default_provider", "OpenAI")
        self.default_model = config.get("General", "default_model", "gpt-4.1-2025-04-14")
        
        # Agent-specific configurations
        self.agent_configs: Dict[str, AgentModelConfig] = {}
        
        # LLM service instances cache
        self.llm_services: Dict[str, LLMServiceInterface] = {}
        
        # Load configurations
        self._load_configurations()
    
    def _load_configurations(self):
        """Load agent-specific model configurations from config file."""
        config_path = Path.home() / ".AIMA_CodeGen" / "multi_model_config.json"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    for agent, config_data in data.items():
                        self.agent_configs[agent] = AgentModelConfig.from_dict(config_data)
            except Exception as e:
                logger.error(f"Failed to load multi-model config: {e}")
        else:
            # Create default configurations
            self._create_default_configs()
    
    def _create_default_configs(self):
        """Create default agent configurations."""
        # Optimal configurations for each agent type
        self.agent_configs = {
            "Planner": AgentModelConfig(
                provider="OpenAI",
                model="gpt-4.1-2025-04-14",
                temperature=0.7,
                max_tokens=2000
            ),
            "CodeGen": AgentModelConfig(
                provider="OpenAI",
                model="gpt-4.1-2025-04-14",
                temperature=0.2,  # Lower for code generation
                max_tokens=4000
            ),
            "TestWriter": AgentModelConfig(
                provider="OpenAI",
                model="gpt-4.1-2025-04-14",
                temperature=0.2,  # Lower for test generation
                max_tokens=4000
            ),
            "Reviewer": AgentModelConfig(
                provider="Anthropic",
                model="claude-opus-4-20250514",  # Claude is excellent at code review
                temperature=0.3,
                max_tokens=2000
            ),
            "Explainer": AgentModelConfig(
                provider="Anthropic",
                model="claude-sonnet-4-20250514",  # Good balance for explanations
                temperature=0.7,
                max_tokens=1000
            )
        }
    
    def save_configurations(self):
        """Save current configurations to file."""
        config_path = Path.home() / ".AIMA_CodeGen" / "multi_model_config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        data = {agent: cfg.to_dict() for agent, cfg in self.agent_configs.items()}
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_llm_service(self, agent_type: str) -> LLMServiceInterface:
        """Get LLM service instance for a specific agent."""
        # Get configuration for this agent
        if agent_type in self.agent_configs:
            agent_config = self.agent_configs[agent_type]
            provider = agent_config.provider
        else:
            # Use default
            provider = self.default_provider
        
        # Check cache
        if provider in self.llm_services:
            return self.llm_services[provider]
        
        # Create new instance
        llm_service = self._create_llm_service(provider)
        self.llm_services[provider] = llm_service
        return llm_service
    
    def _create_llm_service(self, provider: str) -> LLMServiceInterface:
        """Create LLM service instance for provider."""
        # Get API key
        api_key = self._get_api_key(provider)
        
        if provider.lower() == "openai":
            return OpenAIAdapter(api_key)
        elif provider.lower() == "anthropic":
            return AnthropicAdapter(api_key)
        elif provider.lower() == "google":
            return GoogleAdapter(api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key for provider."""
        # Similar to orchestrator._get_api_key but simplified
        import os
        
        # Check environment variables
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        
        env_var = env_var_map.get(provider.lower())
        if env_var:
            api_key = os.environ.get(env_var)
            if api_key:
                return api_key
        
        # Check config
        config_key = f"{provider.lower()}_api_key"
        api_key = config.get("API_Keys", config_key)
        if api_key:
            return api_key
        
        raise InvalidAPIKeyError(f"No API key found for {provider}")
    
    def get_agent_config(self, agent_type: str) -> AgentModelConfig:
        """Get configuration for specific agent."""
        if agent_type in self.agent_configs:
            return self.agent_configs[agent_type]
        
        # Return default configuration
        return AgentModelConfig(
            provider=self.default_provider,
            model=self.default_model,
            temperature=config.get("LLM", "other_temperature", 0.7),
            max_tokens=config.get("LLM", "other_max_tokens", 1000)
        )
    
    def set_agent_config(self, agent_type: str, config: AgentModelConfig):
        """Set configuration for specific agent."""
        self.agent_configs[agent_type] = config
        self.save_configurations()
    
    def update_agent_config(self, agent_type: str, **kwargs):
        """Update specific fields of agent configuration."""
        current_config = self.get_agent_config(agent_type)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(current_config, key):
                setattr(current_config, key, value)
        
        self.agent_configs[agent_type] = current_config
        self.save_configurations()
    
    def get_model_options(self, provider: str) -> list:
        """Get available models for a provider."""
        model_options = {
            "OpenAI": [
                "gpt-4.1-2025-04-14",
                "o4-mini-2025-04-16",
                "o3-2025-04-16"
            ],
            "Anthropic": [
                "claude-opus-4-20250514",
                "claude-sonnet-4-20250514"
            ],
            "Google": [
                "gemini-2.5-pro-preview-05-06",
                "gemini-2.5-flash-preview-05-20"
            ]
        }
        
        return model_options.get(provider, [])
    
    def validate_all_services(self) -> Dict[str, bool]:
        """Validate all configured LLM services."""
        results = {}
        
        # Get unique providers
        providers = set([self.default_provider])
        for agent_config in self.agent_configs.values():
            providers.add(agent_config.provider)
        
        # Test each provider
        for provider in providers:
            try:
                service = self._create_llm_service(provider)
                results[provider] = service.validate_api_key()
            except Exception as e:
                logger.error(f"Failed to validate {provider}: {e}")
                results[provider] = False
        
        return results


class MultiModelOrchestrator:
    """Extension of Orchestrator to support multi-model configuration."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.multi_model_manager = MultiModelManager()
    
    def configure_agents_with_multi_model(self):
        """Configure all agents to use their specific models."""
        # Update each agent with its specific LLM service
        agents = {
            "Planner": self.orchestrator.planner,
            "CodeGen": self.orchestrator.codegen,
            "TestWriter": self.orchestrator.testwriter,
            "Reviewer": getattr(self.orchestrator, 'reviewer', None),
            "Explainer": self.orchestrator.explainer
        }
        
        for agent_type, agent in agents.items():
            if agent:
                # Get LLM service for this agent type
                llm_service = self.multi_model_manager.get_llm_service(agent_type)
                agent.llm_service = llm_service
                
                # Store model configuration in agent
                agent.model_config = self.multi_model_manager.get_agent_config(agent_type)
                logger.info(f"Configured {agent_type} with {agent.model_config.provider} - {agent.model_config.model}")
    
    def execute_with_multi_model(self, agent_type: str, context: Dict) -> Dict:
        """Execute agent with its specific model configuration."""
        # Get agent
        agent = getattr(self.orchestrator, agent_type.lower(), None)
        if not agent:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        # Get model configuration
        model_config = self.multi_model_manager.get_agent_config(agent_type)
        
        # Update context with model info
        context["model"] = model_config.model
        context["temperature"] = model_config.temperature
        context["max_tokens"] = model_config.max_tokens
        
        # Execute agent
        return agent.execute(context)
    
    def update_agent_model(self, agent_type: str, provider: str = None, 
                          model: str = None, temperature: float = None):
        """Update model configuration for specific agent."""
        kwargs = {}
        if provider:
            kwargs["provider"] = provider
        if model:
            kwargs["model"] = model
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        self.multi_model_manager.update_agent_config(agent_type, **kwargs)
        
        # Reconfigure agents
        self.configure_agents_with_multi_model()
    
    def get_cost_breakdown_by_agent(self) -> Dict[str, Dict[str, float]]:
        """Get cost breakdown by agent type."""
        # This would track costs per agent
        # Implementation would require modifying agents to track their individual costs
        pass


# Example configuration presets for different use cases
class ModelPresets:
    """Predefined model configurations for different scenarios."""
    
    FAST_DEVELOPMENT = {
        "Planner": AgentModelConfig("OpenAI", "o4-mini-2025-04-16", 0.7, 2000),
        "CodeGen": AgentModelConfig("OpenAI", "o4-mini-2025-04-16", 0.2, 4000),
        "TestWriter": AgentModelConfig("OpenAI", "o4-mini-2025-04-16", 0.2, 3000),
        "Reviewer": AgentModelConfig("Google", "gemini-2.5-flash-preview-05-20", 0.3, 2000),
        "Explainer": AgentModelConfig("Google", "gemini-2.5-flash-preview-05-20", 0.7, 1000)
    }
    
    HIGH_QUALITY = {
        "Planner": AgentModelConfig("OpenAI", "o3-2025-04-16", 0.5, 3000),
        "CodeGen": AgentModelConfig("OpenAI", "gpt-4.1-2025-04-14", 0.1, 6000),
        "TestWriter": AgentModelConfig("OpenAI", "gpt-4.1-2025-04-14", 0.1, 5000),
        "Reviewer": AgentModelConfig("Anthropic", "claude-opus-4-20250514", 0.2, 3000),
        "Explainer": AgentModelConfig("Anthropic", "claude-opus-4-20250514", 0.6, 2000)
    }
    
    BALANCED = {
        "Planner": AgentModelConfig("OpenAI", "gpt-4.1-2025-04-14", 0.7, 2000),
        "CodeGen": AgentModelConfig("OpenAI", "gpt-4.1-2025-04-14", 0.2, 4000),
        "TestWriter": AgentModelConfig("OpenAI", "gpt-4.1-2025-04-14", 0.2, 4000),
        "Reviewer": AgentModelConfig("Anthropic", "claude-sonnet-4-20250514", 0.3, 2000),
        "Explainer": AgentModelConfig("Google", "gemini-2.5-pro-preview-05-06", 0.7, 1500)
    }
    
    @classmethod
    def apply_preset(cls, preset_name: str, manager: MultiModelManager):
        """Apply a preset configuration."""
        presets = {
            "fast": cls.FAST_DEVELOPMENT,
            "quality": cls.HIGH_QUALITY,
            "balanced": cls.BALANCED
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        preset = presets[preset_name]
        for agent_type, config in preset.items():
            manager.set_agent_config(agent_type, config)
        
        manager.save_configurations()
        logger.info(f"Applied '{preset_name}' preset configuration")