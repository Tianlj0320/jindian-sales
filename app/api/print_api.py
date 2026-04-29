"""打印模板 API - V2.2"""

from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.database import async_session
from app.models import Order

router = APIRouter(prefix="/api/print", tags=["打印管理"])


def make_rows(items, cols):
    rows = []
    for i, p in enumerate(items, 1):
        cells = [str(i)]
        for col in cols:
            cells.append(str(p.get(col, "")))
        rows.append("<tr>" + "".join("<td>" + c + "</td>" for c in cells) + "</tr>")
    return "".join(rows)


def fmt(v):
    return f"¥{float(v or 0):,.2f}"


def html_escape(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_contract(d):
    rows = make_rows(d["products"], ["name", "qty", "unit", "price", "subtotal"])
    body = (
        '<div class="print-page">'
        '<div class="header"><div class="company-name">金 典 软 装</div><div class="doc-title">订 货 合 同</div></div>'
        '<div class="order-meta">'
        '<div class="meta-row">'
        '<div class="meta-item"><span class="meta-label">订单编号：</span>'
        + html_escape(d["order_no"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">订单日期：</span>'
        + html_escape(d["order_date"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">交货日期：</span>'
        + html_escape(d["delivery_date"])
        + "</div>"
        "</div></div>"
        '<div class="info-grid">'
        '<div class="info-col"><span class="meta-label">客户姓名：</span>'
        + html_escape(d["customer_name"])
        + "</div>"
        '<div class="info-col"><span class="meta-label">联系电话：</span>'
        + html_escape(d["customer_phone"])
        + "</div>"
        '<div class="info-col"><span class="meta-label">安装地址：</span>'
        + html_escape(d["install_address"])
        + "</div>"
        '<div class="info-col"><span class="meta-label">导购：</span>'
        + html_escape(d["salesperson_name"])
        + "</div>"
        '<div class="info-col"><span class="meta-label">提货方式：</span>'
        + html_escape(d["delivery_method"])
        + "</div>"
        "</div>"
        '<div class="section"><div class="section-title">订 货 明 细</div>'
        '<table><thead><tr><th width="40">#</th><th>产品名称</th><th width="50">数量</th><th width="50">单位</th><th width="90">单价</th><th width="100">小计</th></tr></thead><tbody>'
        + rows
        + "</tbody></table>"
        '<div class="amounts">'
        '<div class="row"><span>标价合计：</span><span>' + d["quote_amount"] + "</span></div>"
        '<div class="row"><span>优惠金额：</span><span>-' + d["discount_amount"] + "</span></div>"
        '<div class="row"><span>抹零金额：</span><span>-' + d["round_amount"] + "</span></div>"
        '<div class="row total"><span>合同总金额：</span><span>' + d["amount"] + "</span></div>"
        '<div class="row"><span>已收定金：</span><span>' + d["received"] + "</span></div>"
        '<div class="row"><span>尚欠金额：</span><span style="color:#c00">'
        + d["debt"]
        + "</span></div>"
        "</div></div>"
        '<div class="contract-note"><b>特别约定：</b>窗帘为定制产品，按实际测量尺寸生产。非质量问题概不退换。安装完毕后请当场验收，如有异议请现场提出。定金到账后订单正式生效。</div>'
        '<div class="signatures">'
        '<div class="sign-item">客户签名：<div class="sign-line"></div><br>日期：___________</div>'
        '<div class="sign-item">导购签名：<div class="sign-line"></div><br>日期：___________</div>'
        '<div class="sign-item">门店确认：<div class="sign-line"></div><br>日期：___________</div>'
        "</div></div>"
    )
    return _HTML_CONTRACT + body + _HTML_FOOTER.format(t=d["now"])


def render_measurement(d):
    rows = make_rows(d["products"], ["name", "location", "width", "height", "qty", "memo"])
    body = (
        '<div class="print-page">'
        '<div class="header"><div class="company-name">金 典 软 装</div><div class="doc-title">测 量 记 录 单</div></div>'
        '<div class="order-meta">'
        '<div class="meta-row">'
        '<div class="meta-item"><span class="meta-label">订单编号：</span>'
        + html_escape(d["order_no"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">客户姓名：</span>'
        + html_escape(d["customer_name"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">电话：</span>'
        + html_escape(d["customer_phone"])
        + "</div>"
        "</div>"
        '<div class="meta-row">'
        '<div class="meta-item" style="flex:2"><span class="meta-label">安装地址：</span>'
        + html_escape(d["install_address"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">导购：</span>'
        + html_escape(d["salesperson_name"])
        + "</div>"
        "</div></div>"
        '<div class="section"><div class="section-title">测 量 明 细</div>'
        '<table><thead><tr><th width="40">#</th><th>产品</th><th>安装位置</th><th>宽度(M)</th><th>高度(M)</th><th width="40">数量</th><th>备注</th></tr></thead><tbody>'
        + rows
        + "</tbody></table></div>"
        '<div class="section"><div class="section-title">备 注</div><div style="border:1px solid #ddd;min-height:60px;padding:8px;border-radius:4px">'
        + html_escape(d.get("content", ""))
        + "</div></div>"
        '<div class="signatures">'
        '<div class="sign-item">测量员签名：<div class="sign-line"></div><br>日期：___________</div>'
        '<div class="sign-item">客户确认：<div class="sign-line"></div><br>日期：___________</div>'
        "</div></div>"
    )
    return _HTML_CONTRACT + body + _HTML_FOOTER.format(t=d["now"])


def render_processing(d):
    rows = make_rows(d["products"], ["name", "qty", "size", "process", "memo"])
    body = (
        '<div class="print-page">'
        '<div class="header"><div class="company-name">金 典 软 装</div><div class="doc-title">加 工 单</div></div>'
        '<div class="order-meta">'
        '<div class="meta-row">'
        '<div class="meta-item"><span class="meta-label">订单编号：</span>'
        + html_escape(d["order_no"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">订单日期：</span>'
        + html_escape(d["order_date"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">交货日期：</span>'
        + html_escape(d["delivery_date"])
        + "</div>"
        "</div>"
        '<div class="meta-row">'
        '<div class="meta-item"><span class="meta-label">客户姓名：</span>'
        + html_escape(d["customer_name"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">安装地址：</span>'
        + html_escape(d["install_address"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">提货方式：</span>'
        + html_escape(d["delivery_method"])
        + "</div>"
        "</div></div>"
        '<div class="section"><div class="section-title">加 工 明 细</div>'
        '<table><thead><tr><th width="40">#</th><th>产品名称</th><th width="50">数量</th><th>尺寸规格</th><th>工艺要求</th><th>备注</th></tr></thead><tbody>'
        + rows
        + "</tbody></table></div>"
        '<div class="signatures">'
        '<div class="sign-item">生产负责人：<div class="sign-line"></div></div>'
        '<div class="sign-item">审核：<div class="sign-line"></div></div>'
        '<div class="sign-item">日期：<div class="sign-line"></div></div>'
        "</div></div>"
    )
    return _HTML_CONTRACT + body + _HTML_FOOTER.format(t=d["now"])


def render_install(d):
    rows = make_rows(d["products"], ["name", "qty", "memo"])
    body = (
        '<div class="print-page">'
        '<div class="header"><div class="company-name">金 典 软 装</div><div class="doc-title">安 装 派 工 单</div></div>'
        '<div class="order-meta">'
        '<div class="meta-row">'
        '<div class="meta-item"><span class="meta-label">订单编号：</span>'
        + html_escape(d["order_no"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">预约安装日期：</span>'
        + html_escape(d.get("install_date", ""))
        + "</div>"
        '<div class="meta-item"><span class="meta-label">客户电话：</span>'
        + html_escape(d["customer_phone"])
        + "</div>"
        "</div>"
        '<div class="meta-row">'
        '<div class="meta-item" style="flex:2"><span class="meta-label">安装地址：</span>'
        + html_escape(d["install_address"])
        + "</div>"
        '<div class="meta-item"><span class="meta-label">导购：</span>'
        + html_escape(d["salesperson_name"])
        + "</div>"
        "</div></div>"
        '<div class="section"><div class="section-title">安 装 项 目</div>'
        '<table><thead><tr><th width="40">#</th><th>产品名称</th><th width="50">数量</th><th>安装说明</th></tr></thead><tbody>'
        + rows
        + "</tbody></table></div>"
        '<div class="section"><div class="section-title">客 户 确 认</div>'
        '<div class="signatures" style="margin-top:20px">'
        '<div class="sign-item">安装人员：<div class="sign-line"></div><br>员工编号：___________</div>'
        '<div class="sign-item">客户签名：<div class="sign-line"></div><br>验收日期：___________</div>'
        "</div>"
        '<div style="margin-top:16px;font-size:12px;color:#888">备注：安装完成后请客户确认签字，如有问题请现场拨打客服电话。</div>'
        "</div></div>"
    )
    return _HTML_CONTRACT + body + _HTML_FOOTER.format(t=d["now"])


_HTML_CONTRACT = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>金典软装</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:"宋体","Microsoft YaHei",sans-serif;font-size:14px;color:#333;background:#fff}
  .print-page{max-width:800px;margin:0 auto;padding:30px 40px}
  .header{text-align:center;border-bottom:2px solid #1a3a5c;padding-bottom:16px;margin-bottom:24px}
  .company-name{font-size:22px;font-weight:bold;color:#1a3a5c;letter-spacing:2px}
  .doc-title{font-size:16px;color:#666;margin-top:6px}
  .order-meta{margin-bottom:20px;font-size:13px}
  .meta-row{display:flex;flex-wrap:wrap;border-bottom:1px solid #eee;padding:4px 0}
  .meta-item{flex:1;min-width:200px}
  .meta-label{color:#888}
  .info-grid{display:flex;flex-wrap:wrap;margin-bottom:20px}
  .info-col{flex:1;min-width:200px;padding:6px 0}
  .section{margin-bottom:20px}
  .section-title{font-size:14px;font-weight:bold;color:#1a3a5c;border-left:3px solid #1a3a5c;padding-left:8px;margin-bottom:10px}
  table{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed}
  th{background:#f5f7fa;color:#1a3a5c;padding:8px 6px;text-align:left;border-bottom:2px solid #1a3a5c}
  td{padding:7px 6px;border-bottom:1px solid #eee}
  .amounts{text-align:right;padding:10px 0;border-top:2px solid #1a3a5c;margin-top:10px}
  .amounts .row{display:flex;justify-content:flex-end;gap:20px;padding:4px 0}
  .amounts .row.total{font-size:16px;font-weight:bold;color:#1a3a5c;border-top:1px solid #333;padding-top:8px;margin-top:4px}
  .signatures{display:flex;justify-content:space-between;margin-top:40px;padding-top:20px;border-top:1px solid #eee}
  .sign-item{text-align:center;flex:1}
  .sign-line{height:40px;border-bottom:1px solid #333;margin-top:30px;min-width:120px;display:inline-block}
  .footer{margin-top:30px;text-align:center;font-size:11px;color:#aaa}
  .contract-note{background:#f5f7fa;padding:10px 14px;border-radius:4px;font-size:12px;color:#666;margin-top:16px;border:1px solid #e8e8e8}
  @media print { body { padding: 0 } }
</style>
</head>
<body>
"""

_HTML_FOOTER = """
<div class="footer">本文件由金典软装系统生成 · 打印时间：{t} · 电话：13362527898</div>
</body></html>
"""

TEMPLATES = {
    "contract": render_contract,
    "processing": render_processing,
    "install": render_install,
    "measurement": render_measurement,
}


@router.get("/{template}/{order_id}")
async def print_template(template: str, order_id: int, authorization: str = Header(None)):
    if template not in TEMPLATES:
        raise HTTPException(
            status_code=400, detail="未知模板，可选：contract/processing/install/measurement"
        )
    async with async_session() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        items = order.items or []
        products = [i for i in items if i.get("productId")]

        d = {
            "order_no": order.order_no or "",
            "order_date": order.order_date or "",
            "delivery_date": order.delivery_date or "",
            "customer_name": order.customer_name or "",
            "customer_phone": order.customer_phone or "",
            "install_address": order.install_address or "",
            "salesperson_name": order.salesperson or "",
            "order_type": order.order_type or "窗帘",
            "content": order.content or "",
            "quote_amount": fmt(order.quote_amount),
            "discount_amount": fmt(order.discount_amount),
            "round_amount": fmt(order.round_amount),
            "amount": fmt(order.amount),
            "received": fmt(order.received),
            "debt": fmt(order.debt),
            "delivery_method": order.delivery_method or "上门安装",
            "install_date": str(order.install_date) if order.install_date else "",
            "products": products,
            "now": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        return HTMLResponse(content=TEMPLATES[template](d))
