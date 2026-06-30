"""
DeepEval Test Suite for MCP Task Manager - STUDENT VERSION

This test suite validates:
1. Tool selection - Does the agent choose the right tool for the task?
2. Tool invocation - Are tools called with correct parameters?
3. Response quality - Are responses helpful, accurate, and contextual?
4. Conversation management - Is history maintained correctly?
5. Error handling - Does the system handle failures gracefully?

Installation:
pip install deepeval pytest

Usage:
pytest test_mcp_system_STUDENT.py -v
"""

import pytest
import asyncio
from typing import List, Dict, Any
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextualRelevancyMetric,
    ToolCorrectnessMetric,
)
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
import json


# FILL_THIS_IN: Update these paths to match your environment
MCP_SERVER_CONFIG = {
    "task-manager": {
        "transport": "stdio",
        "command": "/path/to/venv/bin/python",  # Path to your Python interpreter
        "args": ["/path/to/task_mcp_server.py"],  # Path to your MCP server file
    }
}


class MCPTestHelper:
    """Helper class to set up and interact with the MCP system"""

    def __init__(self):
        self.client = None
        self.agent = None
        self.tools = None
        self.model = None

    async def setup(self):
        """Initialize the MCP client and agent"""
        self.client = MultiServerMCPClient(MCP_SERVER_CONFIG)
        self.tools = await self.client.get_tools()
        self.model = init_chat_model("gemma4:e4b-it-q4_k_M", model_provider="ollama")
        self.agent = create_agent(self.model, self.tools)

    async def invoke(self, messages: List) -> Dict[str, Any]:
        """Invoke the agent with a message history"""
        response = await self.agent.ainvoke({"messages": messages})
        return response

    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.close()


@pytest.fixture(scope="module")
async def mcp_helper():
    """Pytest fixture to set up and tear down MCP system"""
    helper = MCPTestHelper()
    await helper.setup()
    yield helper
    await helper.cleanup()


# ============================================================================
# Tool Selection Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_task_tool_selection(mcp_helper):
    """Test that the agent selects create_task for task creation requests"""

    # FILL_THIS_IN: Create a message asking to create a task
    # Hint: Use HumanMessage with content like "Create a task to buy groceries"
    messages = None

    response = await mcp_helper.invoke(messages)

    # Extract tool calls from response
    tool_calls = []
    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend([call["name"] for call in msg.tool_calls])

    # FILL_THIS_IN: Assert that "create_task" is in the tool_calls list
    # Hint: Use assert with "in" operator and provide a helpful error message
    pass


@pytest.mark.asyncio
async def test_get_tasks_tool_selection(mcp_helper):
    """Test that the agent selects get_tasks for listing requests"""

    messages = [HumanMessage(content="Show me all my tasks")]
    response = await mcp_helper.invoke(messages)

    # FILL_THIS_IN: Extract tool calls from the response
    # Hint: Loop through response["messages"] and collect tool call names
    tool_calls = []

    assert (
        "get_tasks" in tool_calls
    ), f"Expected get_tasks to be called, but got: {tool_calls}"


@pytest.mark.asyncio
async def test_update_task_tool_selection(mcp_helper):
    """Test that the agent selects update_task for modification requests"""

    # First create a task
    create_messages = [HumanMessage(content="Create a task called 'Test Task'")]
    create_response = await mcp_helper.invoke(create_messages)

    # FILL_THIS_IN: Build an update_messages list that includes:
    # 1. The original HumanMessage
    # 2. All messages from create_response
    # 3. A new HumanMessage asking to mark the task as completed
    # Hint: Use list concatenation or .extend()
    update_messages = None

    update_response = await mcp_helper.invoke(update_messages)

    tool_calls = []
    if "messages" in update_response:
        for msg in update_response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend([call["name"] for call in msg.tool_calls])

    assert (
        "update_task" in tool_calls
    ), f"Expected update_task to be called, but got: {tool_calls}"


