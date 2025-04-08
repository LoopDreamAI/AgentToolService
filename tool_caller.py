## FastAPI request call tool
import json
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
            if not msg.data:
                print(f"Received message: {msg.data}")
                continue
            event = getattr(msg, 'event', None)
            if event == 'error':
                print(f"Error: {msg.data}")
                return None
            
            data = json.loads(msg.data)
            print(f"Status update: {data['status']}")
            
            if data["status"] == "completed":
                return data["result"]
            elif data["status"] == "failed":
                print(f"Tool error: {data['error']}")
                return None
            elif data["status"] == "cancelled":
                return None
                
    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return None


if __name__ == "__main__":
    print()
    
   
    