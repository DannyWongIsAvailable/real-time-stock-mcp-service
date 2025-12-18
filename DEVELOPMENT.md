# 开发者文档

本文档面向想要扩展或修改本项目的开发者。

## 项目架构

### 核心设计模式：依赖注入

本项目采用依赖注入（Dependency Injection）设计模式，使得代码解耦、易于测试和扩展。

```
┌────────────────────┐
│  src/stock_mcp/app.py  │  ← 主入口，协调各个组件
└─────────┬──────────┘
          │
          ├─→ data_source_interface.py  ← 定义抽象接口
          │
          ├─→ stock_data_source.py   ← 具体实现
          │
          ├── utils/
          │   ├── utils.py    # 工具模块通用工具
          │   └── markdown_formatter.py   # Markdown格式化工具
          │
          ├── crawler/                   ← 网络爬虫模块
          │   ├── base_crawler.py        # 爬虫基类
          │   ├── basic_data.py          # 基础数据爬虫
          │   ├── real_time_data.py      # 实时数据爬虫
          │   ├── technical_data.py      # 技术数据爬虫
          │   ├── financial_analysis.py  # 财务分析爬虫
          │   ├── fundamental_data.py    # 基本面数据爬虫
          │   ├── market.py              # 市场行情爬虫
          │   ├── smart_review.py        # 智能点评爬虫
          │   ├── valuation_data.py      # 估值分析爬虫
          │   └── ...
          │
          └─→ mcp_tools/                     ← 各个MCP工具模块
               ├─ search.py                 ← 股票搜索和交易日信息
               ├─ real_time_data.py         ← 实时股票行情数据
               ├─ kline_data.py             ← K线数据和技术指标
               ├─ fundamental.py            ← 基本面数据（主营构成、经营范围等）
               ├─ valuation.py              ← 估值分析数据（市盈率、市净率等）
               ├─ financial_analysis.py      ← 财务分析数据（财务比率、业绩概况等）
               ├─ market.py                 ← 市场行情数据（板块行情、资金流向等）
               └─ smart_review.py           ← 智能点评和评分
```

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

项目包含8个MCP工具模块，每个模块提供特定领域的功能：

- `search.py` - 股票搜索和交易日信息
- `real_time_data.py` - 实时股票行情数据
- `kline_data.py` - K线数据和技术指标
- `fundamental.py` - 基本面数据（主营构成、经营范围等）
- `valuation.py` - 估值分析数据（市盈率、市净率等）
- `financial_analysis.py` - 财务分析数据（财务比率、业绩概况等）
- `market.py` - 市场行情数据（板块行情、资金流向等）
- `smart_review.py` - 智能点评和评分

## 环境要求

- Python 3.12+
- Windows/Linux/MacOS
- uv 包管理器

## 准备项目

1. 克隆项目
   ```bash
   git clone https://github.com/DannyWongIsAvailable/real-time-stock-mcp-service.git
   ```

2. 安装依赖
   ```bash
   pip install uv
   ```

3. 创建运行环境
   ```bash
   uv sync
   ```

4. 运行项目
   ```bash
   uv run python -m stock_mcp
   ```

## 爬虫模块说明

### 爬虫基类

项目中的所有网络爬虫都继承自 [EastMoneyBaseSpider](../src/crawler/base_crawler.py) 基类。该基类提供了通用的网络请求功能，包括：

- Session管理和请求封装
- 请求头/Cookies配置
- JSONP解析
- 股票代码格式转换

所有具体的爬虫类都应该继承这个基类，以复用这些通用功能。

## 如何添加新功能

### 1. 添加新的爬虫

如果你想添加一个新的爬虫来获取特定的数据，可以按照以下步骤进行：

#### 步骤 1: 创建新的爬虫类

在 [src/stock_mcp/crawler/](../src/stock_mcp/crawler/) 目录下创建新的爬虫文件，继承 [EastMoneyBaseSpider](../src/stock_mcp/crawler/base_crawler.py) 基类：

