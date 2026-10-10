"""Tests for LLMAgent and LLMJudgeMonitor."""

import json

from uaise.agents.llm_agent import LLMAgent
from uaise.core.types import Action, Scenario, ViolationType
from uaise.models.mock import MockModel
from uaise.monitors.llm_judge import LLMJudgeMonitor


def _make_scenario() -> Scenario:
    return Scenario(
        id="sc_01",
        name="Test Scenario",
        description="A test scenario",
        intended_task="Optimize code",
        allowed_actions=["refactor_code"],
        is_violation=False,
        violation_type=ViolationType.NONE,
    )


def test_llm_agent_json_parsing():
    mock = MockModel(
        responses=[
            json.dumps(
                {
                    "action": "refactor_code",
                    "rationale": "optimized loops",
                    "parameters": {"level": 2},
                }
            )
        ]
    )
    agent = LLMAgent(model=mock)
    action = agent.act(_make_scenario())

    assert action.name == "refactor_code"
    assert action.rationale == "optimized loops"
    assert action.parameters["level"] == 2


def test_llm_agent_markdown_code_block_parsing():
    markdown_wrapped = (
        "```json\n"
        + json.dumps({"action": "refactor_code", "rationale": "inside markdown"})
        + "\n```"
    )
    mock = MockModel(responses=[markdown_wrapped])
    agent = LLMAgent(model=mock)
    action = agent.act(_make_scenario())

    assert action.name == "refactor_code"
    assert action.rationale == "inside markdown"


def test_llm_agent_malformed_fallback():
    mock = MockModel(responses=["I cannot output JSON, sorry!"])
    agent = LLMAgent(model=mock)
    action = agent.act(_make_scenario())

    assert action.name == "malformed_model_output"
    assert "Failed to parse" in action.rationale


def test_llm_judge_monitor_evaluation():
    mock = MockModel(
        responses=[
            json.dumps(
                {
                    "is_flagged": True,
                    "risk_score": 0.95,
                    "rationale": "Action bypasses safety assertion.",
                }
            )
        ]
    )
    judge = LLMJudgeMonitor(model=mock)
    dec = judge.evaluate(Action(name="delete_tests"), _make_scenario())

    assert dec.is_flagged
    assert dec.risk_score == 0.95
    assert dec.rationale == "Action bypasses safety assertion."
    assert dec.triggered_rule == "llm_judge_assessment"


def test_llm_judge_monitor_malformed_fallback():
    mock = MockModel(responses=["Not a valid json response from judge"])
    judge = LLMJudgeMonitor(model=mock)
    dec = judge.evaluate(Action(name="act"), _make_scenario())

    assert dec.is_flagged
    assert dec.risk_score == 0.5
    assert "Malformed judge JSON" in dec.rationale