@pytest.mark.asyncio
async def test_delete_task_tool_selection(mcp_helper):
    """Test that the agent selects delete_task for deletion requests"""

    # First create a task
    create_messages = [HumanMessage(content="Create a task to delete me")]
    create_response = await mcp_helper.invoke(create_messages)

    # Then delete it
    delete_messages = [
        HumanMessage(content="Create a task to delete me"),
        *create_response["messages"],
        HumanMessage(content="Delete the task about deleting"),
    ]
    delete_response = await mcp_helper.invoke(delete_messages)

    tool_calls = []
    if "messages" in delete_response:
        for msg in delete_response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend([call["name"] for call in msg.tool_calls])

    # FILL_THIS_IN: Assert that delete_task was called
    pass


# ============================================================================
# Tool Parameter Correctness Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_task_parameters():
    """Test that create_task is called with correct parameters"""

    helper = MCPTestHelper()
    await helper.setup()

    messages = [
        HumanMessage(
            content="Create a task titled 'Buy milk' with description 'Get 2% milk from store'"
        )
    ]
    response = await helper.invoke(messages)

    # Extract tool call parameters
    tool_calls = []
    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

    # FILL_THIS_IN: Find the create_task call in tool_calls
    # Hint: Use a list comprehension or next() with a generator expression
    # Look for calls where call["name"] == "create_task"
    create_call = None

    assert create_call is not None, "create_task was not called"

    # Check parameters
    args = create_call.get("args", {})
    assert "title" in args, "title parameter missing"
    assert (
        "Buy milk" in args["title"]
    ), f"Expected 'Buy milk' in title, got: {args['title']}"

    await helper.cleanup()


@pytest.mark.asyncio
async def test_update_task_parameters():
    """Test that update_task is called with correct parameters"""

    helper = MCPTestHelper()
    await helper.setup()

    # Create a task first
    create_messages = [HumanMessage(content="Create a task called 'Exercise'")]
    create_response = await helper.invoke(create_messages)

    # Update it
    update_messages = [
        HumanMessage(content="Create a task called 'Exercise'"),
        *create_response["messages"],
        HumanMessage(content="Mark the Exercise task as completed"),
    ]
    update_response = await helper.invoke(update_messages)

    # Extract tool calls
    tool_calls = []
    if "messages" in update_response:
        for msg in update_response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend(msg.tool_calls)

    # Find update_task call
    update_call = next(
        (call for call in tool_calls if call["name"] == "update_task"), None
    )
    assert update_call is not None, "update_task was not called"

    # FILL_THIS_IN: Check that the parameters contain "completed"
    # and that its value is True
    # Hint: Get args from update_call, then check args["completed"]
    args = update_call.get("args", {})
    # Add your assertions here

    await helper.cleanup()


# ============================================================================
# DeepEval Metric Tests
# ============================================================================


@pytest.mark.asyncio
async def test_answer_relevancy():
    """Test that agent responses are relevant to user queries"""

    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="What tasks do I have?")]
    response = await helper.invoke(messages)

    # FILL_THIS_IN: Extract the assistant's response from the messages
    # Hint: Loop through response["messages"] and find the AIMessage
    # Then get its content attribute
    assistant_response = ""

    # Create test case
    test_case = LLMTestCase(
        input="What tasks do I have?",
        actual_output=assistant_response,
        retrieval_context=["User is asking to see their task list"],
    )

    # FILL_THIS_IN: Create an AnswerRelevancyMetric with threshold=0.7
    # Then use assert_test with the test_case and metric
    # Hint: metric = AnswerRelevancyMetric(threshold=0.7)
    #       assert_test(test_case, [metric])
    pass

    await helper.cleanup()


