import sys
import json
import pytest
import pytest_asyncio
from typing import List, Dict, Any

from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ToolCorrectnessMetric,
)
from deepeval.models import DeepEvalBaseLLM

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage

import ollama as _ollama


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MCP_SERVER_CONFIG = {
    "task-manager": {
        "transport": "stdio",
        "command": sys.executable
        "args": ["mcp_server/task_mcp_server.solution.py"],
    }
}

JUDGE_MODEL = "gemma4:e4b-it-q4_k_M"


# ---------------------------------------------------------------------------
# Local Ollama judge — prevents DeepEval from calling OpenAI
# ---------------------------------------------------------------------------


class OllamaJudge(DeepEvalBaseLLM):
    """Thin DeepEvalBaseLLM wrapper around a local Ollama model."""

    def __init__(self, model: str = JUDGE_MODEL):
        self.model_name = model

    def load_model(self):
        return self.model_name

    def generate(self, prompt: str) -> str:
        response = _ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self.model_name


local_judge = OllamaJudge()


# ---------------------------------------------------------------------------
# MCP helper
# ---------------------------------------------------------------------------


class MCPTestHelper:
    """Owns the agent and MCP client for the duration of a test."""

    def __init__(self):
        self.client = None
        self.agent = None
        self.tools = None
        self.model = None

    async def setup(self):
        self.client = MultiServerMCPClient(MCP_SERVER_CONFIG)
        self.tools = await self.client.get_tools()
        self.model = init_chat_model("gemma4:e4b-it-q4_k_M", model_provider="ollama")
        self.agent = create_agent(self.model, self.tools)

    async def invoke(self, messages: List) -> Dict[str, Any]:
        return await self.agent.ainvoke({"messages": messages})

    async def cleanup(self):
        pass

@pytest_asyncio.fixture(scope="module")
async def mcp_helper():
    helper = MCPTestHelper()
    await helper.setup()
    yield helper
    await helper.cleanup()


# ============================================================================
# Tool Selection Tests
# ============================================================================


async def test_create_task_tool_selection(mcp_helper):
    """Agent should choose create_task for task-creation requests."""
    messages = [HumanMessage(content="Create a task to buy groceries")]
    response = await mcp_helper.invoke(messages)

    tool_calls = _extract_tool_names(response)
    assert "create_task" in tool_calls, f"Expected create_task, got: {tool_calls}"


async def test_get_tasks_tool_selection(mcp_helper):
    """Agent should choose get_tasks for listing requests."""
    messages = [HumanMessage(content="Show me all my tasks")]
    response = await mcp_helper.invoke(messages)

    tool_calls = _extract_tool_names(response)
    assert "get_tasks" in tool_calls, f"Expected get_tasks, got: {tool_calls}"


async def test_update_task_tool_selection(mcp_helper):
    """Agent should choose update_task for modification requests."""
    create_messages = [HumanMessage(content="Create a task called 'Test Task'")]
    create_response = await mcp_helper.invoke(create_messages)

    update_messages = [
        HumanMessage(content="Create a task called 'Test Task'"),
        *create_response["messages"],
        HumanMessage(content="Mark the Test Task as completed"),
    ]
    update_response = await mcp_helper.invoke(update_messages)

    tool_calls = _extract_tool_names(update_response)
    assert "update_task" in tool_calls, f"Expected update_task, got: {tool_calls}"


async def test_delete_task_tool_selection(mcp_helper):
    """Agent should choose delete_task for deletion requests."""
    create_messages = [HumanMessage(content="Create a task to delete me")]
    create_response = await mcp_helper.invoke(create_messages)

    delete_messages = [
        HumanMessage(content="Create a task to delete me"),
        *create_response["messages"],
        HumanMessage(content="Delete the task about deleting"),
    ]
    delete_response = await mcp_helper.invoke(delete_messages)

    tool_calls = _extract_tool_names(delete_response)
    assert "delete_task" in tool_calls, f"Expected delete_task, got: {tool_calls}"


# ============================================================================
# Tool Parameter Correctness Tests
# ============================================================================


