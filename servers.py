from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

# import mcp

app = FastAPI(title="MCP Protocol Layer")

class RPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict
    id: str | int | None = None

@app.post("/mcp/toolcall", tags=["MCP Core"])
async def handle_rpc(
    request: RPCRequest,
    x_mcp_agent: str = Header(..., description="Agent标识 (如anthropic/v1)"),
    x_tool_version: str = Header("1.0", description="协议版本")
):
    pass

@app.get("/mcp/alltools")
async def get_all_tools():
    with open("MCP/tools_list.json") as file:
        pass