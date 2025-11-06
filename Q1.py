"""
币安期货测试网自动交易策略
功能：
1. 实时监听 bookTicker 获取最优买卖价
2. 随机下单（多空各50%概率）
3. 每5笔订单后自动撤销所有挂单
"""

import asyncio
import json
import os
import time
import hmac
import hashlib
import random
import urllib.parse
from typing import Optional, Tuple

import aiohttp
import websockets

# =========================== 配置参数 ===========================

# API密钥配置（优先使用config.py文件，次选环境变量）
try:
    from config import API_KEY, API_SECRET
except ImportError:
    API_KEY = os.getenv("BINANCE_API_KEY", "")
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# 测试网配置
WS_BASE_URL = os.getenv("WS_BASE", "wss://stream.binancefuture.com")
REST_BASE_URL = os.getenv("REST_BASE", "https://testnet.binancefuture.com")
TRADING_SYMBOL = os.getenv("SYMBOL", "BTCUSDT").upper()

# 交易参数
ORDER_QUANTITIES = [0.004, 0.005, 0.006, 0.007]  # 随机下单数量池
BUY_PRICE_RATIO = 0.95   # 买单价格为中间价的95%
SELL_PRICE_RATIO = 1.05  # 卖单价格为中间价的105%
CANCEL_ORDER_COUNT = 5   # 每5笔订单后撤销所有挂单

# WebSocket重连参数
WS_PING_INTERVAL = 20
WS_PING_TIMEOUT = 20
MAX_RETRY_COUNT = 6
RETRY_BASE_DELAY = 2

# =========================== 工具函数(Utility Layer) ===========================

def sign_query(params: dict, secret: str) -> str:
    """
    生成Binance API签名
    :param params: 请求参数字典
    :param secret: API密钥
    :return: HMAC SHA256签名
    """
    query = urllib.parse.urlencode(params)
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


def timestamp_ms() -> int:
    """
    获取当前时间戳（毫秒）
    :return: 13位时间戳
    """
    return int(time.time() * 1000)


# =========================== 核心类定义 ===========================

