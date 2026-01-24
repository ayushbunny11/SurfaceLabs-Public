from typing import Dict, Optional
from google.adk.agents import LlmAgent

from app.utils.logget_setup import ai_logger


class AgentManager:
    """Manages the lifecycle of LLM agents."""
    
    def __init__(self):
        self._agents: Dict[str, LlmAgent] = {}
        ai_logger.debug("AgentManager initialized")

    def create(self, name: str, model: str, instruction: str, description: str, tools=None):
        """Create and register a new LLM agent."""
        ai_logger.debug(f"Creating agent '{name}' with model='{model}', tools_count={len(tools) if tools else 0}")
        
        try:
            agent = LlmAgent(
                name=name,
                description=description,
                model=model,
                instruction=instruction,
                tools=tools or [],
            )
            self._agents[name] = agent
            ai_logger.debug(f"Agent '{name}' created successfully (instruction_length={len(instruction)})")
            return agent
        except Exception as e:
            ai_logger.error(f"Failed to create agent '{name}': {str(e)}", exc_info=True)
            raise

    def update(self, name: str, **kwargs) -> Optional[LlmAgent]:
        """Update an existing agent's configuration."""
        agent = self._agents.get(name)
        if not agent:
            ai_logger.warning(f"Cannot update agent '{name}': agent not found in registry")
            return None

        updated_fields = []
        if "instruction" in kwargs:
            agent.instruction = kwargs["instruction"]
            updated_fields.append("instruction")
        if "tools" in kwargs:
            agent.tools = kwargs["tools"]
            updated_fields.append(f"tools({len(kwargs['tools'])})")
        if "model" in kwargs:
            agent.model = kwargs["model"]
            updated_fields.append(f"model({kwargs['model']})")

        ai_logger.debug(f"Agent '{name}' updated: {', '.join(updated_fields)}")
        return agent

    def delete(self, name: str):
        """Remove an agent from the registry."""
        if name in self._agents:
            self._agents.pop(name, None)
            ai_logger.debug(f"Agent '{name}' deleted from registry")
        else:
            ai_logger.warning(f"Cannot delete agent '{name}': agent not found in registry")

    def get(self, name: str) -> Optional[LlmAgent]:
        """Retrieve an agent by name."""
        agent = self._agents.get(name)
        if not agent:
            ai_logger.debug(f"Agent '{name}' not found in registry")
        return agent

    def list(self):
        """List all registered agent names."""
        agent_names = list(self._agents.keys())
        ai_logger.debug(f"Listing {len(agent_names)} registered agents: {agent_names}")
        return agent_names
