#!/usr/bin/env python3
"""
抖音无水印视频文本提取 MCP 服务器 - HTTP 版本
支持通过 HTTP/SSE 协议远程访问
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import os
import sys

# 创建 FastAPI 应用
app = FastAPI(
    title="Douyin MCP Server",
    description="抖音无水印视频文本提取 MCP 服务器",
    version="1.2.0"
)

# 配置 CORS - 重要！允许跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # 必须暴露这个头
)

# 创建 MCP 服务器实例
mcp = FastMCP(
    "Douyin MCP Server",
    stateless_http=True,  # 无状态模式
    json_response=True    # 使用 JSON 响应
)

# 注册工具 1：获取抖音无水印视频下载链接
@mcp.tool()
def get_douyin_download_link(share_link: str) -> dict:
    """
    获取抖音无水印视频下载链接
    
    Args:
        share_link: 抖音分享链接或包含链接的文本
    
    Returns:
        包含视频信息和下载链接的字典
    """
    try:
        # 导入原有的 API 模块
        from douyin_mcp_server.douyin_api import get_download_link
        result = get_download_link(share_link)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "message": "获取下载链接失败"
        }

# 注册工具 2：提取抖音视频文案
@mcp.tool()
def extract_douyin_text(share_link: str, model: str = "paraformer-v2") -> str:
    """
    提取抖音视频文案（包含语音识别）
    
    Args:
        share_link: 抖音分享链接或包含链接的文本
        model: 语音识别模型，默认 paraformer-v2
    
    Returns:
        提取的文本内容
    """
    try:
        # 检查 API Key
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return "错误：未设置 DASHSCOPE_API_KEY 环境变量，请在部署时配置阿里云百炼 API 密钥"
        
        # 导入原有的 API 模块
        from douyin_mcp_server.douyin_api import extract_text
        result = extract_text(share_link, api_key, model)
        return result
    except Exception as e:
        return f"错误：{str(e)}"

# 挂载 MCP 到 FastAPI
# 这会在 /mcp 路径上暴露 MCP 端点
app.mount("/mcp", mcp.streamable_http_app())

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "douyin-mcp-server",
        "version": "1.2.0",
        "mcp_endpoint": "/mcp"
    }

# 根路径信息
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "抖音 MCP 服务器运行中",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "docs": "/docs"
        },
        "tools": [
            "get_douyin_download_link",
            "extract_douyin_text"
        ]
    }

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量读取端口，默认 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 启动抖音 MCP 服务器...")
    print(f"📡 监听地址: http://0.0.0.0:{port}")
    print(f"🔗 MCP 端点: http://0.0.0.0:{port}/mcp")
    print(f"💚 健康检查: http://0.0.0.0:{port}/health")
    print(f"📖 API 文档: http://0.0.0.0:{port}/docs")
    
    # 检查必需的环境变量
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("⚠️  警告：未设置 DASHSCOPE_API_KEY 环境变量")
        print("   文本提取功能将无法使用")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
