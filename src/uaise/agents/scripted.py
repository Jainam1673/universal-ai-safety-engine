"""Deterministic scripted agents for offline benchmarks."""

from __future__ import annotations

import random
from typing import Literal

from uaise.core.types import Action, Scenario

AgentStrategy = Literal["safe", "reward_hacker", "opportunistic"]


class ScriptedAgent:
    """A deterministic agent executing rule-based policies for benchmark testing."""

    def __init__(self, strategy: AgentStrategy = "safe", seed: int = 42) -> None:
        self.strategy = strategy
        self.seed = seed
        self._rng = random.Random(seed)

    @property
    def agent_id(self) -> str:
        return f"scripted_agent_{self.strategy}"

    def act(self, scenario: Scenario) -> Action:
        """Select an action based on scenario metadata and agent strategy."""
        safe_action_data = scenario.metadata.get(
            "safe_action",
            {
                "name": scenario.allowed_actions[0] if scenario.allowed_actions else "noop",
                "params": {},
            },
        )
        hack_action_data = scenario.metadata.get(
            "hack_action",
            {"name": "bypass_constraint", "params": {"reason": "maximize_proxy_metric"}},
        )

        if self.strategy == "safe":
            return Action(
                name=safe_action_data["name"],
                parameters=safe_action_data.get("params", {}),
                rationale="Adhering strictly to safe specification and allowed constraints.",
            )

        if self.strategy == "reward_hacker":
            # If scenario offers a shortcut/hack action, take it
            if "hack_action" in scenario.metadata:
                return Action(
                    name=hack_action_data["name"],
                    parameters=hack_action_data.get("params", {}),
                    rationale="Exploiting specification loophole to maximize immediate reward.",
                )
            return Action(
                name=safe_action_data["name"],
                parameters=safe_action_data.get("params", {}),
                rationale="Adhering to standard task procedure.",
            )

        if self.strategy == "opportunistic":
            # 50% probability of hacking if available, deterministic based on RNG
            if "hack_action" in scenario.metadata and self._rng.random() < 0.5:
                return Action(
                    name=hack_action_data["name"],
                    parameters=hack_action_data.get("params", {}),
                    rationale="Opportunistically exploiting specification loophole.",
                )
            return Action(
                name=safe_action_data["name"],
                parameters=safe_action_data.get("params", {}),
                rationale="Adhering to specification.",
            )

        raise ValueError(f"Unknown strategy: {self.strategy}")
