# Task Extractor Agent - Workflow Visualization

**Description:** Extracts actionable tasks from unread emails

## Graph Structure

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	format_emails(format_emails)
	extract_tasks(extract_tasks)
	parse_response(parse_response)
	__end__([<p>__end__</p>]):::last
	__start__ --> format_emails;
	extract_tasks --> parse_response;
	format_emails --> extract_tasks;
	parse_response --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```

## State Schema

| Field | Type | Optional |
|-------|------|----------|
| `emails` | `List[dict]` | No |
| `emails_text` | `<class 'str'>` | No |
| `raw_response` | `<class 'str'>` | No |
| `tasks` | `ActionItem]` | No |

