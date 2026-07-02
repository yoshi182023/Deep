"""
Manual tests for tool selection - run with: uv run python tests/test_tool_manual.py
"""
from agents.tool_agent import ToolSelectionAgent

def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return value

def run_test(name, user_input, expected_tool, expected_params=None):
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Input: {user_input}")
    print(f"Expected tool: {expected_tool}")

    agent = ToolSelectionAgent()
    tools = agent.select_tools(user_input)

    print(f"Selected tools: {tools}")

    if not tools:
        print("❌ FAIL: No tools selected")
        return False

    if tools[0]["name"] != expected_tool:
        print(f"❌ FAIL: Expected {expected_tool}, got {tools[0]['name']}")
        return False

    if expected_params:
        for key, expected_value in expected_params.items():
            actual_value = tools[0]["input"].get(key)
            if key == "is_read":
                actual_value = normalize_bool(actual_value)
                expected_value = normalize_bool(expected_value)
            if actual_value != expected_value:
                print(f"❌ FAIL: Expected {key}={expected_value}, got {actual_value}")
                return False

    print("✅ PASS")
    return True

if __name__ == "__main__":
    print("Running Tool Selection Manual Tests")
    print("="*60)

    tests = [
        ("List unread emails", "show unread emails", "list_emails", {"is_read": False}),
        ("Search keyword", "search Phoenix", "search_emails_by_content", {"query": "Phoenix"}),
        ("Search with filter", "search Phoenix in unread emails", "search_emails_by_content", {"is_read": False}),
        ("Get stats", "how many unread emails do I have", "get_stats", {}),
        ("Get threads", "show all threads", "get_threads", {}),
        ("Mark unread", "mark email 123 as unread", "mark_email_unread", {"email_id": "123"}),
    ]

    passed = 0
    failed = 0

    for test in tests:
        if run_test(*test):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")
