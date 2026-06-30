import ollama
from storage import ExpenseStorage
import json

storage = ExpenseStorage()

tools = [
    {
        "type": "function",
        "function": {
            "name": "add_expense",
            "description": "Add a new expense to the tracking system",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Expense category (e.g., groceries, dining, transportation)",
                    },
                    "amount": {"type": "number", "description": "Amount spent"},
                    "description": {
                        "type": "string",
                        "description": "Optional description of the expense",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (optional, defaults to today)",
                    },
                },
                "required": ["category", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_expenses",
            "description": "Retrieve expenses with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category"},
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_expense",
            "description": "Update an existing expense",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {
                        "type": "integer",
                        "description": "ID of the expense to update",
                    },
                    "category": {"type": "string", "description": "New category"},
                    "amount": {"type": "number", "description": "New amount"},
                    "description": {"type": "string", "description": "New description"},
                    "date": {
                        "type": "string",
                        "description": "New date in YYYY-MM-DD format",
                    },
                },
                "required": ["expense_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_expense",
            "description": "Delete an expense by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_id": {
                        "type": "integer",
                        "description": "ID of the expense to delete",
                    }
                },
                "required": ["expense_id"],
            },
        },
    },
]


def execute_tool(tool_name: str, arguments: dict) -> dict:
    try:
        if tool_name == "add_expense":
            return storage.add_expense(**arguments)
        elif tool_name == "get_expenses":
            return storage.get_expenses(**arguments)
        elif tool_name == "update_expense":
            return storage.update_expense(**arguments)
        elif tool_name == "delete_expense":
            return storage.delete_expense(**arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    except Exception as e:
        raise Exception(f"Tool execution error: {str(e)}")


def chat(user_message: str, conversation_history: list, max_retries: int = 3) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    response = ollama.chat(
        model="llama3.1:8b", messages=conversation_history, tools=tools
    )

    conversation_history.append(response["message"])

    if response["message"].get("tool_calls"):
        for tool_call in response["message"]["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]

            retry_count = 0
            while retry_count < max_retries:
                try:
                    result = execute_tool(tool_name, arguments)
                    conversation_history.append(
                        {"role": "tool", "content": json.dumps(result)}
                    )
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        conversation_history.append(
                            {
                                "role": "tool",
                                "content": json.dumps(
                                    {
                                        "error": f"Failed after {max_retries} attempts: {str(e)}"
                                    }
                                ),
                            }
                        )
                        break

                    conversation_history.append(
                        {
                            "role": "tool",
                            "content": json.dumps(
                                {"error": str(e), "retry": retry_count}
                            ),
                        }
                    )

                    retry_response = ollama.chat(
                        model="llama3.1:8b", messages=conversation_history, tools=tools
                    )
                    conversation_history.append(retry_response["message"])

                    if retry_response["message"].get("tool_calls"):
                        tool_call = retry_response["message"]["tool_calls"][0]
                        tool_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]
                    else:
                        break

        final_response = ollama.chat(
            model="llama3.1:8b", messages=conversation_history, tools=tools
        )
        conversation_history.append(final_response["message"])
        return final_response["message"]["content"]

    return response["message"]["content"]


def main():
    print("Expense Tracker - Type 'quit' to exit\n")
    conversation_history = [
        {
            "role": "system",
            "content": "You are a helpful expense tracking assistant. Help users add, view, update, and delete their expenses. When users request data in a specific format (like JSON or CSV), format your response accordingly. Be concise and clear.",
        }
    ]

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "quit":
            break

        if not user_input:
            continue

        response = chat(user_input, conversation_history)
        print(f"Assistant: {response}\n")


if __name__ == "__main__":
    main()
