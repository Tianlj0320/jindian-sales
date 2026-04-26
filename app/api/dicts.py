from fastapi import APIRouter
from sqlalchemy import text
from app.database import async_session

router = APIRouter(prefix="/api/dicts", tags=["码表"])

@router.get("")
async def get_all_dicts():
    """获取所有码表分类和条目"""
    async with async_session() as session:
        result = await session.execute(text(
            "SELECT category_key, item_key, item_value, color, sort, enabled FROM dict_items ORDER BY category_key, sort"
        ))
        rows = result.fetchall()
    
    result_dict = {}
    for r in rows:
        cat, k, v, c, s, e = r
        if cat not in result_dict:
            result_dict[cat] = []
        result_dict[cat].append({"k": k, "v": v, "c": c or "", "s": s or 0, "e": bool(e)})
    return result_dict