```python
# src/crawler/my_new_crawler.py
from .base_crawler import EastMoneyBaseSpider

class MyNewCrawler(EastMoneyBaseSpider):
    """新的数据爬虫示例"""
    
    def __init__(self, session=None, timeout=None):
        super().__init__(session, timeout)
        # 设置特定的请求头
        self.headers["Referer"] = "https://example.com/"
    
    def get_my_data(self, param: str):
        """获取特定数据"""
        url = "https://example.com/api/data"
        params = {"param": param}
        return self._get_json(url, params)
```

#### 步骤 2: 在数据源中使用新的爬虫

在 [WebCrawlerDataSource](../src/stock_mcp/stock_data_source.py) 中使用这个新的爬虫：

```python
# src/stock_data_source.py
from stock_mcp.crawler import MyNewCrawler


class WebCrawlerDataSource(FinancialDataInterface):
    def __init__(self):
        # 初始化新的爬虫
        self.my_new_crawler = MyNewCrawler()

    def get_my_data(self, param: str):
        """获取特定数据"""
        return self.my_new_crawler.get_my_data(param)
```

#### 步骤 3: 在接口中添加对应的方法

在 [data_source_interface.py](../src/stock_mcp/data_source_interface.py) 中添加对应的接口方法：

```python
@abstractmethod
def get_my_data(self, param: str) -> Dict[str, Any]:
    """
    获取特定数据
    
    Args:
        param: 参数说明
        
    Returns:
        返回数据格式
    """
    pass
```

### 2. 添加新的数据获取方法

如果需要添加新的数据获取功能（不涉及新的爬虫）：

#### 步骤 1: 在接口中定义方法

编辑 `src/stock_mcp/data_source_interface.py`:

```python
@abstractmethod
def get_new_feature_data(self, param: str) -> Dict[str, Any]:
    """
    获取新功能数据
    
    Args:
        param: 参数说明
        
    Returns:
        返回数据格式
    """
    pass
```

#### 步骤 2: 在具体实现中实现方法

编辑 `src/stock_mcp/stock_data_source.py`:

```python
def get_new_feature_data(self, param: str) -> Dict[str, Any]:
    """获取新功能数据"""
    data = self._make_request(f'/v1/new_feature/{param}')
    return data
```

### 3. 添加新的工具模块

#### 步骤 1: 创建工具模块文件

创建 `src/stock_mcp/mcp_tools/my_new_tool.py`:

```python
"""
我的新工具模块

提供xxx功能
"""

import logging
from mcp.server.fastmcp import FastMCP
from stock_mcp.data_source_interface import FinancialDataInterface

logger = logging.getLogger(__name__)


def register_my_new_tools(app: FastMCP, data_source: FinancialDataInterface):
    """
    注册我的新工具
    
    Args:
        app: FastMCP应用实例
        data_source: 数据源实例
    """

    @app.tool()
    def my_new_tool(param: str) -> str:
        """
        工具功能说明（这个docstring会显示给AI）
        
        详细说明这个工具的用途和使用方法。
        
        Args:
            param: 参数说明
            
        Returns:
            返回格式说明
            
        Examples:
            - my_new_tool("example1")
            - my_new_tool("example2")
        """
        try:
            logger.info(f"执行新工具: {param}")

            # 1. 使用data_source获取数据
            data = data_source.get_new_feature_data(param)

            # 2. 处理数据
            if not data:
                return "未找到数据"

            return data

        except Exception as e:
            logger.error(f"工具执行出错: {e}")
            return f"执行失败: {str(e)}"

    logger.info("我的新工具已注册")
```

#### 步骤 2: 在主文件中注册

编辑 `src/stock_mcp/app.py`:

```python
# 1. 导入注册函数
from stock_mcp.mcp_tools import register_my_new_tools

# 2. 在注册区域添加
register_my_new_tools(app, active_data_source)
```

### 4. 切换数据源

如果想使用其他数据源（如 Tushare、AKShare 等）：

#### 步骤 1: 创建新的数据源实现

创建 `src/stock_mcp/another_data_source.py`:

```python
from stock_mcp.data_source_interface import FinancialDataInterface


class AnotherDataSource(FinancialDataInterface):
    """另一个数据源实现"""

    def __init__(self):
        # 初始化代码
        pass

    def initialize(self) -> bool:
        # 实现初始化
        return True

    def cleanup(self):
        # 实现清理
        pass

    # 实现接口中的所有方法...
    def search_stock(self, keyword: str):
        # 使用新数据源的API
        pass
```

