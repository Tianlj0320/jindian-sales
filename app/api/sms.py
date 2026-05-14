# app/api/sms.py
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter
from sqlalchemy import and_, select, text

from app.database import async_session
from app.models import SmsCode
from app.schemas import SmsResponse, SmsResponseData, SmsSendRequest

router = APIRouter(prefix="/api/sms", tags=["短信"])


@router.post("/send", response_model=SmsResponse)
async def send_sms(req: SmsSendRequest) -> SmsResponse:
    """
    发送短信验证码
    Demo模式：固定返回 888888，不真实发短信
    """
    DEMO_CODE = "888888"
    EXPIRES_MINUTES = 5

    async with async_session() as session:
        # 清理过期验证码
        await session.execute(
            text(
                "UPDATE sms_code SET used = 1 WHERE phone = :phone AND used = 0 AND expires_at < :now"
            ),
            {"phone": req.phone, "now": datetime.now()},
        )

        # 检查是否频繁发送（60秒内只能发一次）
        recent_result = await session.execute(
            select(SmsCode)
            .where(
                and_(
                    SmsCode.phone == req.phone,
                    SmsCode.created_at > datetime.now() - timedelta(seconds=60),
                )
            )
            .order_by(SmsCode.created_at.desc())
            .limit(1)
        )
        recent = recent_result.scalar_one_or_none()
        if recent:
            return SmsResponse(success=False, error="发送过于频繁，请稍后再试")

        # 创建新验证码（Demo模式用固定码）
        code_obj = SmsCode(
            phone=req.phone,
            code=DEMO_CODE,
            code_type=req.type,
            expires_at=datetime.now() + timedelta(minutes=EXPIRES_MINUTES),
            used=False,
        )
        session.add(code_obj)
        await session.commit()

        return SmsResponse(
            success=True, data=SmsResponseData(code=DEMO_CODE, expires_in=EXPIRES_MINUTES * 60)
        )
