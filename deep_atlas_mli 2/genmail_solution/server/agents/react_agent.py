from typing import List, TypedDict
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from agents.tool_agent import TOOL_DESCRIPTIONS, extract_json_array, EMAIL_TOOLS
from agents.tool_executor import execute_tool

MAX_ITERATIONS = 5

REACT_PROMPT = f"""You are an email assistant. Call tools to fulfill the user's request.

Tools:
{TOOL_DESCRIPTIONS}

{{context}}User request: {{request}}
Output a JSON array of tool calls, or [] if you have enough information.
Output ONLY the JSON array."""


class ReactState(TypedDict):
    user_input: str
    tool_results: List[dict]
    selected_tools: List[dict]
    iteration_count: int


def reason(state: ReactState) -> ReactState:
    prior = ""
    if state["tool_results"]:
        summaries = "\n".join(
            f"  {r['tool']}: {r['output']}"
            for r in state["tool_results"]
        )
        prior = f"Prior results:\n{summaries}\n\n"

    prompt = REACT_PROMPT.format(context=prior, request=state["user_input"])
    llm = ChatOllama(model="llama3.2", temperature=0)
    response = llm.invoke(prompt)

    valid_names = {t["name"] for t in EMAIL_TOOLS}
    try:
        candidates = extract_json_array(response.content)
        selected = [t for t in candidates if isinstance(t, dict) and t.get("name") in valid_names]
    except Exception:
        selected = []

    return {**state, "selected_tools": selected, "iteration_count": state["iteration_count"] + 1}


def act(state: ReactState) -> ReactState:
    results = [
        {"tool": tool["name"], "output": execute_tool(tool["name"], tool.get("input", {}))}
        for tool in state["selected_tools"]
    ]
    return {**state, "tool_results": state["tool_results"] + results}


def should_continue(state: ReactState) -> str:
    if state["selected_tools"] and state["iteration_count"] < MAX_ITERATIONS:
        return "continue"
    return "end"


def create_workflow():
    workflow = StateGraph(ReactState)
    workflow.add_node("reason", reason)
    workflow.add_node("act", act)
    workflow.set_entry_point("reason")
    workflow.add_conditional_edges("reason", should_continue, {"continue": "act", "end": END})
    workflow.add_edge("act", "reason")
    return workflow.compile()


def run_react_agent(user_input: str) -> dict:
    app = create_workflow()
    result = app.invoke({
        "user_input": user_input,
        "tool_results": [],
        "selected_tools": [],
        "iteration_count": 0
    })
    return {
        "tool_results": result["tool_results"],
        "iterations": result["iteration_count"]
    }
