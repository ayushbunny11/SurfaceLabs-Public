from typing import Dict, Optional
from google.adk.agents import Agent

class AgentManager:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def create(self, name: str, model: str, instruction: str, tools=None):
        agent = Agent(
            name=name,
            model=model,
            instruction=instruction,
            tools=tools or []
        )
        self._agents[name] = agent
        return agent

    def update(self, name: str, **kwargs) -> Optional[Agent]:
        agent = self._agents.get(name)
        if not agent:
            return None

        if "instruction" in kwargs:
            agent.instruction = kwargs["instruction"]
        if "tools" in kwargs:
            agent.tools = kwargs["tools"]
        if "model" in kwargs:
            agent.model = kwargs["model"]

        return agent

    def delete(self, name: str):
        self._agents.pop(name, None)

    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def list(self):
        return list(self._agents.keys())