class BinanceClient:
    """
    币安期货API客户端
    负责处理与币安期货API的交互，包括下单和撤单
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        """
        初始化客户端
        :param api_key: API密钥
        :param api_secret: API密钥密码
        :param base_url: API基础URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def ensure_session(self) -> None:
        """确保HTTP会话已创建"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"X-MBX-APIKEY": self.api_key}
            )

    async def close(self) -> None:
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None

    async def place_order(self, symbol: str, side: str, price: str, qty: str) -> Tuple[int, str]:
        """
        下限价单
        :param symbol: 交易对
        :param side: 买卖方向（BUY/SELL）
        :param price: 价格
        :param qty: 数量
        :return: (HTTP状态码, 响应内容)
        """
        await self.ensure_session()
        url = f"{self.base_url}/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": qty,
            "price": price,
            "timestamp": timestamp_ms(),
        }
        params["signature"] = sign_query(params, self.api_secret)
        
        async with self.session.post(url, data=params) as resp:
            return resp.status, await resp.text()

    async def cancel_all_orders(self, symbol: str) -> Tuple[int, str]:
        """
        撤销指定交易对的所有挂单
        :param symbol: 交易对
        :return: (HTTP状态码, 响应内容)
        """
        await self.ensure_session()
        url = f"{self.base_url}/fapi/v1/allOpenOrders"
        params = {"symbol": symbol, "timestamp": timestamp_ms()}
        params["signature"] = sign_query(params, self.api_secret)
        
        async with self.session.delete(url, params=params) as resp:
            return resp.status, await resp.text()

class Trader:
    """
    交易策略执行器
    负责执行自动交易逻辑和订单管理
    """
    
    def __init__(self, client: BinanceClient, symbol: str):
        """
        初始化交易器
        :param client: API客户端实例
        :param symbol: 交易对符号
        """
        self.client = client
        self.symbol = symbol
        self.bid: Optional[float] = None
        self.ask: Optional[float] = None
        self.order_count = 0
        self.running = True

    def update_ticker(self, bid: float, ask: float) -> None:
        """
        更新最新买卖价
        :param bid: 最新买价
        :param ask: 最新卖价
        """
        self.bid, self.ask = bid, ask

    def get_mid_price(self) -> Optional[float]:
        """
        计算中间价
        :return: 中间价或None（如果价格未就绪）
        """
        if self.bid and self.ask:
            return (self.bid + self.ask) / 2
        return None

    async def trade_loop(self) -> None:
        """
        主交易循环
        每3-7秒随机下一个买单或卖单
        """
        while self.running:
            # 随机等待3-7秒
            await asyncio.sleep(random.uniform(3, 7))
            
            # 获取当前中间价
            mid_price = self.get_mid_price()
            if not mid_price:
                print("📊 等待最新报价中...")
                continue

            # 随机选择买卖方向
            side = random.choice(["BUY", "SELL"])
            qty = str(random.choice(ORDER_QUANTITIES))

            # 根据方向计算限价
            if side == "BUY":
                limit_price = f"{mid_price * BUY_PRICE_RATIO:.1f}"
            else:
                limit_price = f"{mid_price * SELL_PRICE_RATIO:.1f}"

            # 执行下单
            print(f"\n📈 下单 → {side} {qty} @ {limit_price}")
            status, resp = await self.client.place_order(
                self.symbol, side, limit_price, qty
            )
            print(f"✅ 下单结果: HTTP {status} | {resp}")

            # 更新订单计数
            self.order_count += 1
            
            # 每5笔订单后撤销所有挂单
            if self.order_count >= CANCEL_ORDER_COUNT:
                await asyncio.sleep(2)  # 等待2秒
                print("❌ 正在撤销所有订单...")
                status, response = await self.client.cancel_all_orders(self.symbol)
                print(f"❌ 撤单结果: HTTP {status} | {response}")
                self.order_count = 0

# =========================== WebSocket监听器 ===========================

async def websocket_listener(uri: str, trader: Trader) -> None:
    """
    WebSocket连接监听器，负责获取实时价格数据
    """
    retry_count = 0
    
    while True:
        try:
            print(f"🔗 正在连接到 {uri} ...")
            
            async with websockets.connect(
                uri, 
                ping_interval=WS_PING_INTERVAL, 
                ping_timeout=WS_PING_TIMEOUT
            ) as websocket:
                print(f"✅ 已连接。正在监听 {TRADING_SYMBOL} 最优买卖价 (测试网)...")
                retry_count = 0  # 重置重试计数
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        # 兼容不同的数据格式
                        payload = data.get("data", data)
                        
                        bid = float(payload["b"])  # 最优买价
                        ask = float(payload["a"])  # 最优卖价
                        
                        trader.update_ticker(bid, ask)
                        print(f"💰 [{payload['s']}] 买价: {bid:.2f} | 卖价: {ask:.2f}", end="\r")
                        
                    except (KeyError, ValueError) as e:
                        print(f"⚠️ 数据解析错误: {e}")
                        
        except Exception as e:
            retry_count = min(retry_count + 1, MAX_RETRY_COUNT)
            wait_time = min(RETRY_BASE_DELAY ** retry_count, 30)
            print(f"❌ WebSocket连接错误: {e}")
            print(f"🔄 {wait_time}秒后重连 (第{retry_count}次重试)...")
            await asyncio.sleep(wait_time)


# =========================== 主程序 ===========================

async def main():
    """主程序入口"""
    print(f"📊 交易对: {TRADING_SYMBOL}")
    print(f"🌐 测试网地址: {REST_BASE_URL}")
    
    # 构建WebSocket流地址
    stream = f"{TRADING_SYMBOL.lower()}@bookTicker"
    websocket_uri = f"{WS_BASE_URL}/ws/{stream}"
    
    # 创建客户端和交易器
    client = BinanceClient(API_KEY, API_SECRET, REST_BASE_URL)
    trader = Trader(client, TRADING_SYMBOL)
    
    try:
        # 并发运行WebSocket监听和交易循环
        await asyncio.gather(
            websocket_listener(websocket_uri, trader),
            trader.trade_loop()
        )
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭...")
    finally:
        await client.close()
        print("👋 程序已退出")


if __name__ == "__main__":
    """
    运行说明：
    1. 确保已配置API密钥（config.py或环境变量）
    2. 安装依赖：pip install aiohttp websockets
    3. 运行：python Q1.py
    """
    asyncio.run(main())
