# Tool Selection Test Cases - Quick Reference

## Test Case Matrix

| Test Name | User Input | Expected Tool | Key Parameters | Category | Edge Case |
|-----------|-----------|----------------|----------------|----------|-----------|
| `test_list_unread_emails` | "Show me all my unread emails" | `list_emails` | `is_read=false` | Basic | No |
| `test_list_emails_from_sender` | "Get all emails from sarah.chen@acme.com" | `list_emails` | `sender="sarah.chen@acme.com"` | Basic | No |
| `test_get_thread_emails` | "Show me all messages in thread abc123" | `list_emails` | `thread_id="abc123"` | Basic | No |
| `test_get_inbox_stats` | "How many unread emails do I have?" | `get_stats` | none | Basic | No |
| `test_get_threads_list` | "Show me all my email conversations" | `get_threads` | none | Basic | No |
| `test_get_specific_email` | "Show me the details of email email_789" | `get_email` | `email_id="email_789"` | Basic | No |
| `test_create_new_email` | "Send an email to john@example.com with subject 'Meeting Tomorrow' and body 'See you at 3pm'" | `create_email` | `recipient`, `subject`, `body` | CRUD | No |
| `test_mark_email_read` | "Mark email email_123 as read" | `mark_email_read` | `email_id="email_123"` | CRUD | No |
| `test_delete_email` | "Delete email with id email_456" | `delete_email` | `email_id="email_456"` | CRUD | No |
| `test_reply_to_thread` | "Reply to thread thread_999 saying 'Thanks for the update'" | `create_email` | `thread_id="thread_999"`, `body` | CRUD | No |
| `test_complex_filter_combination` | "Show unread emails from sarah.chen@acme.com" | `list_emails` | `is_read=false`, `sender` | Complex | No |
| `test_recipient_filter` | "Show emails I sent to alex.wong@vendor.com" | `list_emails` | `recipient="alex.wong@vendor.com"` | Complex | No |
| `test_ambiguous_search_query` | "Find emails about the Phoenix project" | `search_emails_by_content` OR `list_emails` | `query` or filters | Complex | Yes |
| `test_stat_summary_request` | "Give me a summary of my inbox" | `get_stats` | none | Complex | No |
| `test_thread_count_query` | "How many email threads do I have?" | `get_threads` OR `get_stats` | none | Complex | Yes |
| `test_empty_query` | "Show me emails" | `list_emails` | none or minimal | Edge Case | Yes |
| `test_invalid_email_id_format` | "Delete email INVALID_ID_123!@#" | `delete_email` | `email_id` with invalid format | Edge Case | Yes |
| `test_multi_action_request` | "Mark email_111 as read and then delete email_222" | `mark_email_read`, `delete_email` | Two separate tool calls | Edge Case | Yes |
| `test_conversational_style_request` | "Hey, can you check if I have any new messages from my boss?" | `list_emails` OR `get_stats` | conversational parsing | Edge Case | Yes |
| `test_nonexistent_functionality` | "Archive all emails from last year" | `list_emails` OR `delete_email` | graceful degradation | Edge Case | Yes |

## Test Categories

### 🟢 Basic Operations (6 tests)
Simple, single-tool selection with clear user intent.
- Should have ~100% pass rate
- Tests fundamental tool matching

### 🔵 CRUD Operations (4 tests)
Create, Read, Update, Delete actions on emails.
- Should have ~95%+ pass rate
- Tests parameter extraction accuracy

### 🟡 Complex Scenarios (5 tests)
Multiple filters, ambiguous intent, or requires reasoning.
- Should have ~80%+ pass rate
- Tests LLM's ability to handle nuance

### 🔴 Edge Cases (6 tests)
Unusual inputs, invalid data, or stress tests.
- Expected pass rate: ~60-80%
- Tests robustness and graceful degradation

## Parameter Extraction Validation

| Parameter | Tests Covering | Expected Behavior |
|-----------|----------------|-------------------|
| `is_read` | test_list_unread_emails, test_complex_filter_combination | Boolean extraction from "unread"/"read" |
| `sender` | test_list_emails_from_sender, test_complex_filter_combination | Email address extraction |
| `recipient` | test_recipient_filter | Email address extraction |
| `thread_id` | test_get_thread_emails, test_reply_to_thread | ID extraction from context |
| `email_id` | test_get_specific_email, test_mark_email_read, test_delete_email, test_invalid_email_id_format | ID extraction, handles invalid formats |
| `subject` | test_create_new_email | Free text extraction |
| `body` | test_create_new_email, test_reply_to_thread | Free text extraction |

## Multi-Tool Scenarios

| Test | Tools Expected | Reasoning Required |
|------|----------------|-------------------|
| test_multi_action_request | mark_email_read + delete_email | Sequential action recognition |
| test_ambiguous_search_query | search OR list | Semantic understanding |
| test_thread_count_query | get_threads OR get_stats | Multiple valid approaches |

## Failure Analysis Guide

### If Basic Tests Fail
- Issue: Tool descriptions may be unclear
- Fix: Refine tool descriptions and schemas
- Check: API key and connectivity

### If CRUD Tests Fail
- Issue: Parameter extraction problems
- Fix: Add examples to tool schemas
- Check: Required vs optional parameter definitions

### If Complex Tests Fail
- Issue: LLM reasoning or ambiguity handling
- Fix: Add system prompt or few-shot examples
- Consider: Breaking complex queries into steps

### If Edge Cases Fail
- Issue: Expected behavior - these test robustness
- Action: Document behavior and decide if acceptable
- Consider: Adding fallback tools or error handling

## Running Specific Test Categories

```bash
# Run only basic tests
pytest tests/test_tool_selection.py -k "list or get_inbox or get_threads or get_specific"

# Run only CRUD tests
pytest tests/test_tool_selection.py -k "create or mark or delete or reply"

# Run only complex tests
pytest tests/test_tool_selection.py -k "complex or recipient or ambiguous or stat or thread_count"

# Run only edge cases
pytest tests/test_tool_selection.py -k "empty or invalid or multi_action or conversational or nonexistent"
```

## Success Criteria

### Minimum Viable
- ✅ All basic tests pass (6/6)
- ✅ Most CRUD tests pass (3/4)
- ✅ Half of complex tests pass (3/5)

### Production Ready
- ✅ All basic tests pass (6/6)
- ✅ All CRUD tests pass (4/4)
- ✅ Most complex tests pass (4/5)
- ✅ Half of edge cases handled (3/6)

### Excellent
- ✅ All basic tests pass (6/6)
- ✅ All CRUD tests pass (4/4)
- ✅ All complex tests pass (5/5)
- ✅ Most edge cases handled (5/6)

## Next Test Ideas

Consider adding tests for:
- Time-based queries ("emails from last week")
- Priority/importance filters
- Attachment handling
- Multiple recipients (BCC/CC)
- Draft vs sent email distinction
- Thread reply chains
- Bulk operations
- Conditional logic ("if unread, mark as read")
- Chained operations with dependencies
