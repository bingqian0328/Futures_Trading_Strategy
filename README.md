# 期货自动交易策略 / Futures Auto Trading Strategy

一个基于 Python 的币安期货测试网自动交易策略，支持实时价格监听、智能下单和风险控制。

## 🎯 功能特性

### 核心功能
- 📈 **实时价格监听**: 通过 WebSocket 监听 BTCUSDT bookTicker 数据流
- 🤖 **自动交易**: 每 3-7 秒随机执行买入/卖出操作
- 💰 **智能定价**: 买单为中间价的 95%，卖单为中间价的 105%
- 🛡️ **风险控制**: 每 5 笔订单后自动撤销所有挂单
- 🔄 **断线重连**: 支持 WebSocket 自动重连机制

### 技术特性
- ⚡ **异步编程**: 基于 asyncio 的高性能异步架构
- 🔐 **安全认证**: 支持 API 密钥配置文件和环境变量
- 📊 **详细日志**: 完整的交易日志和状态监控
- 🎨 **用户友好**: 清晰的中文界面和 emoji 状态指示

## 📋 系统要求

### 环境要求
- Python 3.7+
- 币安期货测试网账户
- 稳定的网络连接

### 依赖库
```bash
aiohttp>=3.8.0
websockets>=10.0
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd CoinW_TechnicalTest
```

### 2. 创建虚拟环境
```bash
# macOS/Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. 安装依赖
```bash
pip install aiohttp websockets
```

### 4. 配置 API 密钥

#### 方法一：配置文件（推荐）
编辑 `config.py` 文件：
```python
API_KEY = "your_testnet_api_key"
API_SECRET = "your_testnet_api_secret"
```

#### 方法二：环境变量
```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```

### 5. 运行程序
```bash
python Q1.py
```

## ⚙️ 配置参数

### 交易参数
```python
ORDER_QUANTITIES = [0.004, 0.005, 0.006, 0.007]  # 随机下单数量池
BUY_PRICE_RATIO = 0.95   # 买单价格为中间价的95%
SELL_PRICE_RATIO = 1.05  # 卖单价格为中间价的105%
CANCEL_ORDER_COUNT = 5   # 每5笔订单后撤销所有挂单
```

### 网络参数
```python
WS_PING_INTERVAL = 20    # WebSocket ping 间隔
WS_PING_TIMEOUT = 20     # WebSocket ping 超时
MAX_RETRY_COUNT = 6      # 最大重试次数
RETRY_BASE_DELAY = 2     # 重试基础延迟
```

### 环境配置
```python
WS_BASE_URL = "wss://stream.binancefuture.com"      # WebSocket 基础URL
REST_BASE_URL = "https://testnet.binancefuture.com"  # REST API 基础URL
TRADING_SYMBOL = "BTCUSDT"                          # 交易对
```

## 📊 运行示例

```
🚀 启动币安期货自动交易策略...
📊 交易对: BTCUSDT
🌐 测试网地址: https://testnet.binancefuture.com
🔗 正在连接到 wss://stream.binancefuture.com/ws/btcusdt@bookTicker ...
✅ 已连接。正在监听 BTCUSDT 最优买卖价 (测试网)...
💰 [BTCUSDT] 买价: 43250.12 | 卖价: 43251.34

📈 下单 → BUY 0.005 @ 41087.6
✅ 下单结果: HTTP 200 | {"orderId":12345}

📈 下单 → SELL 0.006 @ 45413.9
✅ 下单结果: HTTP 200 | {"orderId":12346}

🔄 达到撤单条件，等待2秒后撤销所有订单...
❌ 正在撤销所有订单...
❌ 撤单结果: HTTP 200 | {"code":200,"msg":"All orders canceled"}
```

## 🏗️ 项目结构

```
CoinW_TechnicalTest/
├── Q1.py              # 主程序文件
├── Q2.py              # 扑克牌概率计算
├── config.py          # API密钥配置文件
├── README.md          # 项目说明文档
└── venv/              # 虚拟环境目录
```

## 📚 代码架构

### 核心类设计
- **BinanceClient**: 币安 API 客户端，处理所有 API 交互
- **Trader**: 交易策略执行器，实现交易逻辑和风险控制
- **websocket_listener**: WebSocket 监听器，获取实时市场数据

### 模块分层
1. **配置层**: 参数配置和环境变量管理
2. **工具层**: API 签名生成和时间戳工具
3. **业务层**: 交易逻辑和订单管理
4. **数据层**: WebSocket 数据流处理
5. **主程序**: 程序入口和协程管理

## 🛡️ 安全特性

### API 密钥安全
- ✅ 支持配置文件和环境变量两种方式
- ✅ 配置文件不包含在版本控制中
- ✅ 仅支持测试网环境，无真实资金风险

### 异常处理
- ✅ WebSocket 连接异常自动重连
- ✅ API 调用失败处理和重试
- ✅ 数据解析错误捕获
- ✅ 程序优雅退出机制

## 🔧 故障排除

### 常见问题

**Q: 出现 `-4164` 错误怎么办？**
A: 这表示订单名义价值小于 100 USDT。程序会自动调整数量以满足最小名义价值要求。

**Q: WebSocket 连接失败？**
A: 检查网络连接，程序会自动重连。如果持续失败，可能是网络问题。

**Q: API 密钥无效？**
A: 确认使用的是币安期货测试网的 API 密钥，不是现货或主网密钥。

**Q: 程序运行但不下单？**
A: 检查 API 密钥配置是否正确，确认测试网账户余额充足。

### 调试模式
如需调试，可以修改日志级别或添加更详细的输出信息。
