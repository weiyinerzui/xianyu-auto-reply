"""商品详情提取工具

处理 item_detail 字段的三种形态：
1. 真实描述纯文本（浏览器抓取 / 用户手动编辑）
2. 商品列表卡片的 JSON dump（save_items_list_to_db 首次同步写入，非真实描述）
3. 旧版 {"detail": "..."} 包装格式
"""
import json
from typing import Optional

# mtop.taobao.idle.pc.detail 响应中的描述字段候选（按优先级排列）
DETAIL_DESC_KEYS = ('itemDescMulti', 'itemDesc', 'detailDesc', 'description', 'desc')


def extract_real_item_detail(item_detail) -> Optional[str]:
    """从 item_detail 字段值中提取真实商品描述文本

    Args:
        item_detail: 数据库 item_detail 字段值（str 或空值）

    Returns:
        真实描述文本；无有效详情（JSON卡片dump / 空）返回 None
    """
    if not item_detail or not str(item_detail).strip():
        return None
    text = str(item_detail).strip()
    if not text.startswith('{'):
        return text
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        # 看似JSON但解析失败，按纯文本处理
        return text
    if isinstance(data, dict):
        # 旧版 {"detail": "..."} 包装格式
        inner = data.get('detail')
        if isinstance(inner, str) and inner.strip():
            return inner.strip()
        # 无 detail 键的 JSON 对象 → 商品卡片元数据 dump，非真实描述
        return None
    return text


def extract_desc_from_detail_api(node, depth: int = 0) -> str:
    """递归从商品详情API响应中提取描述文本

    防御式解析：不依赖固定字段路径（接口结构可能变化），
    按 DETAIL_DESC_KEYS 优先级在任意嵌套层级查找第一个非空字符串值。

    Args:
        node: API响应的任意子节点（dict / list / 标量）
        depth: 当前递归深度，防止过深嵌套

    Returns:
        描述文本；未找到返回空字符串
    """
    if depth > 12 or node is None:
        return ''
    if isinstance(node, dict):
        # 优先匹配本层的高优先级键（itemDescMulti > itemDesc > ...）
        for key in DETAIL_DESC_KEYS:
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        # 递归子节点
        for value in node.values():
            found = extract_desc_from_detail_api(value, depth + 1)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = extract_desc_from_detail_api(value, depth + 1)
            if found:
                return found
    return ''