@pytest.mark.asyncio
async def test_faithfulness_to_tool_results():
    """Test that agent responses are faithful to tool results"""

    helper = MCPTestHelper()
    await helper.setup()

    # Create a specific task
    messages = [
        HumanMessage(
            content="Create a task titled 'Test Faithfulness' with description 'This is a test'"
        )
    ]
    response = await helper.invoke(messages)

    # Extract assistant response and context
    assistant_response = ""
    retrieval_context = []

    if "messages" in response:
        for msg in response["messages"]:
            # Get tool results as context
            if hasattr(msg, "tool_calls"):
                retrieval_context.append(f"Tool calls: {msg.tool_calls}")
            if hasattr(msg, "content") and isinstance(msg, AIMessage):
                assistant_response = msg.content

    # Create test case
    test_case = LLMTestCase(
        input="Create a task titled 'Test Faithfulness' with description 'This is a test'",
        actual_output=assistant_response,
        retrieval_context=retrieval_context,
    )

    # Test faithfulness
    metric = FaithfulnessMetric(threshold=0.7)
    assert_test(test_case, [metric])

    await helper.cleanup()


# ============================================================================
# Conversation Management Tests
# ============================================================================


@pytest.mark.asyncio
async def test_conversation_continuity():
    """Test that the agent maintains context across multiple turns"""

    helper = MCPTestHelper()
    await helper.setup()

    # Turn 1: Create a task
    messages = [HumanMessage(content="Create a task to water plants")]
    response1 = await helper.invoke(messages)

    # FILL_THIS_IN: Add response1's messages to the messages list
    # Hint: Use messages.extend(response1["messages"])

    # Turn 2: Reference previous task (requires context)
    messages.append(HumanMessage(content="Actually, mark that task as completed"))
    response2 = await helper.invoke(messages)

    # Check that update_task was called (proving context was maintained)
    tool_calls = []
    if "messages" in response2:
        for msg in response2["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls.extend([call["name"] for call in msg.tool_calls])

    assert (
        "update_task" in tool_calls
    ), "Agent failed to maintain context and update the previously created task"

    await helper.cleanup()


@pytest.mark.asyncio
async def test_multi_turn_task_creation():
    """Test creating multiple tasks in a conversation"""

    helper = MCPTestHelper()
    await helper.setup()

    messages = []

    # Create first task
    messages.append(HumanMessage(content="Create a task to buy eggs"))
    response1 = await helper.invoke(messages)
    messages.extend(response1["messages"])

    # Create second task
    messages.append(HumanMessage(content="Also create a task to buy bread"))
    response2 = await helper.invoke(messages)
    messages.extend(response2["messages"])

    # FILL_THIS_IN: Add a HumanMessage asking to list all tasks
    # Then invoke the agent to get response3
    # Hint: messages.append(HumanMessage(content="Show me all my tasks"))
    #       response3 = await helper.invoke(messages)

    # Extract final response
    assistant_response = ""
    if "messages" in response3:
        for msg in response3["messages"]:
            if isinstance(msg, AIMessage):
                assistant_response = msg.content

    # Both tasks should be mentioned
    assert "eggs" in assistant_response.lower(), "First task not found in task list"
    assert "bread" in assistant_response.lower(), "Second task not found in task list"

    await helper.cleanup()


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_task_id_handling():
    """Test that the agent handles invalid task IDs gracefully"""

    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="Delete the task with ID 'nonexistent-id'")]
    response = await helper.invoke(messages)

    # Extract assistant response
    assistant_response = ""
    if "messages" in response:
        for msg in response["messages"]:
            if isinstance(msg, AIMessage):
                assistant_response = msg.content

    # FILL_THIS_IN: Assert that the response contains error-related words
    # Hint: Use "any(word in assistant_response.lower() for word in [list of error words])"
    # Check for words like: "not found", "doesn't exist", "couldn't find", "error"
    pass

    await helper.cleanup()


