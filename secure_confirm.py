"""
自动确认发货模块 - 明文版本（安全修复）
原混淆版本已备份为 secure_confirm_ultra.py.bak
"""
import time
import asyncio
import json
from utils.xianyu_utils import trans_cookies, generate_sign
from loguru import logger


class SecureConfirm:
    def __init__(self, session, cookies_str, cookie_id):
        self.session = session
        self.cookies_str = cookies_str
        self.cookie_id = cookie_id
        self.current_token = None
        self.last_token_refresh_time = 0
        self.token_refresh_interval = 3600
        # 解析cookies字符串为字典
        self.cookies = {}
        if cookies_str:
            for cookie in cookies_str.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    self.cookies[key] = value

    async def refresh_token(self):
        """刷新token的方法 - 这里需要从主类中复制相关逻辑"""
        # 这里需要实现token刷新逻辑
        pass

    async def update_config_cookies(self):
        """更新数据库中的Cookie配置"""
        try:
            from db_manager import db_manager
            # 更新数据库中的cookies
            db_manager.update_cookie_value(self.cookie_id, self.cookies_str)
            logger.debug(f"【{self.cookie_id}】已更新数据库中的Cookie")
        except Exception as e:
            logger.error(f"【{self.cookie_id}】更新数据库Cookie失败: {self._safe_str(e)}")

    def _safe_str(self, obj):
        """安全字符串转换"""
        try:
            return str(obj)
        except:
            return "无法转换的对象"

    async def auto_confirm(self, order_id, retry_count=0):
        """自动确认发货"""
        if retry_count >= 4:  # 最多重试3次
            logger.error("自动确认发货失败，重试次数过多")
            return {"error": "自动确认发货失败，重试次数过多"}

        # 如果是重试（retry_count > 0），强制刷新token
        if retry_count > 0:
            old_token = trans_cookies(self.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.cookies_str).get('_m_h5_tk') else ''
            logger.info(f"重试第{retry_count}次，强制刷新token... 当前_m_h5_tk: {old_token}")
            await self.refresh_token()
            new_token = trans_cookies(self.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.cookies_str).get('_m_h5_tk') else ''
            logger.info(f"重试刷新token完成，新的_m_h5_tk: {new_token}")
        else:
            # 确保使用最新的token（首次调用时的正常逻辑）
            if not self.current_token or (time.time() - self.last_token_refresh_time) >= self.token_refresh_interval:
                old_token = trans_cookies(self.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.cookies_str).get('_m_h5_tk') else ''
                logger.info(f"Token过期或不存在，刷新token... 当前_m_h5_tk: {old_token}")
                await self.refresh_token()
                new_token = trans_cookies(self.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.cookies_str).get('_m_h5_tk') else ''
                logger.info(f"Token刷新完成，新的_m_h5_tk: {new_token}")

        # 确保session已创建
        if not self.session:
            raise Exception("Session未创建")

        params = {
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': str(int(time.time()) * 1000),
            'sign': '',
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': 'mtop.taobao.idle.logistic.consign.dummy',
            'sessionOption': 'AutoLoginOnly',
        }

        data_val = '{"orderId":"' + order_id + '", "tradeText":"","picList":[],"newUnconsign":true}'
        data = {
            'data': data_val,
        }

        # 始终从最新的cookies中获取_m_h5_tk token（刷新后cookies会被更新）
        token = trans_cookies(self.cookies_str).get('_m_h5_tk', '').split('_')[0] if trans_cookies(self.cookies_str).get('_m_h5_tk') else ''

        if token:
            logger.info(f"使用cookies中的_m_h5_tk token: {token}")
        else:
            logger.warning("cookies中没有找到_m_h5_tk token")

        sign = generate_sign(params['t'], token, data_val)
        params['sign'] = sign

        try:
            logger.info(f"【{self.cookie_id}】开始自动确认发货，订单ID: {order_id}")
            async with self.session.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.logistic.consign.dummy/1.0/',
                params=params,
                data=data
            ) as response:
                res_json = await response.json()

                # 检查并更新Cookie
                if 'set-cookie' in response.headers:
                    new_cookies = {}
                    for cookie in response.headers.getall('set-cookie', []):
                        if '=' in cookie:
                            name, value = cookie.split(';')[0].split('=', 1)
                            new_cookies[name.strip()] = value.strip()

                    # 更新cookies
                    if new_cookies:
                        self.cookies.update(new_cookies)
                        # 生成新的cookie字符串
                        self.cookies_str = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
                        # 更新数据库中的Cookie
                        await self.update_config_cookies()
                        logger.debug("已更新Cookie到数据库")

                logger.info(f"【{self.cookie_id}】自动确认发货响应: {res_json}")

                # 检查响应结果
                if res_json.get('ret') and res_json['ret'][0] == 'SUCCESS::调用成功':
                    logger.info(f"【{self.cookie_id}】✅ 自动确认发货成功，订单ID: {order_id}")
                    return {"success": True, "order_id": order_id}
                else:
                    error_msg = res_json.get('ret', ['未知错误'])[0] if res_json.get('ret') else '未知错误'
                    logger.warning(f"【{self.cookie_id}】❌ 自动确认发货失败: {error_msg}")

                    # 如果是token相关错误，进行重试
                    if 'token' in error_msg.lower() or 'sign' in error_msg.lower():
                        logger.info(f"【{self.cookie_id}】检测到token错误，准备重试...")
                        return await self.auto_confirm(order_id, retry_count + 1)

                    return {"error": error_msg, "order_id": order_id}

        except Exception as e:
            logger.error(f"【{self.cookie_id}】自动确认发货API请求异常: {self._safe_str(e)}")
            await asyncio.sleep(0.5)

            # 网络异常也进行重试
            if retry_count < 2:
                logger.info(f"【{self.cookie_id}】网络异常，准备重试...")
                return await self.auto_confirm(order_id, retry_count + 1)

            return {"error": f"网络异常: {self._safe_str(e)}", "order_id": order_id}
