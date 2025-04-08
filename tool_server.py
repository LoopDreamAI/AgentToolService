import json
import os
import uuid
import asyncio
import uvicorn
from typing import Dict
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from sse_starlette.sse import EventSourceResponse

from mcp import MCPManager

manager = MCPManager()

current_dir = os.path.dirname(os.path.abspath(__file__))
def load_agent_tools():
    config_path = os.path.join(current_dir, "config", "agent_tools.json")
    with open(config_path, 'r') as file:
        return json.load(file)
    
agent_tools = load_agent_tools()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.ready()
    yield
    for client in manager.client_list:
        await client.cleanup()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    status = "ok" if manager.get_status() else "unready"
    return {"status": status}

@app.get("/reset")
async def reset():
    try:
        global agent_tools
        agent_tools = load_agent_tools()
        await manager.ready()
        status = "ok" if manager.get_status() else "unready"
        return {"status": status}
    except Exception as e:
        print(f"Error during reset: {e}")
        return {"status": "error"}

@app.get("/get_tool")
async def get_tools():
    return manager.get_tools()

@app.get("/get_tool/{agent_name}")
async def get_tools(agent_name: str):
    if (not agent_tools.get(agent_name)) or (not agent_tools[agent_name]):
        return manager.get_tools()
    return agent_tools[agent_name]


# Call
tasks: Dict[str, dict] = {}

@app.post("/call_tool/{tool_name}")
async def create_tool_task(tool_name: str, tool_args: Dict):
    tool_names = manager.get_toolnames()
    if tool_name not in tool_names:
        raise HTTPException(404, "Tool not found")
    task_id = str(uuid.uuid4())
    
    tasks[task_id] = {
        "tool": tool_name,
        "arg": tool_args,
        "status": "pendding",
        "result": None,
        "error": None,
    }

    asyncio.create_task(execute_tool(task_id, tool_name, tool_args))
    
    return {"task_id": task_id}

async def execute_tool(task_id: str, tool_name: str, tool_args: Dict):
    update_task(task_id, {"status": "running"})
    try:
        result = await manager.call_tool(
            tool_name,
            tool_args
        )
        
        update_task(task_id, {
            "status": "completed",
            "result": result
        })
        
    except Exception as e:
        update_task(task_id, {
            "status": "failed",
            "error": str(e)
        })
    finally:
        await asyncio.sleep(300)
        tasks.pop(task_id, None)

def update_task(task_id: str, updates: dict):
    if task_id in tasks:
        tasks[task_id].update(updates)

@app.get("/callback/{task_id}")
async def sse_updates(task_id: str):
    async def event_generator():
        last_status = None
        while True:
            task = tasks.get(task_id)
            
            if not task:
                yield {
                    "event": "error", 
                    "data": "The task does not exist or has been cleared."
                }
                break
                
            if task["status"] != last_status:
                yield {
                    "data": {
                        "status": task["status"],
                        "result": task["result"],
                        "error": task["error"]
                    }
                }
                last_status = task["status"]
                if task["status"] in ("completed", "failed", "cancelled"):
                    break

            await asyncio.sleep(1)
    return EventSourceResponse(event_generator())

@app.get("/cancel/{task_id}")
async def cancel_task(task_id: str):
    if task := tasks.get(task_id):
        task["status"] = "cancelled"
        return {
                "data": {
                    "status": task["status"],
                    "result": task["result"],
                    "error": task["error"]
                }
            }
    else:
        return {
                "event": "error", 
                "data": "The task does not exist or has been cleared."
            }

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8848,
        lifespan="on"
        # reload=True
    )