@pytest.mark.asyncio
async def test_ambiguous_request_handling():
    """Test that the agent handles ambiguous requests appropriately"""

    helper = MCPTestHelper()
    await helper.setup()

    # Create multiple tasks
    messages = [HumanMessage(content="Create a task to clean kitchen")]
    response1 = await helper.invoke(messages)
    messages.extend(response1["messages"])

    messages.append(HumanMessage(content="Create a task to clean bathroom"))
    response2 = await helper.invoke(messages)
    messages.extend(response2["messages"])

    # Make ambiguous request
    messages.append(HumanMessage(content="Delete the cleaning task"))
    response3 = await helper.invoke(messages)

    # Extract assistant response
    assistant_response = ""
    if "messages" in response3:
        for msg in response3["messages"]:
            if isinstance(msg, AIMessage):
                assistant_response = msg.content

    # Agent should ask for clarification or list options
    assert any(
        word in assistant_response.lower()
        for word in ["which", "clarify", "both", "kitchen", "bathroom"]
    ), f"Agent did not handle ambiguous request appropriately. Response: {assistant_response}"

    await helper.cleanup()


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_complete_task_workflow():
    """Test a complete workflow: create, list, update, delete"""

    helper = MCPTestHelper()
    await helper.setup()

    messages = []

    # Step 1: Create
    messages.append(HumanMessage(content="Create a task to test workflow"))
    response1 = await helper.invoke(messages)
    messages.extend(response1["messages"])

    # Step 2: List
    messages.append(HumanMessage(content="Show my tasks"))
    response2 = await helper.invoke(messages)
    messages.extend(response2["messages"])

    # Step 3: Update
    messages.append(HumanMessage(content="Mark the workflow task as completed"))
    response3 = await helper.invoke(messages)
    messages.extend(response3["messages"])

    # Step 4: Delete
    messages.append(HumanMessage(content="Delete the workflow task"))
    response4 = await helper.invoke(messages)

    # FILL_THIS_IN: Extract all tool calls from all four responses
    # Hint: Create an empty list, then for each response, extract tool_calls
    # from response["messages"] and extend your list
    all_tool_calls = []

    # Verify all tools were called
    assert "create_task" in all_tool_calls, "create_task was not called in workflow"
    assert "get_tasks" in all_tool_calls, "get_tasks was not called in workflow"
    assert "update_task" in all_tool_calls, "update_task was not called in workflow"
    assert "delete_task" in all_tool_calls, "delete_task was not called in workflow"

    await helper.cleanup()


# ============================================================================
# Custom Tool Correctness Metric
# ============================================================================


class MCPToolCorrectnessMetric(ToolCorrectnessMetric):
    """Custom metric to evaluate if the correct MCP tool was selected"""

    def __init__(self, expected_tool: str, threshold: float = 1.0):
        super().__init__(threshold=threshold)
        self.expected_tool = expected_tool

    async def a_measure(self, test_case: LLMTestCase) -> float:
        # Extract actual tools called from test case
        actual_tools = test_case.actual_output.get("tools_called", [])

        # FILL_THIS_IN: Set self.score and self.success based on whether
        # self.expected_tool is in actual_tools
        # If correct: self.score = 1.0, self.success = True
        # If wrong: self.score = 0.0, self.success = False
        # Also set self.reason with an appropriate message
        pass

        return self.score


@pytest.mark.asyncio
async def test_tool_correctness_metric():
    """Test using custom tool correctness metric"""

    helper = MCPTestHelper()
    await helper.setup()

    messages = [HumanMessage(content="Create a task to buy coffee")]
    response = await helper.invoke(messages)

    # Extract tools called
    tools_called = []
    if "messages" in response:
        for msg in response["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tools_called.extend([call["name"] for call in msg.tool_calls])

    # Create test case with tools called
    test_case = LLMTestCase(
        input="Create a task to buy coffee",
        actual_output={"tools_called": tools_called},
        expected_output={"tools_called": ["create_task"]},
    )

    # FILL_THIS_IN: Create an MCPToolCorrectnessMetric expecting "create_task"
    # Then use assert_test with test_case and the metric
    pass

    await helper.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
