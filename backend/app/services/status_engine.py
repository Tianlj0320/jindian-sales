"""
订单状态引擎（V4.0）
单一定义所有状态流转规则，避免分散在各处
"""

from __future__ import annotations

from typing import Any

# ── 订单状态配置 ──────────────────────────────────────────────
# 每个state: label(显示名), color(颜色), next(可跳转状态列表)
ORDER_STATUS_CONFIG: dict[str, dict[str, Any]] = {
    # V4.0 量尺前置流程
    "initial": {
        "label": "待量尺",
        "color": "#909399",
        "next": ["measured"],
        "phase": "measure",
    },
    "measured": {
        "label": "已量尺",
        "color": "#409eff",
        "next": ["confirmed"],
        "phase": "measure",
    },
    # V3.0 核心流程（已确认→已验收）
    "confirmed": {
        "label": "已确认",
        "color": "#409eff",
        "next": ["split"],
        "phase": "order",
    },
    "split": {
        "label": "已分单",
        "color": "#7c3aed",
        "next": ["purchasing"],
        "phase": "purchase",
    },
    "purchasing": {
        "label": "采购中",
        "color": "#f59e0b",
        "next": ["partial_in", "stocked"],
        "phase": "purchase",
    },
    "partial_in": {
        "label": "部分到货",
        "color": "#f97316",
        "next": ["stocked"],
        "phase": "purchase",
    },
    "stocked": {
        "label": "已入库",
        "color": "#10b981",
        "next": ["processing"],
        "phase": "production",
    },
    "processing": {
        "label": "加工中",
        "color": "#f97316",
        "next": ["completed"],
        "phase": "production",
    },
    "completed": {
        "label": "已完成",
        "color": "#6366f1",
        "next": ["install_scheduled"],
        "phase": "production",
    },
    # 安装流程
    "install_scheduled": {
        "label": "已派工",
        "color": "#8b5cf6",
        "next": ["installed"],
        "phase": "installation",
    },
    "installed": {
        "label": "已安装",
        "color": "#1a3a5c",
        "next": ["accepted"],
        "phase": "installation",
    },
    "accepted": {
        "label": "已验收",
        "color": "#059669",
        "next": [],
        "phase": "done",
    },
    # 异常状态
    "after_sale": {
        "label": "售后中",
        "color": "#ef4444",
        "next": [],
        "phase": "after_sale",
    },
    "cancelled": {
        "label": "已取消",
        "color": "#d9d9d9",
        "next": [],
        "phase": "done",
    },
}

# 线性状态步骤（推进顺序）
STATUS_STEPS: list[str] = [
    "initial",
    "measured",
    "confirmed",
    "split",
    "purchasing",
    "partial_in",
    "stocked",
    "processing",
    "completed",
    "install_scheduled",
    "installed",
    "accepted",
]

# 跳过的异常状态（不参与线性推进）
SKIP_STATUSES: frozenset = frozenset(["partial_in", "after_sale", "cancelled"])

# 终态（不可再推进）
TERMINAL_STATUSES: frozenset = frozenset(["accepted", "cancelled", "after_sale"])

# V3 → V4 状态映射（兼容旧数据）
V3_TO_V4_MAP: dict[str, str] = {
    "created": "initial",
    "confirmed": "confirmed",
    "split": "split",
    "purchasing": "purchasing",
    "stocked": "stocked",
    "processing": "processing",
    "completed": "completed",
    "install_order_generated": "install_scheduled",
    "shipped": "installed",
    "installed": "installed",
    "accepted": "accepted",
    "production_exception": "after_sale",
    "cancelled": "after_sale",
}


def get_status_info(status_key: str) -> dict:
    """获取状态配置信息"""
    return ORDER_STATUS_CONFIG.get(status_key, {})


def get_status_label(status_key: str) -> str:
    """获取状态显示名称"""
    info = get_status_info(status_key)
    return info.get("label", status_key)


def get_status_color(status_key: str) -> str:
    """获取状态颜色"""
    info = get_status_info(status_key)
    return info.get("color", "#909399")


def get_next_status(current_key: str) -> str | None:
    """获取线性推进的下一个状态（跳过异常态）"""
    try:
        idx = STATUS_STEPS.index(current_key)
    except ValueError:
        mapped = V3_TO_V4_MAP.get(current_key)
        if mapped:
            return get_next_status(mapped)
        return None

    for i in range(idx + 1, len(STATUS_STEPS)):
        next_key = STATUS_STEPS[i]
        if next_key not in SKIP_STATUSES:
            return next_key
    return None


def get_all_next_statuses(current_key: str) -> list[str]:
    """获取当前状态所有可跳转的目标"""
    info = get_status_info(current_key)
    if not info:
        mapped = V3_TO_V4_MAP.get(current_key)
        if mapped:
            info = get_status_info(mapped)
    return info.get("next", [])


def can_transition(from_key: str, to_key: str) -> bool:
    """判断状态转换是否合法"""
    if from_key in TERMINAL_STATUSES:
        return False
    next_keys = get_all_next_statuses(from_key)
    if next_keys:
        return to_key in next_keys
    return to_key == get_next_status(from_key)


def is_terminal(status_key: str) -> bool:
    """是否为终态"""
    return status_key in TERMINAL_STATUSES or len(get_all_next_statuses(status_key)) == 0


def normalize_status_key(key: str) -> str:
    """将 V3.0 status_key 转为 V4.0 key"""
    return V3_TO_V4_MAP.get(key, key)


def get_all_status_options() -> list[dict]:
    """获取所有状态选项（用于前端下拉）"""
    return [
        {"key": k, "label": v["label"], "color": v["color"], "phase": v.get("phase", "")}
        for k, v in ORDER_STATUS_CONFIG.items()
    ]
