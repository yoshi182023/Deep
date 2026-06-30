import ollama  # 导入 Ollama SDK，用于与本地模型对话
from storage import ExpenseStorage  # 导入费用存储类
import json  # 导入 JSON 序列化库

storage = ExpenseStorage()  # 初始化存储实例
# 原 FILL_THIS_IN 位置开始：tools 函数调用定义
# 定义模型可调用的工具列表
tools = [  
    {  # 工具 1 配置开始
        "type": "function",   
        "function": {   
            "name": "add_expense",  # 函数名为 add_expense
            "description": "Add a new expense to the tracking system",  
            "parameters": {  
                # 参数模式定义开始
                "type": "object",  
                # 参数整体为对象
                "properties": {  
           
                    "category": { 
                    # 字段定义开始
                        "type": "string",  
                    #  类型为字符串
                        "description": "Expense category (e.g., groceries, dining, transportation)",  # category 字段说明
                    },   
                    "amount": {"type": "number", "description": "Amount spent"},  # amount 类型为数字并说明含义
                    "description": {  
                        "type": "string",  # description 类型为字符串
                        "description": "Optional description of the expense",  # description 字段说明
                    },  # description 字段定义结束
                    "date": {   
                        "type": "string",  
                        # date 类型为字符串
                        "description": "Date in YYYY-MM-DD format (optional, defaults to today)",  # date 字段说明
                    },   
                },  # 参数字段定义结束
                "required": ["category", "amount"],  
                # 必填字段为 category 和 amount
            },  # 参数模式定义结束
        },  # 函数定义对象结束
    },  # 工具 1 配置结束
    {  # 工具 2 配置开始
        "type": "function",  # 声明这是函数类型工具
        "function": {  # 函数定义对象开始
            "name": "get_expenses",  # 函数名为 get_expenses
            "description": "Retrieve expenses with optional filters",  # 函数用途说明
            "parameters": {  
                "type": "object",   
                "properties": {  # 参数字段定义开始
                    "category": {"type": "string", "description": "Filter by category"},  # 按分类筛选参数
                    "start_date": {  # start_date 字段定义开始
                        "type": "string",  # start_date 类型为字符串
                        "description": "Start date in YYYY-MM-DD format",  # start_date 字段说明
                    },  # start_date 字段定义结束
                    "end_date": {  # end_date 字段定义开始
                        "type": "string",  # end_date 类型为字符串
                        "description": "End date in YYYY-MM-DD format",  # end_date 字段说明
                    },  # end_date 字段定义结束
                },  # 参数字段定义结束
            },  # 参数模式定义结束
        },  # 函数定义对象结束
    },  # 工具 2 配置结束
    {   
        "type": "function",   
        "function": {   
            "name": "update_expense",  
            # 函数名为 update_expense
            "description": "Update an existing expense", 
             # 函数用途说明
            "parameters": {  
                "type": "object",     
                "properties": {   
                    "expense_id": {   
                        "type": "integer",  # expense_id 类型为整数
                        "description": "ID of the expense to update",  # expense_id 字段说明
                    },  
                    "category": {"type": "string", "description": "New category"},  # 新分类参数
                    "amount": {"type": "number", "description": "New amount"},  # 新金额参数
                    "description": {"type": "string", "description": "New description"},  # 新描述参数
                    "date": {  # date 字段定义开始
                        "type": "string",  # date 类型为字符串
                        "description": "New date in YYYY-MM-DD format",  # date 字段说明
                    },  # date 字段定义结束
                },  # 参数字段定义结束
                "required": ["expense_id"],  # 必填字段为 expense_id
            },  # 参数模式定义结束
        },  # 函数定义对象结束
    },  # 工具 3 配置结束
    {  # 工具 4 配置开始
        "type": "function",  # 声明这是函数类型工具
        "function": {  # 函数定义对象开始
            "name": "delete_expense",  # 函数名为 delete_expense
            "description": "Delete an expense by ID",  # 函数用途说明
            "parameters": {  # 参数模式定义开始
                "type": "object",  # 参数整体为对象
                "properties": {  # 参数字段定义开始
                    "expense_id": {  # expense_id 字段定义开始
                        "type": "integer",  # expense_id 类型为整数
                        "description": "ID of the expense to delete",  # expense_id 字段说明
                    }  # expense_id 字段定义结束
                },  # 参数字段定义结束
                "required": ["expense_id"],  # 必填字段为 expense_id
            },  # 参数模式定义结束
        },  # 函数定义对象结束
    },  # 工具 4 配置结束
]  # 工具列表定义结束
# 原 FILL_THIS_IN 位置结束：tools 函数调用定义


def execute_tool(tool_name: str, arguments: dict) -> dict:  
    # 根据工具名执行对应存储方法
    try:  
        # 原 FILL_THIS_IN 位置开始：工具名到存储方法的映射逻辑
        if tool_name == "add_expense":  # 匹配新增费用工具
            return storage.add_expense(**arguments)  # 解包参数并调用新增方法
        elif tool_name == "get_expenses":  # 匹配查询费用工具
            return storage.get_expenses(**arguments)  # 解包参数并调用查询方法
        elif tool_name == "update_expense":  # 匹配更新费用工具
            return storage.update_expense(**arguments)  # 解包参数并调用更新方法
        elif tool_name == "delete_expense":  # 匹配删除费用工具
            return storage.delete_expense(**arguments)  # 解包参数并调用删除方法
        else:  # 处理未知工具名
            raise ValueError(f"Unknown tool: {tool_name}")  # 抛出未知工具异常
        # 原 FILL_THIS_IN 位置结束：工具名到存储方法的映射逻辑
    except Exception as e:  # 捕获所有执行异常
        raise Exception(f"Tool execution error: {str(e)}")  # 统一包装后重新抛出异常


