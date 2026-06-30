from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage
import asyncio
import traceback


def get_message_role(msg):
    """Extract role from a message (dict or LangChain message object)"""
    if isinstance(msg, dict):
        return msg.get("role")
    elif isinstance(msg, HumanMessage):
        return "user"
    elif isinstance(msg, AIMessage):
        return "assistant"
    else:
        # Try to get type attribute for other LangChain message types
        return getattr(msg, "type", None)


def get_message_content(msg):
    """Extract content from a message (dict or LangChain message object)"""
    if isinstance(msg, dict):
        return msg.get("content", "")
    else:
        return getattr(msg, "content", "")


async def main():
    try:
        print("Initializing MCP client and agent...")
        client = MultiServerMCPClient(
            {
                "task-manager": {
                    "transport": "stdio",
                    "command": "/Users/jpranaymartin/Code/learn-mcp/mcp_servers/.venv/bin/python",
                    "args": [
                        "/Users/jpranaymartin/Code/learn-mcp/mcp_servers/mcp_server/task_mcp_server.py"
                    ],
                }
            }
        )
        tools = await client.get_tools()
        # Initialize Ollama chat model explicitly
        model = init_chat_model("gemma4:e4b-it-q4_k_M", model_provider="ollama")
        agent = create_agent(model, tools)
        print("Ready! Type your message (or 'quit'/'exit'/'q' to end):\n")

        # Maintain conversation history
        messages = []

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                if not user_input:
                    continue

                # Add user message to history
                messages.append(HumanMessage(content=user_input))

                # Invoke agent with conversation history
                response = await agent.ainvoke({"messages": messages})

                # Extract and display the response
                # Handle different response formats from langchain agents
                assistant_response = None

                if isinstance(response, dict):
                    # Check for "output" key (common in langchain agents)
                    if "output" in response:
                        assistant_response = response["output"]
                    # Check for "messages" key
                    elif "messages" in response:
                        # Get all assistant messages from the response
                        response_messages = response["messages"]
                        # Find the last assistant message that's not already in our history
                        # This prevents duplicating messages
                        existing_message_count = len(messages)
                        if len(response_messages) > existing_message_count:
                            # Get new messages (those after our current history)
                            new_messages = response_messages[existing_message_count:]
                            assistant_messages = [
                                msg
                                for msg in new_messages
                                if get_message_role(msg) == "assistant"
                            ]
                            if assistant_messages:
                                assistant_response = get_message_content(assistant_messages[-1])
                                # Add the new assistant message to history
                                messages.append(assistant_messages[-1])
                        else:
                            # Fallback: get any assistant message from response
                            assistant_messages = [
                                msg
                                for msg in response_messages
                                if get_message_role(msg) == "assistant"
                            ]
                            if assistant_messages:
                                assistant_response = get_message_content(assistant_messages[-1])
                                # Only add if not already in history (check by content and role)
                                last_msg = assistant_messages[-1]
                                msg_already_exists = any(
                                    get_message_role(m) == get_message_role(last_msg)
                                    and get_message_content(m) == get_message_content(last_msg)
                                    for m in messages
                                )
                                if not msg_already_exists:
                                    messages.append(last_msg)
                    # Check for "answer" key (some agent types)
                    elif "answer" in response:
                        assistant_response = response["answer"]
                    else:
                        # Fallback: convert entire dict to string
                        assistant_response = str(response)
                elif isinstance(response, str):
                    assistant_response = response
                else:
                    assistant_response = str(response)

                # Display the response
                if assistant_response:
                    print(f"\nAssistant: {assistant_response}\n")
                else:
                    print(f"\nAssistant: {response}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError processing message: {e}\n")
                traceback.print_exc()
                continue

    except Exception as e:
        print(f"Error initializing: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
