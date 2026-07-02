import json
from agents.tool_agent import ToolSelectionAgent, EMAIL_TOOLS

try:
    from deepeval import assert_test
    from deepeval.metrics import ToolCorrectnessMetric
    from deepeval.test_case import LLMTestCase
    from deepeval.models.base_model import DeepEvalBaseLLM
    from langchain_ollama import ChatOllama

    class OllamaEvaluator(DeepEvalBaseLLM):
        def __init__(self, model="llama3.2"):
            self.model = ChatOllama(model=model, temperature=0)

        def load_model(self):
            return self.model

        def generate(self, prompt: str) -> str:
            return self.model.invoke(prompt).content

        async def a_generate(self, prompt: str) -> str:
            return self.generate(prompt)

        def get_model_name(self) -> str:
            return f"ollama/{self.model.model}"

    evaluator = OllamaEvaluator()

    def make_metric():
        return ToolCorrectnessMetric(model=evaluator)

except ImportError:
    def assert_test(*args, **kwargs): pass
    def make_metric(): return None
    class LLMTestCase:
        def __init__(self, **kwargs): pass

agent = ToolSelectionAgent()

def normalize_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return value

def test_list_unread_emails():
    """Should select list_emails with is_read=false"""
    user_input = "Show me all my unread emails"
    tool_uses = agent.select_tools(user_input)

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "list_emails"
    assert normalize_bool(tool_uses[0]["input"].get("is_read")) == False

