"""Multi-agent containment and tool delegation security policies."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ContainmentPolicy:
    """Security policy bounding agent capability escalation and delegation."""

    policy_id: str
    max_delegation_depth: int = 1
    allowed_subagent_roles: tuple[str, ...] = ("worker", "analyst")
    prohibited_capabilities: tuple[str, ...] = (
        "spawn_shell",
        "modify_system_permissions",
        "network_listen",
    )
    allow_privilege_escalation: bool = False
    metadata: dict[str, str] = field(default_factory=dict)
