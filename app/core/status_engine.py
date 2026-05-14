"""
V4.0 订单状态引擎（JSON 驱动配置化）
app/core/status_engine.py
"""

# ─── 订单状态配置 ────────────────────────────────────────────────────────────
ORDER_STATUS_CONFIG = {
    "initial": {
        "label": "待量尺",
        "color": "#909399",
        "next": ["measured"],
    },
    "measured": {
        "label": "已量尺",
        "color": "#409eff",
        "next": ["confirmed"],
    },
    "confirmed": {
        "label": "已确认",
        "color": "#409eff",
        "next": ["split"],
    },
    "split": {
        "label": "已分单",
        "color": "#7c3aed",
        "next": ["purchasing"],
    },
    "purchasing": {
        "label": "采购中",
        "color": "#f59e0b",
        "next": ["partial_in", "stocked"],
    },
    "partial_in": {
        "label": "部分到货",
        "color": "#f97316",
        "next": ["stocked"],
    },
    "stocked": {
        "label": "已入库",
        "color": "#10b981",
        "next": ["processing"],
    },
    "processing": {
        "label": "加工中",
        "color": "#f97316",
        "next": ["completed"],
    },
    "completed": {
        "label": "待安装",
        "color": "#6366f1",
        "next": ["install_scheduled"],
    },
    "install_scheduled": {
        "label": "已派工",
        "color": "#8b5cf6",
        "next": ["installed"],
    },
    "installed": {
        "label": "已安装",
        "color": "#1a3a5c",
        "next": ["accepted"],
    },
    "accepted": {
        "label": "已验收",
        "color": "#059669",
        "next": [],
    },
    "after_sale": {
        "label": "售后中",
        "color": "#ef4444",
        "next": [],
    },
    # ── 兼容 V3.0 状态 key ──────────────────────────────────────────────────
    "created": {
        "label": "待确认",
        "color": "#909399",
        "next": ["confirmed"],
    },
}

# V3.0 → V4.0 状态 key 映射（兼容旧数据）
V3_TO_V4_STATUS_MAP = {
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

# 线性状态步骤（用于状态推进）
STATUS_STEPS_V4 = [
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

# 异常状态（不参与线性推进）
SKIP_STATUSES = frozenset(["partial_in", "after_sale"])


def get_status_info(status_key: str) -> dict:
    """获取状态配置信息"""
    return ORDER_STATUS_CONFIG.get(status_key, {})


def get_next_status(current_key: str) -> str | None:
    """获取下一个状态（线性推进，跳过异常态）"""
    try:
        idx = STATUS_STEPS_V4.index(current_key)
    except ValueError:
        # 兼容 V3.0 key
        mapped = V3_TO_V4_STATUS_MAP.get(current_key)
        if mapped:
            try:
                idx = STATUS_STEPS_V4.index(mapped)
            except ValueError:
                return None
        else:
            return None

    for i in range(idx + 1, len(STATUS_STEPS_V4)):
        next_key = STATUS_STEPS_V4[i]
        if next_key not in SKIP_STATUSES:
            return next_key
    return None


def get_all_next_statuses(current_key: str) -> list[str]:
    """获取当前状态所有可跳转的目标状态"""
    info = get_status_info(current_key)
    # 兼容 V3.0 key
    if not info and current_key in V3_TO_V4_STATUS_MAP:
        info = get_status_info(V3_TO_V4_STATUS_MAP[current_key])
    return info.get("next", [])


def can_transition(from_key: str, to_key: str) -> bool:
    """判断状态转换是否合法"""
    next_keys = get_all_next_statuses(from_key)
    if next_keys:
        return to_key in next_keys
    # 如果没有配置 next，则只允许线性推进
    return to_key == get_next_status(from_key)


def is_terminal(status_key: str) -> bool:
    """判断是否为终态（不可再推进）"""
    return len(get_all_next_statuses(status_key)) == 0


def normalize_status_key(key: str) -> str:
    """将 V3.0 status_key 转换为 V4.0 key"""
    return V3_TO_V4_STATUS_MAP.get(key, key)