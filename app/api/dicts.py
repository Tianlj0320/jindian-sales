from fastapi import APIRouter, Body
from sqlalchemy import text

from app.database import async_session
from app.schemas import CommonResponse

router = APIRouter(prefix="/api/dicts", tags=["码表"])


@router.get("")
async def get_all_dicts():
    """获取所有码表分类和条目"""
    async with async_session() as session:
        result = await session.execute(
            text(
                "SELECT category_key, item_key, item_value, color, sort, enabled FROM dict_items ORDER BY category_key, sort"
            )
        )
        rows = result.fetchall()

    result_dict = {}
    for r in rows:
        cat, k, v, c, s, e = r
        if cat not in result_dict:
            result_dict[cat] = []
        result_dict[cat].append({"k": k, "v": v, "c": c or "", "s": s or 0, "e": bool(e)})
    return result_dict


@router.post("/items", response_model=CommonResponse)
async def create_dict_item(req: dict = Body(...)):
    """新增码表条目"""
    async with async_session() as session:
        category_key = req.get("category_key")
        item_key = req.get("item_key")
        item_value = req.get("item_value", "")
        color = req.get("color", "")
        sort = req.get("sort", 0)
        enabled = req.get("enabled", True)

        if not category_key or not item_key:
            return CommonResponse(success=False, error="category_key 和 item_key 不能为空")

        await session.execute(
            text(
                "INSERT INTO dict_items (category_key, item_key, item_value, color, sort, enabled) "
                "VALUES (:category_key, :item_key, :item_value, :color, :sort, :enabled)"
            ),
            {
                "category_key": category_key,
                "item_key": item_key,
                "item_value": item_value,
                "color": color,
                "sort": sort,
                "enabled": 1 if enabled else 0,
            },
        )
        await session.commit()
        return CommonResponse(success=True, data={"category_key": category_key, "item_key": item_key})


@router.put("/items", response_model=CommonResponse)
async def update_dict_item(req: dict = Body(...)):
    """更新码表条目（按 category_key + item_key 定位）"""
    async with async_session() as session:
        category_key = req.get("category_key")
        item_key = req.get("item_key")
        item_value = req.get("item_value")
        color = req.get("color")
        sort = req.get("sort")
        enabled = req.get("enabled")

        if not category_key or not item_key:
            return CommonResponse(success=False, error="category_key 和 item_key 不能为空")

        updates = []
        params = {"category_key": category_key, "item_key": item_key}
        if item_value is not None:
            updates.append("item_value = :item_value")
            params["item_value"] = item_value
        if color is not None:
            updates.append("color = :color")
            params["color"] = color
        if sort is not None:
            updates.append("sort = :sort")
            params["sort"] = sort
        if enabled is not None:
            updates.append("enabled = :enabled")
            params["enabled"] = 1 if enabled else 0

        if not updates:
            return CommonResponse(success=False, error="没有需要更新的字段")

        sql = f"UPDATE dict_items SET {', '.join(updates)} WHERE category_key = :category_key AND item_key = :item_key"
        await session.execute(text(sql), params)
        await session.commit()
        return CommonResponse(success=True, data={"category_key": category_key, "item_key": item_key})


@router.delete("/items", response_model=CommonResponse)
async def delete_dict_item(category_key: str = Body(...), item_key: str = Body(...)):
    """删除码表条目"""
    async with async_session() as session:
        await session.execute(
            text(
                "DELETE FROM dict_items WHERE category_key = :category_key AND item_key = :item_key"
            ),
            {"category_key": category_key, "item_key": item_key},
        )
        await session.commit()
        return CommonResponse(success=True, data={"category_key": category_key, "item_key": item_key})