#### 步骤 2: 修改主文件

编辑 `src/stock_mcp/app.py`:

```python
# 修改这一行
from stock_mcp.another_data_source import AnotherDataSource

# 更改实例化
active_data_source: FinancialDataInterface = AnotherDataSource()
```

## 代码规范

### 1. 命名规范

- **文件名**: 使用小写字母和下划线，如 `stock_basic.py`
- **类名**: 使用大驼峰命名，如 `StockDataSource`
- **函数名**: 使用小写字母和下划线，如 `get_stock_info`
- **常量**: 使用大写字母和下划线，如 `MAX_RESULTS`

### 2. 文档字符串

每个函数都应该有清晰的文档字符串：

```python
def function_name(param1: str, param2: int) -> str:
    """
    简短的功能描述（一句话）
    
    详细的功能说明，可以多行。
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
        
    Examples:
        - function_name("test", 123)
        - function_name("demo", 456)
    """
    pass
```

### 3. 日志记录

合理使用日志：

```python
logger.info("一般信息")       # 正常流程信息
logger.debug("调试信息")      # 调试信息（详细）
logger.warning("警告信息")    # 警告（不影响运行）
logger.error("错误信息")      # 错误（需要关注）
```

### 4. 异常处理

所有工具函数都应该有异常处理：

```python
@app.tool()
def my_tool(param: str) -> str:
    try:
        # 主要逻辑
        result = do_something(param)
        return format_result(result)
    except SpecificException as e:
        logger.error(f"特定错误: {e}")
        return f"操作失败: {str(e)}"
    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        return f"发生错误: {str(e)}"
```

## 测试

### 单元测试

创建测试文件 `tests/test_my_tool.py`:

```python
import pytest
from stock_mcp.mcp_tools import register_my_new_tools
from unittest.mock import Mock

def test_my_new_tool():
    # 创建模拟的数据源
    mock_data_source = Mock()
    mock_data_source.get_new_feature_data.return_value = {"key": "value"}

    # 创建模拟的app
    mock_app = Mock()

    # 注册工具
    register_my_new_tools(mock_app, mock_data_source)

    # 验证注册成功
    assert mock_app.tool.called
```

运行测试:

```bash
uv run pytest tests/
```

### 集成测试

使用 `test_basic.py` 作为模板创建更多测试。

## 调试技巧

### 1. 启用详细日志

修改 `src/stock_mcp/app.py`:

```python
setup_logging(level=logging.DEBUG)
```

### 2. 独立测试工具

创建临时测试脚本:

```python
from stock_mcp.stock_data_source import WebCrawlerDataSource

# 测试某个功能
data_source = WebCrawlerDataSource()
data_source.initialize()

result = data_source.search_stock("贵州茅台")
print(result)

data_source.cleanup()
```

### 3. 使用Python调试器

```python
import pdb

def my_function():
    pdb.set_trace()  # 在这里设置断点
    # 代码继续...
```

## 常见问题

### Q: 如何添加新的K线周期？

**A**: 在 `get_kline_data` 方法中添加对新周期的支持，确保API支持该周期。

### Q: 如何优化API请求性能？

**A**: 可以考虑：

1. 添加缓存机制
2. 批量请求
3. 使用异步请求

### Q: 如何处理API限流？

**A**: 在 `_make_request` 方法中添加重试逻辑和延迟。

```python
import time

def _make_request_with_retry(self, endpoint, params, max_retries=3):
    for i in range(max_retries):
        try:
            return self._make_request(endpoint, params)
        except RateLimitError:
            if i < max_retries - 1:
                time.sleep(2 ** i)  # 指数退避
            else:
                raise
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 技术栈

- **Python**: 3.12+
- **MCP SDK**: FastMCP
- **HTTP客户端**: requests
- **包管理**: uv

## 参考资源

- [MCP 官方文档](https://docs.mcp.run)
- [FastMCP 文档](https://github.com/jlowin/fastmcp)

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。