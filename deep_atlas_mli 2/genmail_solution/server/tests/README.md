# Tool Selection Testing with DeepEval

This test suite validates that the LLM correctly selects tools based on user inputs for email management operations.

## Setup

1. Install dependencies (from server directory):
```bash
uv sync --extra ai
```

2. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Running Tests

Run all tool selection tests:
```bash
cd server
uv run pytest tests/test_tool_selection.py -v
```

Run a specific test:
```bash
uv run pytest tests/test_tool_selection.py::test_list_unread_emails -v
```

Run with detailed output:
```bash
uv run pytest tests/test_tool_selection.py -v -s
```

## Test Coverage

The test suite includes 20+ test cases covering:

### Basic Tool Selection
- `test_list_unread_emails` - Filter for unread emails
- `test_list_emails_from_sender` - Filter by sender
- `test_get_thread_emails` - Filter by thread ID
- `test_get_inbox_stats` - Get statistics
- `test_get_threads_list` - List all threads
- `test_get_specific_email` - Get single email details

### CRUD Operations
- `test_create_new_email` - Create/send new email
- `test_mark_email_read` - Mark email as read
- `test_delete_email` - Delete email
- `test_reply_to_thread` - Reply to existing thread

### Complex Queries
- `test_complex_filter_combination` - Multiple filters (unread + sender)
- `test_recipient_filter` - Filter emails by recipient
- `test_ambiguous_search_query` - Semantic search handling
- `test_stat_summary_request` - Overview/summary requests
- `test_thread_count_query` - Thread metadata queries

### Edge Cases & Failures
- `test_empty_query` - Vague/minimal input
- `test_invalid_email_id_format` - Invalid ID formats
- `test_multi_action_request` - Multiple tools in one request
- `test_conversational_style_request` - Natural language
- `test_nonexistent_functionality` - Requests for unavailable features

## Test Metrics

Tests use DeepEval's `ToolCorrectnessMetric` which evaluates:
- **Tool Selection Accuracy** - Did the LLM select the right tool(s)?
- **Parameter Correctness** - Are tool inputs properly extracted?
- **Multi-tool Handling** - Can it handle multiple actions?

## Available Tools

The agent has access to these email management tools:

1. **list_emails** - List/filter emails (supports thread_id, is_read, sender, recipient)
2. **get_email** - Get single email by ID
3. **create_email** - Create new email or reply to thread
4. **mark_email_read** - Mark email as read
5. **delete_email** - Delete email by ID
6. **get_threads** - Get all threads with metadata
7. **get_stats** - Get inbox statistics
8. **search_emails_by_content** - Semantic search (conceptual tool)

## Expected Failures

Some tests are designed to expose edge cases:
- `test_ambiguous_search_query` - May select list_emails instead of search
- `test_nonexistent_functionality` - Tests graceful handling of unavailable features
- `test_multi_action_request` - Complex requests that might need clarification

## Interpreting Results

**PASS** - LLM selected correct tool(s) with appropriate parameters
**FAIL** - Wrong tool selected or missing required parameters

Look for patterns in failures:
- Does the LLM confuse similar tools (list_emails vs get_email)?
- Does it handle filters correctly?
- Does it extract email addresses and IDs accurately?
- Can it handle multi-step requests?

## Extending Tests

To add new test cases:

1. Create a test function with descriptive name
2. Define user input and expected behavior
3. Call `agent.select_tools(user_input)`
4. Create `LLMTestCase` with expected_tools
5. Assert using `ToolCorrectnessMetric`
6. Add specific assertions for parameters

Example:
```python
def test_your_scenario():
    user_input = "Your user request here"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=tool_uses,
        expected_tools=["tool_name"]
    )

    metric = ToolCorrectnessMetric()
    assert_test(test_case, [metric])

    # Additional assertions
    assert tool_uses[0]["input"].get("param") == "expected_value"
```

## Cost Considerations

Each test makes an API call to Anthropic's Claude. With 20 tests:
- Model: claude-3-5-sonnet-20241022
- ~1000 tokens per test (input + output)
- ~20,000 total tokens ≈ $0.06 per full test run

Run frequently during development but be mindful of API costs.
