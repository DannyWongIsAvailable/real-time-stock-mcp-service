# 快速开始指南

本指南将帮助你快速配置并运行股票数据 MCP Server。

## 1. 安装 uv 包管理器

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux/MacOS
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. 安装项目依赖

在项目根目录执行:

```bash
cd real-time-stock-mcp-service
uv sync
```

这将自动创建虚拟环境并安装所有依赖。

## 3. 配置 API 密钥 (可选)

如果需要 API 密钥，请创建 `.env` 文件:

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的 API Token:

```
STOCKAPI_TOKEN=你的API密钥
```

## 4. 测试运行

直接运行服务器:

```bash
uv run mcp_server.py
```

服务器将启动并等待 MCP 客户端连接。

## 5. 在 client中配置(Claude为例) 

### 5.1 找到配置文件

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`  

### 5.2 编辑配置文件

在配置文件中添加以下内容（注意替换路径）:

```json
{
  "mcpServers": {
    "stock-data": {
      "command": "uv",
      "args": [
        "--directory",
        "F:/path/to/your/project/real-time-stock-mcp-service",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

**重要**: 
- Windows 用户请使用双反斜杠 `\\` 或单斜杠 `/`
- 路径必须是绝对路径
- 不要使用 `~` 或环境变量

**Linux/MacOS 示例**:
```json
{
  "mcpServers": {
    "stock-data": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/username/projects/real-time-stock-mcp-service",
        "run",
        "mcp_server.py"
      ]
    }
  }
}

```

## 6. 查看日志

如需查看详细日志，可以修改 `mcp_server.py` 中的日志级别:

```python
setup_logging(level=logging.DEBUG)  # 改为 DEBUG 级别
```

## 7. 下一步

- 阅读 [README.md](README.md) 了解所有可用工具
- 查看项目结构了解如何添加新功能
- 探索各个工具模块的实现

## 需要帮助?

如遇到问题，请检查:
1. 日志输出
2. client 的错误信息
3. API 配置是否正确
4. 网络连接状态
