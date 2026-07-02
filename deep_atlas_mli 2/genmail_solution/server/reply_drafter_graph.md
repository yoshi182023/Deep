# Reply Drafter Agent - Workflow Visualization

**Description:** Drafts email replies based on thread context

## Graph Structure

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	fetch_thread_context(fetch_thread_context)
	draft_reply(draft_reply)
	__end__([<p>__end__</p>]):::last
	__start__ --> fetch_thread_context;
	fetch_thread_context --> draft_reply;
	draft_reply --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## State Schema

| Field | Type | Optional |
|-------|------|----------|
| `email_id` | `<class 'int'>` | No |
| `thread_emails` | `List[dict]` | No |
| `thread_context` | `<class 'str'>` | No |
| `draft` | `<class 'str'>` | No |
| `feedback` | `str` | Yes |
| `tone` | `str` | Yes |
| `previous_draft` | `str` | Yes |
| `thread_id` | `<class 'str'>` | No |
| `recipient` | `<class 'str'>` | No |
| `subject` | `<class 'str'>` | No |

