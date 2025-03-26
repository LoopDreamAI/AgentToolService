import os, sys
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

server_script_path = os.path.join(current_dir, "mcp_server.py")
venv_path = "/home/ubuntu/miniconda3/envs/tool/"

sys.path.append(os.path.join(current_dir, "..", "LearnAccompany"))
sys.path.append(os.path.join(current_dir, "..", "tools"))

session: Optional[ClientSession] = None
exit_stack = AsyncExitStack()

async def connect_to_server(tool_name, tool_args):
    is_python = server_script_path.endswith('.py')
    is_js = server_script_path.endswith('.js')
    if not (is_python or is_js):
        raise ValueError("Server script must be a .py or .js file")
        
    command = "python" if is_python else "node"
    env = os.environ.copy()
    
    if is_python:
        if venv_path:
            if sys.platform == 'win32':
                python_executable = os.path.join(venv_path, 'Scripts', 'python.exe')
                env['PATH'] = os.path.join(venv_path, 'Scripts') + os.pathsep + env['PATH']
            else:
                python_executable = os.path.join(venv_path, 'bin', 'python')
                env['PATH'] = os.path.join(venv_path, 'bin') + os.pathsep + env['PATH']
            if not os.path.exists(python_executable):
                raise ValueError(f"Python interpreter not found in virtual environment: {python_executable}")
            command = python_executable
        else:
            command = "python"
    else:
        command = "node"

    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
        env=env
    )
    
    try:
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        
        await session.initialize()
        print("session initialized")

        if tool_name == None: 

            response = await session.list_tools()
            available_tools = [{ 
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in response.tools]
            return available_tools
        
        else:
            result = await session.call_tool(tool_name, tool_args)
            # 解码
            try:
                result_list = []
                for item in result.content:
                    res = json.loads(item.text)
                    if isinstance(res, (int, float)):
                        raise ValueError("result is not a json object")
                    else:
                        result_list.append(res)
                return result_list
            except:
                return result.content[0].text

    except Exception as e:
        print(f"An error occurred while connecting to the server: {e}")
        raise


async def call_tool(tool_name, tool_args):
    try:
        result = await connect_to_server(tool_name, tool_args)
        return result
    finally:
        await exit_stack.aclose()

## FastAPI request call tool
import requests
from sseclient import SSEClient

url = "http://127.0.0.1:8848"

def sse_call_tool(tool_name: str, tool_args: dict):
    resp = requests.post(
        f"{url}/call_tool/{tool_name}",
        json=tool_args
    )
    task_id = resp.json()["task_id"]
    print(f"Create Task ID: {task_id}")

    messages = SSEClient(f"{url}/callback/{task_id}")
    
    try:
        for msg in messages:
            event = getattr(msg, 'event', None)
            if event == 'error':
                print(f"Error: {msg.data}")
                return None
            
            data = json.loads(msg.data)
            print(f"Status update: {data['status']}")
            
            if data["status"] == "completed":
                return data["result"]
            elif data["status"] == "failed":
                print(f"Tool error: {data["error"]}")
                return None
            elif data["status"] == "cancelled":
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return None



if __name__ == "__main__":
    # 列出所有工具
    # result = asyncio.run(call_tool(None, None))
    # print(result)
    
    # ours的联网搜索+解析
    # result = asyncio.run(call_tool("web_search", {"query": "中国的首都是哪里", "max_results": 10}))
    # print(result)
    
    # 数学计算
    # result = asyncio.run(call_tool("round", {"a": 1.23456}))
    # print(result)
    
    # 相关论文搜索
    # result = asyncio.run(call_tool("paper_search", {"query": "large language model", "max_num": 10}))
    # print(result)
    
    # 根据文献link和query解析具体内容
    # result = asyncio.run(call_tool("paper_parse", {"link": "https://arxiv.org/abs/2403.08271", 
    #                                               "title": "Humanity’s Last Exam", 
    #                                               "query": "请解析以下论文的摘要：https://arxiv.org/abs/2403.08271"}))
    # print(result)
    
    # 图片解析
    # image_path = os.path.join(current_dir, "Test", "test.png")
    # result = asyncio.run(call_tool("image_to_text", {"image_path" : image_path}))
    # print(result)
    
    # 根据query解析图片内容
    image_path = os.path.join(current_dir, "Test", "word.png")
    result = asyncio.run(call_tool("ask_question_about_image", {"image_path" : image_path, "question" : "请描述图片中是什么文字，具体内容是什么"}))
    print(result)
    
   
    