def chat(user_message: str, conversation_history: list, max_retries: int = 3) -> str:  # 处理一次用户对话并在需要时调用工具
    conversation_history.append({"role": "user", "content": user_message}) 
     # 将用户消息追加到会话历史

    response = ollama.chat(  
        # 向模型发送首次请求
        model="llama3.1:8b", messages=conversation_history, tools=tools  
        # 指定模型、历史消息与可用工具
    )  # 首次请求结束

    conversation_history.append(response["message"]) 
     # 将模型回复追加到会话历史

    if response["message"].get("tool_calls"):  
        # 若模型请求调用工具则进入工具处理流程
        for tool_call in response["message"]["tool_calls"]:  
            # 遍历本轮所有工具调用请求
            tool_name = tool_call["function"]["name"]  # 提取工具名称
            arguments = tool_call["function"]["arguments"]  # 提取工具参数

            # 原 FILL_THIS_IN 位置开始：工具调用失败重试机制
            retry_count = 0  # 初始化重试计数器
            while retry_count < max_retries:  # 在最大重试次数内循环尝试
                try:  # 开始单次工具执行尝试
                    result = execute_tool(tool_name, arguments)  # 执行工具调用
                    conversation_history.append(  # 把工具成功结果写入会话历史
                        {"role": "tool", "content": json.dumps(result)}  # 工具消息使用 JSON 字符串承载结果
                    )  # 写入成功结果结束
                    break  # 执行成功后跳出重试循环
                except Exception as e:  # 捕获本次工具执行异常
                    retry_count += 1  # 重试计数加一
                    if retry_count >= max_retries:  # 如果达到最大重试次数
                        conversation_history.append(  # 记录最终失败信息
                            {  # 工具失败消息对象开始
                                "role": "tool",  # 消息角色为工具
                                "content": json.dumps(  # 将错误信息序列化为 JSON 字符串
                                    {  # 错误详情对象开始
                                        "error": f"Failed after {max_retries} attempts: {str(e)}"  # 包含失败次数与异常内容
                                    }  # 错误详情对象结束
                                ),  # 错误信息序列化结束
                            }  # 工具失败消息对象结束
                        )  # 记录最终失败信息结束
                        break  # 达到重试上限后退出循环

                    conversation_history.append(  # 记录本次失败并提示模型重试
                        {  # 工具失败消息对象开始
                            "role": "tool",  # 消息角色为工具
                            "content": json.dumps(  # 将错误信息序列化为 JSON 字符串
                                {"error": str(e), "retry": retry_count}  # 写入错误内容与当前重试次数
                            ),  # 错误信息序列化结束
                        }  # 工具失败消息对象结束
                    )  # 失败重试信息写入结束

                    retry_response = ollama.chat(  # 把失败上下文发给模型请求新的工具调用
                        model="llama3.1:8b", messages=conversation_history, tools=tools  # 继续使用同一模型与工具定义
                    )  # 重试请求结束
                    conversation_history.append(retry_response["message"])  # 将重试响应追加到会话历史

                    if retry_response["message"].get("tool_calls"):  # 若模型返回新的工具调用
                        tool_call = retry_response["message"]["tool_calls"][0]  # 取第一条新的工具调用
                        tool_name = tool_call["function"]["name"]  # 更新工具名称
                        arguments = tool_call["function"]["arguments"]  # 更新工具参数
                    else:  # 模型未返回新的工具调用
                        break  # 退出重试循环
            # 原 FILL_THIS_IN 位置结束：工具调用失败重试机制

        final_response = ollama.chat(  # 工具处理后再次请求模型生成最终自然语言回复
            model="llama3.1:8b", messages=conversation_history, tools=tools  # 携带完整上下文继续对话
        )  # 最终回复请求结束
        conversation_history.append(final_response["message"])  # 将最终回复追加到会话历史
        return final_response["message"]["content"]  # 返回最终回复文本

    return response["message"]["content"]  # 无工具调用时直接返回首次回复文本


def main():  # 程序主入口函数
    print("Expense Tracker - Type 'quit' to exit\n")  # 打印启动提示
    # 原 FILL_THIS_IN 位置开始：系统消息初始化
    conversation_history = [  # 初始化会话历史列表
        {  # 系统消息对象开始
            "role": "system",  # 消息角色为系统
            "content": "You are a helpful expense tracking assistant. Help users add, view, update, and delete their expenses. When users request data in a specific format (like JSON or CSV), format your response accordingly. Be concise and clear.",  # 定义助手行为与输出要求
        }  # 系统消息对象结束
    ]  # 会话历史初始化结束
    # 原 FILL_THIS_IN 位置结束：系统消息初始化

    while True:   
        user_input = input("You: ").strip()  # 读取并清理用户输入
        if user_input.lower() == "quit":  # 判断是否输入退出命令
            break  

        if not user_input:  # 判断是否为空输入
            continue  # 空输入时进入下一轮循环

        response = chat(user_input, conversation_history)  # 调用聊天处理函数
        print(f"Assistant: {response}\n")  # 打印助手回复


if __name__ == "__main__":   
    main()  
