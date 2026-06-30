# MCP 多服务器客户端：连接并发现 MCP 服务器上的工具
from langchain_mcp_adapters.client import MultiServerMCPClient
# LangChain Agent：将 LLM 与工具组合，实现自动工具调用
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
# 对话消息类型：用户消息与助手消息
from langchain_core.messages import HumanMessage, AIMessage
import asyncio
import traceback


def get_message_role(msg):
    """Extract role from a message (dict or LangChain message object)"""
    # 从字典或 LangChain 消息对象中提取角色（user / assistant）
    if isinstance(msg, dict):
        return msg.get("role")
    elif isinstance(msg, HumanMessage):
        return "user"
    elif isinstance(msg, AIMessage):
        return "assistant"
    else:
        # 其他 LangChain 消息类型，尝试读取 type 属性
        return getattr(msg, "type", None)


def get_message_content(msg):
    """Extract content from a message (dict or LangChain message object)"""
    # 从字典或 LangChain 消息对象中提取文本内容
    if isinstance(msg, dict):
        return msg.get("content", "")
    else:
        return getattr(msg, "content", "")


async def main():
    try:
        print("Initializing MCP client and agent...")

        # FILL_THIS_IN: 初始化 MCP 客户端配置
        # 提示：使用 MultiServerMCPClient，字典结构示例：
        #   - 键：服务器名称（如 "task-manager"）
        #   - 值：包含 "transport"、"command"、"args" 的嵌套字典
        #   - transport 设为 "stdio"（标准输入输出通信）
        #   - command 为虚拟环境中 Python 解释器的绝对路径
        #   - args 为包含 task_mcp_server.py 绝对路径的列表
        client = None

        # FILL_THIS_IN: 从 MCP 服务器动态获取可用工具列表
        # 提示：tools = await client.get_tools()
        tools = None

        # 初始化本地 Ollama 聊天模型（需确保 Ollama 已运行且模型已下载）
        model = init_chat_model("gemma4:e4b-it-q4_k_M", model_provider="ollama")

        # FILL_THIS_IN: 将模型与 MCP 工具组合成 Agent
        # 提示：agent = create_agent(model, tools)
        agent = None

        print("Ready! Type your message (or 'quit'/'exit'/'q' to end):\n")

        # FILL_THIS_IN: 初始化空列表，用于保存多轮对话历史
        # Agent 本身无状态，需在外部维护 messages 列表
        messages = None

        # 主循环：持续接收用户输入并调用 Agent
        while True:
            try:
                # 读取用户输入
                user_input = input("You: ").strip()

                # 退出命令
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                # 忽略空输入
                if not user_input:
                    continue

                # FILL_THIS_IN: 将用户消息加入对话历史
                # 提示：messages.append(HumanMessage(content=user_input))
                pass

                # 携带完整对话历史调用 Agent（支持多轮上下文）
                response = await agent.ainvoke({"messages": messages})

                # 从 Agent 响应中提取助手回复文本
                assistant_response = None

                if isinstance(response, dict):
                    # 部分 Agent 返回格式含 "output" 键
                    if "output" in response:
                        assistant_response = response["output"]
                    # 部分 Agent 返回格式含 "messages" 键
                    elif "messages" in response:
                        response_messages = response["messages"]
                        # 用已有历史长度判断哪些是本次新增的消息，避免重复追加
                        existing_message_count = len(messages)
                        if len(response_messages) > existing_message_count:
                            # 取出本次响应中新增的消息
                            new_messages = response_messages[existing_message_count:]
                            assistant_messages = [
                                msg
                                for msg in new_messages
                                if get_message_role(msg) == "assistant"
                            ]
                            if assistant_messages:
                                assistant_response = get_message_content(
                                    assistant_messages[-1]
                                )
                                # FILL_THIS_IN: 将助手回复追加到对话历史
                                # 提示：messages.append(assistant_messages[-1])
                                pass
                        else:
                            # 回退逻辑：从全部响应消息中找助手消息
                            assistant_messages = [
                                msg
                                for msg in response_messages
                                if get_message_role(msg) == "assistant"
                            ]
                            if assistant_messages:
                                assistant_response = get_message_content(
                                    assistant_messages[-1]
                                )
                                # 仅当历史中不存在相同消息时才追加，防止重复
                                last_msg = assistant_messages[-1]
                                msg_already_exists = any(
                                    get_message_role(m) == get_message_role(last_msg)
                                    and get_message_content(m)
                                    == get_message_content(last_msg)
                                    for m in messages
                                )
                                if not msg_already_exists:
                                    messages.append(last_msg)
                    # 少数 Agent 类型使用 "answer" 键
                    elif "answer" in response:
                        assistant_response = response["answer"]
                    else:
                        # 无法识别格式时，将整个字典转为字符串显示
                        assistant_response = str(response)
                elif isinstance(response, str):
                    assistant_response = response
                else:
                    assistant_response = str(response)

                # 打印助手回复
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


# 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
