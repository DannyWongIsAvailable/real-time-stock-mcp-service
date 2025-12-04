# 实时股票 MCP 服务

这是一个实时股票数据服务的MCP（Model Context Protocol）服务器。它通过东方财富网获取金融数据，并将这些数据以工具的形式暴露给支持MCP的AI模型。

## 功能特性

- 📊 查找股票
- 📈 K线数据查询（日线、周线、月线等）
- 📉 计算技术指标
- 待开发...
## 环境要求

- Python 3.12+
- Windows/Linux/MacOS
- uv 包管理器

## 安装步骤

### 1. 安装 uv 包管理器

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/MacOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 克隆或下载项目

```bash
git clone https://github.com/DannyWongIsAvailable/real-time-stock-mcp-service.git
cd real-time-stock-mcp-service
```

### 3. 使用 uv 安装依赖

```bash
uv sync
```

### 4. 配置 API 密钥

在项目根目录创建 `.env` 文件（可选，如果API需要密钥）：

```
STOCKAPI_TOKEN=your_api_token_here
```

## 使用方法

### 直接运行服务器

```bash
uv run mcp_server.py
```

### client 中配置

编辑 Claude Desktop 的配置文件：

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**MacOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

添加以下配置：

```json
{
  "mcpServers": {
    "stock-data": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\real-time-stock-mcp-service",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

注意：将路径替换为你的实际项目路径。

## 项目结构

```
real-time-stock-mcp-service/
├── mcp_server.py              # MCP服务器主文件
├── pyproject.toml             # 项目配置文件
├── README.md                  # 项目说明文档
├── .env                       # 环境变量配置（需自行创建）
└── src/
    ├── data_source_interface.py    # 数据源接口定义
    ├── stock_data_source.py     # 东方财富网数据源实现
    ├── utils.py                    # 通用工具函数
    ├── formatting/
    │   └── markdown_formatter.py   # Markdown格式化工具（废弃）
    └── tools/  # 工具模块

```

## 核心设计

本项目采用**依赖注入**设计模式：

1. `data_source_interface.py` 定义抽象数据源接口
2. `stock_data_source.py` 提供具体实现
3. 各工具模块通过依赖注入获取数据源实例

这种设计使得：
- ✅ 易于扩展新功能
- ✅ 可以轻松切换不同数据源
- ✅ 便于单元测试
- ✅ 代码解耦，维护性强



## 开发指南

### 添加新工具

1. 在 `src/tools/` 目录创建新的工具模块
2. 实现工具函数并定义注册函数
3. 在 `mcp_server.py` 中导入并注册

示例：

```python
# src/tools/my_new_tool.py
from mcp.server.fastmcp import FastMCP
from src.data_source_interface import StockDataSource

def register_my_tools(app: FastMCP, data_source: StockDataSource):
    @app.tool()
    def my_new_tool(param: str) -> str:
        """工具描述"""
        # 使用 data_source 获取数据
        data = data_source.get_some_data(param)
        return format_data(data)
```

### 切换数据源

只需修改 `mcp_server.py` 中的数据源实例化代码：

```python
# 原来
active_data_source: StockDataSource = StockAPIDataSource()

# 切换为其他数据源
active_data_source: StockDataSource = AnotherDataSource()
```

## 注意事项

⚠️ **重要提醒**：
1. 本服务提供的数据仅供参考，不构成投资建议
2. 数据存在延迟，请以实际交易所数据为准
3. 请遵守数据使用协议和相关法律法规

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。