def test_list_emails_from_sender():
    """Should select list_emails with sender filter"""
    user_input = "Get all emails from sarah.chen@acme.com"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["list_emails"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "list_emails"
    assert tool_uses[0]["input"].get("sender") == "sarah.chen@acme.com"

def test_get_thread_emails():
    """Should select list_emails with thread_id filter"""
    user_input = "Show me all messages in thread abc123"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["list_emails"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "list_emails"
    assert tool_uses[0]["input"].get("thread_id") == "abc123"

def test_get_inbox_stats():
    """Should select get_stats for inbox statistics"""
    user_input = "How many unread emails do I have?"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["get_stats"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "get_stats"

def test_get_threads_list():
    """Should select get_threads for thread overview"""
    user_input = "Show me all my email conversations"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["get_threads"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "get_threads"

def test_create_new_email():
    """Should select create_email with all required fields"""
    user_input = "Send an email to john@example.com with subject 'Meeting Tomorrow' and body 'See you at 3pm'"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["create_email"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "create_email"
    assert tool_uses[0]["input"].get("recipient") == "john@example.com"
    assert "Meeting Tomorrow" in tool_uses[0]["input"].get("subject", "")
    assert "3pm" in tool_uses[0]["input"].get("body", "")

def test_mark_email_read():
    """Should select mark_email_read with email ID"""
    user_input = "Mark email email_123 as read"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["mark_email_read"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "mark_email_read"
    assert tool_uses[0]["input"].get("email_id") == "email_123"

def test_delete_email():
    """Should select delete_email with email ID"""
    user_input = "Delete email with id email_456"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["delete_email"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "delete_email"
    assert tool_uses[0]["input"].get("email_id") == "email_456"

def test_get_specific_email():
    """Should select get_email with email ID"""
    user_input = "Show me the details of email email_789"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["get_email"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "get_email"
    assert tool_uses[0]["input"].get("email_id") == "email_789"

def test_complex_filter_combination():
    """Should select list_emails with multiple filters"""
    user_input = "Show unread emails from sarah.chen@acme.com"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["list_emails"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "list_emails"
    assert tool_uses[0]["input"].get("is_read") == False
    assert tool_uses[0]["input"].get("sender") == "sarah.chen@acme.com"

def test_ambiguous_search_query():
    """Edge case: Should handle semantic search (not in actual API)"""
    user_input = "Find emails about the Phoenix project"

    tool_uses = agent.select_tools(user_input)

    assert len(tool_uses) >= 1
    tool_names = [t["name"] for t in tool_uses]
    assert "search_emails_by_content" in tool_names or "list_emails" in tool_names

def test_reply_to_thread():
    """Should select create_email with thread_id for reply"""
    user_input = "Reply to thread thread_999 saying 'Thanks for the update'"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["create_email"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "create_email"
    assert tool_uses[0]["input"].get("thread_id") == "thread_999"

def test_empty_query():
    """Edge case: Empty or vague input should not crash"""
    user_input = "Show me emails"

    tool_uses = agent.select_tools(user_input)

    assert len(tool_uses) >= 1
    assert tool_uses[0]["name"] == "list_emails"

def test_invalid_email_id_format():
    """Edge case: Should still select correct tool despite invalid ID format"""
    user_input = "Delete email INVALID_ID_123!@#"

    tool_uses = agent.select_tools(user_input)

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "delete_email"

def test_multi_action_request():
    """Edge case: Multiple actions in one request - should select multiple tools"""
    user_input = "Mark email_111 as read and then delete email_222"

    tool_uses = agent.select_tools(user_input)

    tool_names = [t["name"] for t in tool_uses]
    assert "mark_email_read" in tool_names
    assert "delete_email" in tool_names
    assert len(tool_uses) == 2

def test_conversational_style_request():
    """Should handle natural conversational language"""
    user_input = "Hey, can you check if I have any new messages from my boss?"

    tool_uses = agent.select_tools(user_input)

    assert len(tool_uses) >= 1
    assert tool_uses[0]["name"] in ["list_emails", "get_stats"]

def test_stat_summary_request():
    """Should use get_stats for overview questions"""
    user_input = "Give me a summary of my inbox"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["get_stats"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

def test_thread_count_query():
    """Should use get_threads for conversation metadata"""
    user_input = "How many email threads do I have?"

    tool_uses = agent.select_tools(user_input)

    assert len(tool_uses) >= 1
    assert tool_uses[0]["name"] in ["get_threads", "get_stats"]

def test_recipient_filter():
    """Should select list_emails with recipient filter"""
    user_input = "Show emails I sent to alex.wong@vendor.com"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["list_emails"]
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "list_emails"
    assert tool_uses[0]["input"].get("recipient") == "alex.wong@vendor.com"

def test_nonexistent_functionality():
    """Edge case: Request for functionality not available in tools"""
    user_input = "Archive all emails from last year"

    tool_uses = agent.select_tools(user_input)

    if len(tool_uses) > 0:
        assert tool_uses[0]["name"] in ["list_emails", "delete_email"]


def test_simple_keyword_search():
    """Should select search_emails_by_content for keyword search"""
    user_input = "Find emails about Phoenix"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["search_emails_by_content"],
        tools=EMAIL_TOOLS
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "search_emails_by_content"
    assert "Phoenix" in tool_uses[0]["input"].get("query", "")


def test_search_with_read_filter():
    """Should select search_emails_by_content with is_read filter"""
    user_input = "Search Phoenix in unread emails"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["search_emails_by_content"],
        tools=EMAIL_TOOLS
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "search_emails_by_content"
    assert tool_uses[0]["input"].get("is_read") == False


def test_search_with_sender_filter():
    """Should select search_emails_by_content with sender filter"""
    user_input = "Find emails from Sarah mentioning launch"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["search_emails_by_content"],
        tools=EMAIL_TOOLS
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "search_emails_by_content"
    assert "launch" in tool_uses[0]["input"].get("query", "").lower()
    assert "sarah" in tool_uses[0]["input"].get("sender", "").lower()


def test_search_in_thread():
    """Should select search_emails_by_content with thread_id filter"""
    user_input = "Search timeline in thread phoenix-001"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["search_emails_by_content"],
        tools=EMAIL_TOOLS
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "search_emails_by_content"
    assert tool_uses[0]["input"].get("thread_id") == "phoenix-001"


def test_multi_word_search():
    """Should select search_emails_by_content for multi-word queries"""
    user_input = "Find emails about mobile offline sync"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["search_emails_by_content"],
        tools=EMAIL_TOOLS
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "search_emails_by_content"


def test_mark_email_unread():
    """Should select mark_email_unread with email ID"""
    user_input = "Mark email 123 as unread"

    tool_uses = agent.select_tools(user_input)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=json.dumps(tool_uses),
        expected_tools=["mark_email_unread"],
        tools=EMAIL_TOOLS
    )

    metric = make_metric()
    assert_test(test_case, [metric])

    assert len(tool_uses) == 1
    assert tool_uses[0]["name"] == "mark_email_unread"
    assert tool_uses[0]["input"].get("email_id") == "123"


def test_search_vs_filter_disambiguation():
    """Should use search for content queries, list_emails for exact filters"""
    search_input = "Find emails mentioning budget"
    filter_input = "Show emails from john@example.com"

    search_tools = agent.select_tools(search_input)
    filter_tools = agent.select_tools(filter_input)

    assert search_tools[0]["name"] == "search_emails_by_content"
    assert filter_tools[0]["name"] == "list_emails"