async def test_create_task_parameters():
    """create_task should be called with the title from the user message."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = [
        HumanMessage(
            content="Create a task titled 'Buy milk' with description 'Get 2% milk from store'"
        )
    ]
    response = await helper.invoke(messages)

    tool_calls = _extract_tool_call_objects(response)
    create_call = next((c for c in tool_calls if c["name"] == "create_task"), None)

    assert create_call is not None, "create_task was not called"
    args = create_call.get("args", {})
    assert "title" in args, "title parameter missing"
    assert (
        "Buy milk" in args["title"]
    ), f"Expected 'Buy milk' in title, got: {args['title']}"

    await helper.cleanup()


async def test_update_task_parameters():
    """update_task should set completed=True when asked to mark a task done."""
    helper = MCPTestHelper()
    await helper.setup()

    create_messages = [HumanMessage(content="Create a task called 'Exercise'")]
    create_response = await helper.invoke(create_messages)

    update_messages = [
        HumanMessage(content="Create a task called 'Exercise'"),
        *create_response["messages"],
        HumanMessage(content="Mark the Exercise task as completed"),
    ]
    update_response = await helper.invoke(update_messages)

    tool_calls = _extract_tool_call_objects(update_response)
    update_call = next((c for c in tool_calls if c["name"] == "update_task"), None)

    assert update_call is not None, "update_task was not called"
    args = update_call.get("args", {})
    assert "completed" in args, "completed parameter missing"
    assert (
        args["completed"] is True
    ), f"Expected completed=True, got: {args['completed']}"

    await helper.cleanup()


# ============================================================================
# DeepEval Metric Tests
# ============================================================================


async def test_answer_relevancy():
    """Agent responses should be relevant to the user's query."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="What tasks do I have?")]
    response = await helper.invoke(messages)

    assistant_response = _extract_last_ai_content(response)

    test_case = LLMTestCase(
        input="What tasks do I have?",
        actual_output=assistant_response,
        retrieval_context=["User is asking to see their task list"],
    )

    metric = AnswerRelevancyMetric(threshold=0.7, model=local_judge)
    assert_test(test_case, [metric])

    await helper.cleanup()


async def test_faithfulness_to_tool_results():
    """Agent responses should be faithful to what the tools actually returned."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = [
        HumanMessage(
            content="Create a task titled 'Test Faithfulness' with description 'This is a test'"
        )
    ]
    response = await helper.invoke(messages)

    assistant_response = ""
    retrieval_context = []

    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                retrieval_context.append(f"Tool calls: {msg.tool_calls}")
            if isinstance(msg, AIMessage) and msg.content:
                assistant_response = msg.content

    test_case = LLMTestCase(
        input="Create a task titled 'Test Faithfulness' with description 'This is a test'",
        actual_output=assistant_response,
        retrieval_context=retrieval_context,
    )

    metric = FaithfulnessMetric(threshold=0.7, model=local_judge)
    assert_test(test_case, [metric])

    await helper.cleanup()


# ============================================================================
# Conversation Management Tests
# ============================================================================


async def test_conversation_continuity():
    """Agent should track context across turns and update the right task."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="Create a task to water plants")]
    response1 = await helper.invoke(messages)

    messages.extend(response1["messages"])
    messages.append(HumanMessage(content="Actually, mark that task as completed"))
    response2 = await helper.invoke(messages)

    tool_calls = _extract_tool_names(response2)
    assert "update_task" in tool_calls, "Agent lost context and didn't update the task"

    await helper.cleanup()


async def test_multi_turn_task_creation():
    """Both tasks created across turns should appear in the final listing."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = []

    messages.append(HumanMessage(content="Create a task to buy eggs"))
    response1 = await helper.invoke(messages)
    messages.extend(response1["messages"])

    messages.append(HumanMessage(content="Also create a task to buy bread"))
    response2 = await helper.invoke(messages)
    messages.extend(response2["messages"])

    messages.append(HumanMessage(content="Show me all my tasks"))
    response3 = await helper.invoke(messages)

    assistant_response = _extract_last_ai_content(response3)
    assert "eggs" in assistant_response.lower(), "First task not in task list"
    assert "bread" in assistant_response.lower(), "Second task not in task list"

    await helper.cleanup()


# ============================================================================
# Error Handling Tests
# ============================================================================


async def test_invalid_task_id_handling():
    """Agent should surface a clear error for a non-existent task ID."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="Delete the task with ID 'nonexistent-id'")]
    response = await helper.invoke(messages)

    assistant_response = _extract_last_ai_content(response)
    assert any(
        word in assistant_response.lower()
        for word in ["not found", "doesn't exist", "couldn't find", "error"]
    ), f"Expected error message, got: {assistant_response}"

    await helper.cleanup()


