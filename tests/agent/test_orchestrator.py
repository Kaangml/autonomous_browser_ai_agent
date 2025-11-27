"""Tests for Orchestrator with mock LLM."""

import pytest
import json

from agent.orchestrator import Orchestrator, OrchestratorState, TaskStatus, TaskResult
from llm.mock_provider import MockLLMProvider


@pytest.fixture
def mock_planner_response():
    """Mock planner LLM response."""
    return json.dumps({
        "steps": [
            {"step": 1, "type": "navigate", "args": {"url": "https://example.com"}},
            {"step": 2, "type": "extract_text", "args": {"selector": "h1"}},
        ],
        "strategy": "Navigate and extract title",
    })


@pytest.fixture
def mock_evaluator_success():
    """Mock evaluator success response."""
    return json.dumps({
        "success": True,
        "task_complete": False,
        "should_replan": False,
    })


@pytest.fixture
def mock_evaluator_complete():
    """Mock evaluator task complete response."""
    return json.dumps({
        "success": True,
        "task_complete": True,
        "result": "Successfully extracted data",
    })


def test_orchestrator_initialization():
    """Test orchestrator initializes correctly."""
    mock_llm = MockLLMProvider()
    orchestrator = Orchestrator(llm=mock_llm)
    
    assert orchestrator.state is None  # No task started yet
    assert orchestrator.max_retries == 3
    assert orchestrator.max_steps == 20


def test_task_status_values():
    """Test TaskStatus enum values."""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.PLANNING.value == "planning"
    assert TaskStatus.EXECUTING.value == "executing"
    assert TaskStatus.EVALUATING.value == "evaluating"
    assert TaskStatus.REPLANNING.value == "replanning"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"


def test_task_result_dataclass():
    """Test TaskResult dataclass."""
    result = TaskResult(
        success=True,
        task="Test task",
        steps_executed=3,
        final_result="Done",
    )
    
    assert result.success is True
    assert result.task == "Test task"
    assert result.steps_executed == 3
    assert result.execution_log == []
    assert result.error is None


def test_orchestrator_state_dataclass():
    """Test OrchestratorState dataclass."""
    state = OrchestratorState(task="Test task")
    
    assert state.task == "Test task"
    assert state.status == TaskStatus.PENDING
    assert state.current_plan == []
    assert state.executed_steps == []
    assert state.current_step_index == 0


def test_orchestrator_custom_config():
    """Test orchestrator with custom config."""
    mock_llm = MockLLMProvider()
    orchestrator = Orchestrator(
        llm=mock_llm,
        max_retries=5,
        max_steps=50,
    )
    
    assert orchestrator.max_retries == 5
    assert orchestrator.max_steps == 50


@pytest.mark.asyncio
async def test_orchestrator_creates_state_on_execute():
    """Test orchestrator creates state when executing task."""
    mock_llm = MockLLMProvider(responses=[
        # Empty plan to fail fast
        json.dumps({"steps": [], "strategy": "empty"}),
    ])
    
    orchestrator = Orchestrator(llm=mock_llm)
    
    # Before execution
    assert orchestrator.state is None
    
    # Execute - will fail because no planner set
    result = await orchestrator.execute_task("Go to example.com")
    
    # After execution
    assert orchestrator.state is not None
    assert orchestrator.state.task == "Go to example.com"


def test_task_result_with_error():
    """Test TaskResult with error."""
    result = TaskResult(
        success=False,
        task="Failed task",
        steps_executed=1,
        final_result=None,
        error="Connection timeout",
    )
    
    assert result.success is False
    assert result.error == "Connection timeout"


def test_orchestrator_state_with_plan():
    """Test OrchestratorState with plan."""
    state = OrchestratorState(
        task="Search for Python",
        status=TaskStatus.EXECUTING,
        current_plan=[
            {"type": "navigate", "args": {"url": "https://google.com"}},
            {"type": "input", "args": {"selector": "input", "text": "Python"}},
        ],
        current_step_index=1,
    )
    
    assert state.status == TaskStatus.EXECUTING
    assert len(state.current_plan) == 2
    assert state.current_step_index == 1


class TestOrchestratorIntegration:
    """Integration tests for orchestrator."""
    
    @pytest.mark.asyncio
    async def test_orchestrator_with_all_agents(self):
        """Test orchestrator initializes with all agents."""
        from agent.planner import PlannerAgent
        from agent.executor import ExecutorAgent
        from agent.evaluator import EvaluatorAgent
        
        mock_llm = MockLLMProvider()
        
        planner = PlannerAgent(llm=mock_llm)
        executor = ExecutorAgent(llm=mock_llm)
        evaluator = EvaluatorAgent(llm=mock_llm)
        
        orchestrator = Orchestrator(
            llm=mock_llm,
            planner=planner,
            executor=executor,
            evaluator=evaluator,
        )
        
        assert orchestrator.planner is planner
        assert orchestrator.executor is executor
        assert orchestrator.evaluator is evaluator
    
    @pytest.mark.asyncio
    async def test_planner_integration(self):
        """Test planner creates valid plan."""
        from agent.planner import PlannerAgent
        
        plan_response = json.dumps({
            "goal_analysis": "Navigate and extract",
            "lookahead": "After navigation, extract content",
            "steps": [
                {"step_number": 1, "action": "goto", "value": "https://example.com", "reason": "Navigate"},
                {"step_number": 2, "action": "extract_text", "selector": "h1", "reason": "Get title"},
            ],
            "success_criteria": "Title extracted",
        })
        
        mock_llm = MockLLMProvider(responses=[plan_response])
        planner = PlannerAgent(llm=mock_llm)
        
        plan = await planner.plan(task="Get title from example.com")
        
        assert len(plan) == 2
        assert plan[0]["type"] == "goto"
        assert plan[0]["args"]["url"] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_evaluator_integration(self):
        """Test evaluator evaluates step correctly."""
        from agent.evaluator import EvaluatorAgent
        
        evaluator = EvaluatorAgent(llm=None)  # No LLM for simple evaluation
        
        evaluation = await evaluator.evaluate(
            step={"type": "click", "args": {"selector": "#btn"}},
            result={"ok": True, "result": "clicked"},
            remaining_steps=2,
        )
        
        assert evaluation["success"] is True
        assert evaluation["task_complete"] is False
