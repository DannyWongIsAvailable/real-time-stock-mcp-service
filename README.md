# 实时股票分析 MCP 服务

---

这是一个实时股票数据服务的MCP（Model Context Protocol）服务器。它通过东方财富网获取金融数据，并将这些数据以工具的形式暴露给支持MCP的AI模型。

> **项目地址：** https://github.com/DannyWongIsAvailable/real-time-stock-mcp-service.git

- 免费免登录获取数据，免数据源token
- 部分功能支持B股，H股

## 功能特性

- 📊 查找股票
- 📈 K线数据查询（日线、周线、月线等）
- 📉 技术指标分析
- 💰 基本面数据分析
- 📊 财务分析
- 📈 市场行情跟踪
- 🤖 智能点评和评分  
共33个MCP工具

## 使用方法

您可以通过以下2种方式使用本服务：

### 1. 魔搭社区一键云部署

您可以在魔搭社区MCP实验场在线体验该服务，也支持远程连接客户端（streamable HTTP或SSE协议）

https://modelscope.cn/mcp/servers/DannyWong/real-time-stock-mcp

### 2. 本地stdio模式(以Claude Desktop为例)

#### 在 Claude Desktop 中配置

编辑 Claude Desktop 的配置文件：

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**MacOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  

添加以下配置：

```json
{
  "mcpServers": {
    "stock-mcp": {
      "args": [
        "real-time-stock-mcp-service"
      ],
      "command": "uvx"
    }
  }
}
```

> **注意：** 将路径替换为你的实际项目路径。


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

项目包含33个MCP工具模块，每个模块提供特定领域的功能：

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