async def test_ambiguous_request_handling():
    """Agent should ask for clarification when the request is ambiguous.

    NOTE: gemma4:e4b-it-q4_k_M may skip clarification and just delete one task. If this
    test is consistently flaky, switch to a larger model or soften the assertion
    to a pytest.warns / log warning instead of a hard failure.
    """
    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="Create a task to clean kitchen")]
    response1 = await helper.invoke(messages)
    messages.extend(response1["messages"])

    messages.append(HumanMessage(content="Create a task to clean bathroom"))
    response2 = await helper.invoke(messages)
    messages.extend(response2["messages"])

    messages.append(HumanMessage(content="Delete the cleaning task"))
    response3 = await helper.invoke(messages)

    assistant_response = _extract_last_ai_content(response3)
    assert any(
        word in assistant_response.lower()
        for word in ["which", "clarify", "both", "kitchen", "bathroom"]
    ), f"Agent did not clarify ambiguous request. Response: {assistant_response}"

    await helper.cleanup()


# ============================================================================
# Integration Tests
# ============================================================================


async def test_complete_task_workflow():
    """Full CRUD: create → list → update → delete, all four tools should fire."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = []

    messages.append(HumanMessage(content="Create a task to test workflow"))
    response1 = await helper.invoke(messages)
    messages.extend(response1["messages"])

    messages.append(HumanMessage(content="Show my tasks"))
    response2 = await helper.invoke(messages)
    messages.extend(response2["messages"])

    messages.append(HumanMessage(content="Mark the workflow task as completed"))
    response3 = await helper.invoke(messages)
    messages.extend(response3["messages"])

    messages.append(HumanMessage(content="Delete the workflow task"))
    response4 = await helper.invoke(messages)

    all_tool_calls = []
    for response in [response1, response2, response3, response4]:
        all_tool_calls.extend(_extract_tool_names(response))

    assert "create_task" in all_tool_calls, "create_task was not called"
    assert "get_tasks" in all_tool_calls, "get_tasks was not called"
    assert "update_task" in all_tool_calls, "update_task was not called"
    assert "delete_task" in all_tool_calls, "delete_task was not called"

    await helper.cleanup()


# ============================================================================
# Custom Tool Correctness Metric
# ============================================================================


class MCPToolCorrectnessMetric(ToolCorrectnessMetric):
    """Checks that a specific MCP tool was selected, without calling OpenAI."""

    def __init__(self, expected_tool: str, threshold: float = 1.0):
        # Pass model=local_judge so the parent never tries to load OpenAI.
        super().__init__(threshold=threshold, model=local_judge)
        self.expected_tool = expected_tool

    async def a_measure(self, test_case: LLMTestCase) -> float:
        # actual_output is a JSON string (LLMTestCase requires str, not dict).
        try:
            payload = json.loads(test_case.actual_output)
        except (json.JSONDecodeError, TypeError):
            payload = {}
        actual_tools = payload.get("tools_called", [])

        if self.expected_tool in actual_tools:
            self.score = 1.0
            self.success = True
            self.reason = f"Correct tool '{self.expected_tool}' was called"
        else:
            self.score = 0.0
            self.success = False
            self.reason = f"Expected '{self.expected_tool}' but got: {actual_tools}"

        return self.score


async def test_tool_correctness_metric():
    """Custom metric should pass when create_task is called."""
    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="Create a task to buy coffee")]
    response = await helper.invoke(messages)

    tools_called = _extract_tool_names(response)

    test_case = LLMTestCase(
        input="Create a task to buy coffee",
        actual_output=json.dumps({"tools_called": tools_called}),
        expected_output=json.dumps({"tools_called": ["create_task"]}),
    )

    metric = MCPToolCorrectnessMetric(expected_tool="create_task")
    assert_test(test_case, [metric])

    await helper.cleanup()


# ============================================================================
# Private helpers
# ============================================================================


def _extract_tool_names(response: Dict[str, Any]) -> List[str]:
    """Return a flat list of tool names called in a response."""
    names = []
    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                names.extend(call["name"] for call in msg.tool_calls)
    return names


def _extract_tool_call_objects(response: Dict[str, Any]) -> List[Dict]:
    """Return the raw tool-call dicts (name + args) from a response."""
    calls = []
    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                calls.extend(msg.tool_calls)
    return calls


def _extract_last_ai_content(response: Dict[str, Any]) -> str:
    """Return the content of the last AIMessage in a response."""
    if "messages" in response:
        for msg in reversed(response["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                return msg.content
    return ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
