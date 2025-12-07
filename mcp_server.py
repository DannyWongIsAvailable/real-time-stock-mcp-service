"""
股票数据 MCP Server 主文件

这是MCP服务器的入口文件，负责：
1. 初始化数据源
2. 注册所有工具
3. 启动MCP服务器
"""

import logging
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# 导入数据源接口和具体实现
from src.data_source_interface import FinancialDataInterface
from src.stock_data_source import WebCrawlerDataSource
from src.utils.utils import setup_logging

# 导入各模块工具的注册函数
from src.mcp_tools.search import register_search_tools as register_crawler_search_tools
from src.mcp_tools.kline_data import register_kline_tools as register_crawler_kline_tools
from src.mcp_tools.real_time_data import register_real_time_data_tools as register_crawler_real_time_tools
from src.mcp_tools.fundamental import register_fundamental_tools as register_crawler_fundamental_tools
from src.mcp_tools.valuation import register_valuation_tools as register_crawler_valuation_tools
from src.mcp_tools.financial_analysis import register_financial_analysis_tools as register_crawler_financial_analysis_tools


# --- 日志配置 ---
# 设置日志级别，可以改为 logging.DEBUG 以获取更详细的日志
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 依赖注入 ---
# 实例化数据源，后续如需切换数据源，只需修改这一行
active_data_source: FinancialDataInterface = WebCrawlerDataSource()

# --- 获取当前日期用于系统提示 ---
current_date = datetime.now().strftime("%Y-%m-%d")

# --- FastMCP 应用初始化 ---
app = FastMCP(
    name="real-time-stock-mcp-service",
    instructions=f"""📊 一个获取实时股票数据服务和分析的MCP服务器

**今天日期**: {current_date}

📈 主要功能:
- 查找股票名称，代码
- 实时股票数据
- K线数据（日线、周线、月线）
- 计算技术指标
- 基本面数据（主营构成、经营范围、经营评述等）
- 估值分析数据（市盈率、市净率等）
"""
)

# --- 注册所有工具模块 ---
logger.info("开始注册工具模块...")

# 注册K线数据工具

register_crawler_search_tools(app, active_data_source)
register_crawler_real_time_tools(app, active_data_source)
register_crawler_kline_tools(app, active_data_source)
register_crawler_fundamental_tools(app, active_data_source)
register_crawler_valuation_tools(app, active_data_source)
register_crawler_financial_analysis_tools(app, active_data_source)

logger.info("所有工具模块注册完成")

# --- 主执行块 ---
if __name__ == "__main__":
    logger.info(f"🚀 启动股票数据 MCP Server... 今天是 {current_date}")
    logger.info(f"📡 数据源: {active_data_source.__class__.__name__}")
    
    # 初始化数据源
    if active_data_source.initialize():
        logger.info("✅ 数据源初始化成功")
    else:
        logger.warning("⚠️ 数据源初始化失败，某些功能可能不可用")
    
    try:
        # 使用 stdio 传输协议运行服务器
        # 这是 MCP Host（如 Claude Desktop）所需的标准方式
        app.run()
    except KeyboardInterrupt:
        logger.info("🛑 服务器被用户中断")
    except Exception as e:
        logger.exception(f"💥 服务器运行出错: {e}")
    finally:
        # 清理资源
        active_data_source.cleanup()
        logger.info("🧹 资源清理完成，再见！")