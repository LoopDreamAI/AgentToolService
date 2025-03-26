from typing import *
from mcp.server.fastmcp import FastMCP
import inspect
from camel.toolkits import MathToolkit, SymPyToolkit, ImageAnalysisToolkit, SearchToolkit
import os
import sys
import traceback
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, '..'))

mcp = FastMCP("SJTU")

def copy_signature(source_func):
    """复制源函数的签名到目标函数"""
    def decorator(target_func):
        sig = inspect.signature(source_func)
        target_func.__signature__ = sig
        # 复制类型注解
        target_func.__annotations__ = source_func.__annotations__.copy()
        return target_func
    return decorator


toolkit = MathToolkit()
for func in toolkit.get_tools():
    func = func.func
    doc = func.__doc__
    name = func.__name__
    @mcp.tool(description=doc, name=name) # MCP tool identification
    @copy_signature(func)
    async def func_tool(_func=func, **kwargs):
        return _func(**kwargs)


toolkit = SymPyToolkit()
for func in toolkit.get_tools():
    func = func.func
    doc = func.__doc__
    name = func.__name__
    @mcp.tool(description=doc, name=name) # MCP tool identification
    @copy_signature(func)
    async def func_tool(_func=func, **kwargs):
        return _func(**kwargs)


os.environ["OPENAI_API_BASE_URL"] = "http://47.88.65.188:8405/v1"
os.environ["OPENAI_API_KEY"] = "sk-iq1VhpR4mLLriwh619D83f6d7a53426282Ae38731eA7Ff7f"
toolkit = ImageAnalysisToolkit()
for func in toolkit.get_tools():
    func = func.func
    doc = func.__doc__
    name = func.__name__
    @mcp.tool(description=doc, name=name) # MCP tool identification
    @copy_signature(func)
    async def func_tool(_func=func, **kwargs):
        return _func(**kwargs)


free_funcs = ["search_duckduckgo", "search_wiki", "search_baidu", "search_bing"]
toolkit = SearchToolkit()
for func in toolkit.get_tools():
    func = func.func
    doc = func.__doc__
    name = func.__name__
    if name in free_funcs:
        @mcp.tool(description=doc, name=name) # MCP tool identification
        @copy_signature(func)
        async def func_tool(_func=func, **kwargs):
            return _func(**kwargs)

@mcp.tool() # MCP tool identification
async def example_func(example_arg: str) -> str:
    """Please provide a description of the function here.

    Args:
        example_arg: Describe the input here.
    """
    # Here is the specific function of the function.
    print(example_arg)
    return example_arg # Return a string.

if __name__ == "__main__":
    mcp.run(transport='stdio')
    # final_answer = paper_parse_func("Humanity’s Last Exam讲了啥")
    # print(final_answer)
    # import asyncio

    # async def main():
    #     query = "Humanity’s Last Exam讲了啥"
    #     result = await paper_parse_func(query)
    #     print(result)

    # asyncio.run(main())