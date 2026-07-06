# 实时股票分析 MCP 服务

---

这是一个实时股票数据服务的MCP服务器。它通过东方财富网和雪球网获取金融数据，并将这些数据以工具的形式暴露给支持MCP的Agent。

> **代码仓库：** https://github.com/DannyWongIsAvailable/real-time-stock-mcp-service.git

- 免费免登录获取数据

## 功能特性

- 📊 查找股票
- 📈 K线数据查询（支持B股，H股，大盘，分时图）
- 📉 技术指标分析 （MA，MACD，BOLL，RSI等等）
- 💰 基本面数据分析（主营构成、经营范围等）
- 📊 财务分析（财务比率、业绩概况等）
- 💰 估值分析数据（市盈率、市净率等）
- 📈 市场行情跟踪（板块行情、同行对比、资金流向等）
- 🤖 智能点评和评分  

共34个MCP工具

## 使用方法

您可以通过以下3种方式使用本服务：

### 1. 魔搭社区免费云资源一键部署

您可以在魔搭社区MCP实验场中在线体验该服务，也支持客户端远程连接（streamable HTTP或SSE协议）

https://modelscope.cn/mcp/servers/DannyWong/real-time-stock-mcp

### 2. 本地stdio模式(安装软件包运行)

添加以下配置：

```json
{
  "mcpServers": {
    "stock-mcp": {
      "command": "uvx",
      "args": [
        "real-time-stock-mcp-service"
      ],
      "env": {
        "EASTMONEY_COOKIE": "从浏览器复制的东方财富 Cookie",
        "XUEQIU_COOKIE": "从浏览器复制的雪球 Cookie"
      }
    }
  }
}
```

### 3. 本地stdio模式(源代码运行)

```json
{
  "mcpServers": {
    "stock-mcp": {
      "command": "path/to/python.exe",
      "args": ["-m", "stock_mcp"],
      "cwd": "path/to/real-time-stock-mcp-service",
      "env": {
        "EASTMONEY_COOKIE": "从浏览器复制的东方财富 Cookie",
        "XUEQIU_COOKIE": "从浏览器复制的雪球 Cookie"
      }
    }
  }
}
```

> **注意：** 将路径替换为你的实际项目路径。

### Cookie 环境变量

部分接口（如东方财富 datacenter、雪球实时行情/K 线）需要浏览器 Cookie 才能正常访问。请在 MCP 配置的 `env` 字段中设置：

| 环境变量 | 说明 |
|----------|------|
| `EASTMONEY_COOKIE` | 东方财富 Cookie，用于 datacenter、push2 等接口 |
| `XUEQIU_COOKIE` | 雪球 Cookie，用于实时行情、K 线等接口 |
| `LOG_LEVEL` | 可选，日志级别，默认 `INFO` |

**获取 Cookie：**

1. 浏览器登录 [eastmoney.com](https://www.eastmoney.com) 或 [xueqiu.com](https://xueqiu.com)
2. 打开开发者工具（F12）→ Network → 任意请求 → Request Headers
3. 复制 `Cookie` 字段的完整内容，填入 MCP 配置对应环境变量

Cookie 会过期，若出现 403 或数据异常，重新复制并更新配置后重启 MCP 服务即可。

> **安全提示：** 请勿将 Cookie 写入源码或提交到 Git，仅保存在本机 MCP 配置中。


#### 视频教程参考：
- [火遍全网的MCP是什么？怎么用？如何自己开发一个MCP服务？一个视频带你入门！](https://www.bilibili.com/video/BV13R5EzbE6E/?spm_id_from=333.337.search-card.all.click&vd_source=08fc400fe0cfc7eaa723687b764b29f3)
- [Cherry Studio MCP 使用入门教程：从配置到使用](https://www.bilibili.com/video/BV1bkdAYTEYp/?spm_id_from=333.337.search-card.all.click&vd_source=08fc400fe0cfc7eaa723687b764b29f3)

## 核心设计

本项目采用**依赖注入**设计模式：

1. `crawler` 模块获取数据
2. `data_source_interface.py` 定义抽象数据源接口
3. `stock_data_source.py` 提供具体实现
4. 各工具模块通过依赖注入获取数据源实例

这种设计使得：
- ✅ 易于扩展新功能
- ✅ 可以轻松切换不同数据源
- ✅ 便于单元测试
- ✅ 代码解耦，维护性强

## 工具模块

项目包含34个MCP工具模块，每个模块提供特定领域的功能：

- `search.py` - 股票搜索和交易日信息
- `real_time_data.py` - 实时股票行情数据
- `kline_data.py` - K线数据和技术指标
- `fundamental.py` - 基本面数据（主营构成、经营范围等）
- `valuation.py` - 估值分析数据（市盈率、市净率等）
- `financial_analysis.py` - 财务分析数据（财务比率、业绩概况等）
- `market.py` - 市场行情数据（板块行情、资金流向等）
- `smart_review.py` - 智能点评和评分


## 开发指南

详情请查看[开发指南](DEVELOPMENT.md)  

## 注意事项

⚠️ **重要提醒**：
1. 本服务提供的数据仅供参考，不构成投资建议
2. 仅允许个人学习、研究、使用，禁止用于商业用途。严禁滥用！
3. 请遵守数据使用协议和相关法律法规

## 开源协议

[MIT License](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue 或联系项目开发者。  
求一个star，感激不尽！