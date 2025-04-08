# AgentToolService
ATS - Open, Compatible, Safe and Easy Agent tool Service.

## Tool Service

tool服务器端点如下，需要注意/callback端点为SSE连接：

- get("/health")
  服务器状态
  return {"status": status}
  "ok"/"unready"  


- get("/reset")
  重启MCP服务（更新工具后快速配置）
  return {"status": status}
  "ok"/"unready"/"error"  


- get("/get_tool")
  获取当前所有工具
  return ToolList  
```python
[
    {
        "name": "example_func",
        "description": "Please provide a description of the function here.\n\n    Args:\n        example_arg: Describe the input here.\n    ",
        "input_schema": {
            "properties": {
                "example_arg": {
                    "title": "Example Arg",
                    "type": "string"
                }
            },
            "required": [
                "example_arg"
            ],
            "title": "example_funcArguments",
            "type": "object"
        }
    }
]
```  



- post("/call_tool/{tool_name}")
  调用工具
  Input (tool_args: Dict)
  return {"task_id": task_id}  


- get("/callback/{task_id}")
  获取工具结果，通过sse实时响应
  return EventSourceResponse(event_generator())  
  响应处理可见[tool_caller.py](./tool_caller.py)
  




## MCP
```python
{
    "tools" :
    [
        {
            "name": "get_alerts",
            "description": "Get weather alerts for a US state.\n\n    Args:\n        state: Two-letter US state code (e.g. CA, NY)\n    ",
            "input_schema": {
                "properties": {
                    "state": {
                        "title": "State",
                        "type": "string"
                    }
                },
                "required": [
                    "state"
                ],
                "title": "get_alertsArguments",
                "type": "object"
            }
        },
        {
            "name": "get_forecast",
            "description": "Get weather forecast for a location.\n\n    Args:\n        latitude: Latitude of the location\n        longitude: Longitude of the location\n    ",
            "input_schema": {
                "properties": {
                    "latitude": {
                        "title": "Latitude",
                        "type": "number"
                    },
                    "longitude": {
                        "title": "Longitude",
                        "type": "number"
                    }
                },
                "required": [
                    "latitude",
                    "longitude"
                ],
                "title": "get_forecastArguments",
                "type": "object"
            }
        }
    ]
}
```

### MCP --> Model
Model input json:  
```python
{
    "tools" : [
        {
            "name": str, # tool.name
            "description": str, # tool.description
            "input_schema": dict # tool.inputSchema
        }
    ]
}
```

### Model --> MCP
Model output for MCP use tools:  
```python
{
    "type" : "tool_use"
    "name" : str
    "input" : dict
}
```

Example code:  

```python
final_text = []
for content in response.content:
    if content.type == 'text':
        final_text.append(content.text)
    elif content.type == 'tool_use':
        tool_name = content.name
        tool_args = content.input
        result = await self.session.call_tool(tool_name, tool_args)
        final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
```

### MCP --> Model
Model input json:

```python
{
    "messages" : [
        {
            "role": "tool", 
            "content": result.content
        }
    ]
}
```

Example code:  

```python
# for content in response.content:
    # elif content.type == 'tool_use':
        if hasattr(content, 'text') and content.text:
            messages.append({
                "role": "assistant",
                "content": content.text
            })
        messages.append({
            "role": "user", 
            "content": result.content
        })
```

### Model --> User

Example code:  

```python
# for content in response.content:
    # elif content.type == 'tool_use':
        final_text.append(response.content[0].text)
return "\n".join(final_text)
```