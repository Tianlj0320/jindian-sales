/**
 * 打印工具 - 生成打印内容并打开打印窗口
 *
 * 订货合同格式参照 D:\project\订货单.xls 模板设计：
 * - 表头：金典软装设计中心客户订货合同 + 客户信息三列横排
 * - 主料明细表（14列）：成品类型 | 安装位置 | 项目 | 货号 | 尺寸 | 数量 | 单价 | 折扣 | 金额 | 幅数 | 定向 | 幅宽 | 款式 | 工艺
 * - 辅料明细表（5列）：货号 | 数量 | 单价 | 金额 | 备注
 * - 底部：合计金额（大写）+ 定金/余款 + 6条声明 + 店铺地址电话 + 签名区
 *
 * 所有单据统一 A4 纵向，紧凑排版以尽量容纳于一页内。
 * 提供 generateXxxHtml / printXxx 双模式：generate 返回 HTML 字符串供预览，
 * print 调用 generate 后直接打开打印窗口。
 */

// ─── 工具函数 ────────────────────────────────────────────────

/** 金额数字转中文大写（如 96508.46 → 玖万陆仟伍佰零捌圆肆角陆分） */
function numToChinese(num) {
  if (num === 0 || num === null || num === undefined) return '零圆整'
  const digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
  const radices = ['', '拾', '佰', '仟']
  const bigRadices = ['', '万', '亿', '万亿']

  const parts = String(Math.round(num * 100)).padStart(3, '0')
  const intPart = parts.slice(0, -2).replace(/^0+/, '') || '0'
  const decPart = parts.slice(-2)

  let result = ''
  const len = intPart.length
  let zeroCount = 0

  for (let i = 0; i < len; i++) {
    const p = len - 1 - i
    const d = parseInt(intPart[i])
    const segment = Math.floor(p / 4)
    const pos = p % 4

    if (d === 0) {
      zeroCount++
    } else {
      if (zeroCount > 0) {
        result += '零'
      }
      zeroCount = 0
      result += digits[d] + radices[pos]
    }

    if (pos === 0 && zeroCount < 4) {
      result += bigRadices[segment]
      zeroCount = 0
    }
  }

  result += '圆'

  const jiao = parseInt(decPart[0])
  const fen = parseInt(decPart[1])

  if (jiao === 0 && fen === 0) {
    result += '整'
  } else {
    if (jiao > 0) result += digits[jiao] + '角'
    if (fen > 0) result += digits[fen] + '分'
  }

  return result
}

/** 换行符转<br>，用于多行文本 */
function nl2br(text) {
  return (text || '').replace(/\n/g, '<br>').replace(/\r/g, '')
}

// 种子数据中的店铺信息占位描述（未配置时跳过）
const SEED_PLACEHOLDERS = new Set([
  '店铺名称', '店铺编号', '联系电话', '店铺地址',
  '订单抬头', '订单模板', '订单提示/声明',
  '合同抬头', '合同提示/声明',
])

/** 从 storeInfo 中获取已配置的字段值（跳过种子占位符） */
function storeValue(si, key, fallback = '') {
  const v = si[key]?.label || ''
  if (!v || SEED_PLACEHOLDERS.has(v)) return fallback
  return v
}


// ─── 打印模板 ────────────────────────────────────────────────

/**
 * 基础 HTML 模板 — A4 纵向，紧凑基线。
 * 各单据通过 extraStyle 传入自身专有样式覆盖。
 */
function printTemplate(title, contentHtml, extraStyle = '') {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>${title}</title>
<style>
  @page { margin: 8mm 12mm; size: A4 portrait; }
  body { font-family: "SimSun", "宋体", "Microsoft YaHei", serif; font-size: 11px; color: #000; margin: 0; padding: 0; line-height: 1.3; }
  table { width: 100%; border-collapse: collapse; font-size: 9.5px; }
  table.thin td, table.thin th { border: 1px solid #000; padding: 2px 4px; text-align: center; vertical-align: middle; }
  table.thin th { background: #f0f0f0; font-weight: bold; }
  .no-print { display: none; }
  @media print {
    .no-print { display: none; }
    button { display: none; }
  }
  ${extraStyle}
</style>
</head>
<body>
  ${contentHtml}
</body>
</html>`
}


// ─── 订货合同 ────────────────────────────────────────────────

/**
 * 生成订货合同 HTML（供预览或直接打印）
 * @param {Object} order - 订单数据（含 items[]）
 * @param {Object} storeInfo - 店铺信息（可选）
 * @returns {string} 完整 HTML
 */
export function generateContractHtml(order, storeInfo) {
  const si = storeInfo || {}

  const contractTitle = storeValue(si, 'contract_header', '金典软装设计中心客户订货合同')

  // ── 客户信息 ──
  const customerHtml = `
    <table style="margin-bottom:1px;border-collapse:collapse;font-size:11px">
      <tr>
        <td style="width:33%;padding:2px 4px"><b>客户名称：</b>${order.customer_name || ''}</td>
        <td style="width:33%;padding:2px 4px"><b>订货日期：</b>${order.order_date || ''}</td>
        <td style="width:34%;padding:2px 4px"><b>定 单 号：</b>${order.order_no || ''}</td>
      </tr>
      <tr>
        <td style="padding:2px 4px"><b>客户地址：</b>${order.install_address || order.customer_address || ''}</td>
        <td style="padding:2px 4px"><b>交货日期：</b>${order.delivery_date || ''}</td>
        <td style="padding:2px 4px"><b>交货方式：</b>${order.delivery_method || ''}</td>
      </tr>
    </table>
  `

  const mainItems = (order.items || []).filter(i => i.material_type !== '辅料')
  const auxItems = (order.items || []).filter(i => i.material_type === '辅料')

  // 主料表头
  const mainHeaderRows = `
    <tr>
      <th style="width:8%">成品类型</th>
      <th style="width:9%">安装位置</th>
      <th style="width:11%">项目</th>
      <th style="width:8%">货号</th>
      <th style="width:9%">尺寸</th>
      <th style="width:5%">数量</th>
      <th style="width:8%">单价</th>
      <th style="width:5%">折扣</th>
      <th style="width:9%">金额</th>
      <th style="width:5%">幅数</th>
      <th style="width:5%">定向</th>
      <th style="width:5%">幅宽</th>
      <th style="width:5%">款式</th>
      <th style="width:9%">工艺</th>
    </tr>
  `

  function renderSize(item) {
    const w = item.width || 0
    const h = item.height || 0
    const fr = item.fold_ratio || 1
    if (item.calc_type === 'per_meter' && fr > 1 && w > 0) {
      const fabricQty = Math.round(w * fr * 100) / 100
      return `${w}×${fabricQty}`
    }
    if (w > 0 && h > 0) return w + (item.classification === '定制' ? '*' : '×') + h
    if (w > 0) return String(w)
    return ''
  }

  function renderFoldRatio(item) {
    if (item.calc_type === 'per_meter' && (item.fold_ratio || 0) > 1) {
      return item.fold_ratio.toFixed(1)
    }
    return ''
  }

  function renderDiscount(item) {
    const d = item.discount
    if (d === null || d === undefined || d === 1 || d >= 1) return ''
    return (d * 10).toFixed(1)
  }

  function renderQty(item) {
    const q = item.qty
    if (!q) return ''
    if (Number.isInteger(q)) return String(q)
    return q.toFixed(2)
  }

  const mainRows = mainItems.map(item => {
    const size = renderSize(item)
    const qty = item.calc_type === 'fixed' ? String(item.qty || '') : (item.calc_type === 'per_meter' && item.width && item.fold_ratio > 1 ? '' : renderQty(item))
    return `
    <tr>
      <td>${item.item_type || ''}</td>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.product_code || ''}</td>
      <td>${size}</td>
      <td>${qty}</td>
      <td style="text-align:right">${item.unit_price ? '¥' + Number(item.unit_price).toFixed(2) : ''}</td>
      <td>${renderDiscount(item)}</td>
      <td style="text-align:right">${item.final_amount ? '¥' + Number(item.final_amount).toFixed(2) : ''}</td>
      <td>${item.open_type || ''}</td>
      <td>${item.classification || ''}</td>
      <td>${renderFoldRatio(item)}</td>
      <td>${item.style_code || ''}</td>
      <td style="text-align:left;font-size:8.5px">${item.process_desc || item.note || ''}</td>
    </tr>`
  }).join('')

  // 辅料表头（5列）
  const auxHeader = `
    <tr>
      <th style="width:20%">货号</th>
      <th style="width:15%">数量</th>
      <th style="width:15%">单价</th>
      <th style="width:15%">金额</th>
      <th style="width:35%">备注</th>
    </tr>
  `

  const auxRows = auxItems.map(item => `
    <tr>
      <td>${item.product_code || ''}</td>
      <td>${renderQty(item)} ${item.unit || ''}</td>
      <td style="text-align:right">${item.unit_price ? '¥' + Number(item.unit_price).toFixed(2) : ''}</td>
      <td style="text-align:right">${item.final_amount ? '¥' + Number(item.final_amount).toFixed(2) : ''}</td>
      <td style="text-align:left;font-size:8.5px">${item.room ? item.room : ''}${item.room && item.note ? ' ' : ''}${item.note || ''}</td>
    </tr>
  `).join('')

  // ── 金额汇总 ──
  const totalAmount = order.amount || 0
  const received = order.received || 0
  const debt = order.debt || 0
  const chineseAmount = numToChinese(totalAmount)

  // ── 声明条款 ──
  const contractTips = storeValue(si, 'contract_tips')
  let declarationsHtml = ''
  if (contractTips) {
    const lines = contractTips.split('\n').filter(l => l.trim())
    declarationsHtml = lines.map((line, i) => `${i + 1}、${line.trim()}`).join('<br>')
  } else {
    declarationsHtml = `
      1、客户购买后，若对订单各项内容有不明之处，欢迎随时查询。<br>
      2、客户订货时须付60%定金，制作完成，在安装前必须在本店付清余款方可上门安装。<br>
      3、订货后，不办理退款手续，客户若特殊原因需更改，必须在面料、配件裁剪前，否则相应的经济损失由客户承担。<br>
      4、本订单经双方签字或盖章后生效。<br>
      5、客户有权监督本店派出员工的工作表现，并提出宝贵建议。<br>
      6、制作费、轨道及柔纱帘不打折。
    `.replace(/\n\s+/g, '\n')
  }

  const address = storeValue(si, 'address')
  const phone = storeValue(si, 'phone')
  const fax = storeValue(si, 'fax')
  const bottomLine = `地址：${address}${phone ? '  电话：' + phone : ''}${fax ? '  传真：' + fax : ''}`

  return printTemplate('订货合同', `
    <div style="text-align:center;margin-bottom:6px">
      <h1 style="font-size:16px;margin:0;letter-spacing:3px;font-weight:bold">${contractTitle}</h1>
      <div style="font-size:10px;color:#666;margin-top:1px">${order.order_no || ''}</div>
    </div>

    ${customerHtml}

    <h4 style="font-size:11px;margin:4px 0 2px 0;background:#eee;padding:2px 6px">面料明细</h4>
    <table class="thin">
      <thead>${mainHeaderRows}</thead>
      <tbody>${mainRows || '<tr><td colspan="14" style="text-align:center;color:#999">（无）</td></tr>'}</tbody>
    </table>

    ${auxItems.length ? `
    <h4 style="font-size:11px;margin:4px 0 2px 0;background:#eee;padding:2px 6px">辅料明细</h4>
    <table class="thin">
      <thead>${auxHeader}</thead>
      <tbody>${auxRows}</tbody>
    </table>
    ` : ''}

    <div style="margin-top:6px;border-top:1.5px solid #000">
      <table style="margin-top:2px;font-size:11px;border-collapse:collapse">
        <tr>
          <td style="width:33%;padding:1px 4px"><b>合计金额：</b>¥${totalAmount.toFixed(2)}</td>
          <td style="width:33%;padding:1px 4px"><b>应收金额：</b>¥${totalAmount.toFixed(2)}</td>
          <td style="padding:1px 4px"><b>大写：</b>${chineseAmount}</td>
        </tr>
        <tr>
          <td style="padding:1px 4px"><b>定金：</b>¥${received.toFixed(2)}</td>
          <td style="padding:1px 4px" colspan="2"><b>余款：</b>¥${debt.toFixed(2)}</td>
        </tr>
      </table>
    </div>

    <div style="margin-top:4px;font-size:9.5px;line-height:1.5;border-top:1px solid #000;padding-top:2px">
      <b>声明销售约定：</b><br>
      ${declarationsHtml}
    </div>

    <div style="margin-top:4px;font-size:10px;border-top:1px solid #000;padding-top:2px">
      ${bottomLine}
    </div>

    <div style="display:flex;justify-content:space-between;margin-top:14px;font-size:10px">
      <div style="text-align:left">
        <span style="margin-right:10px"><b>业务员：</b>${order.salesperson_name || '________'}</span>
        <span><b>制单人：</b>${order.salesperson_name || '________'}</span>
      </div>
      <div style="text-align:right">
        <b>客户签字：</b><span style="display:inline-block;width:80px;border-bottom:1px solid #000">&nbsp;</span>
      </div>
    </div>

    <div style="text-align:right;font-size:8.5px;color:#999;margin-top:4px">
      打印日期：${new Date().toLocaleDateString('zh-CN')}
    </div>
  `, `
    body { font-size: 11px; line-height: 1.3; }
    table.thin td, table.thin th { padding: 2px 3px; }
    table.thin td { font-size: 9px; }
  `)
}

export function printContract(order, storeInfo) {
  openPrintWindow(generateContractHtml(order, storeInfo))
}


// ─── 测量记录单 ───────────────────────────────────────────────

export function generateMeasurementHtml(order) {
  const itemsHtml = (order.items || []).map((item, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.width || 0}</td>
      <td>${item.height || 0}</td>
      <td>${Math.round((item.width || 0) * (item.fold_ratio || 2.0) * 100) / 100}</td>
      <td></td>
      <td></td>
    </tr>
  `).join('')

  return printTemplate('测量记录单', `
    <div class="print-header">
      <h1>金典软装 · 测量记录单</h1>
      <div class="print-no">订单编号：${order.order_no || ''} &nbsp;&nbsp; 测量日期：________</div>
    </div>

    <div class="print-section">
      <h3>客户信息</h3>
      <div class="info-row"><span class="info-label">客户姓名：</span><span class="info-value">${order.customer_name || ''}</span></div>
      <div class="info-row"><span class="info-label">联系电话：</span><span class="info-value">${order.customer_phone || ''}</span></div>
      <div class="info-row"><span class="info-label">安装地址：</span><span class="info-value">${order.install_address || ''}</span></div>
      <div class="info-row"><span class="info-label">测量人员：</span><span class="info-value">________</span></div>
    </div>

    <div class="print-section">
      <h3>测量数据</h3>
      <table>
        <thead>
          <tr><th>序号</th><th>空间</th><th>产品</th><th>宽度(m)</th><th>高度(m)</th><th>面料用量(m)</th><th>实际测量</th><th>备注</th></tr>
        </thead>
        <tbody>${itemsHtml}</tbody>
      </table>
    </div>

    <div style="margin-top:8px">
      <div class="info-row"><span class="info-label">现场情况：</span><span class="info-value">________________________</span></div>
      <div class="info-row"><span class="info-label">特殊要求：</span><span class="info-value">________________________</span></div>
    </div>

    <div class="signature-area">
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>测量人员签字</div>
      </div>
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>客户确认</div>
      </div>
    </div>
  `, `
    .print-header { text-align:center; margin-bottom:6px; }
    .print-header h1 { font-size:15px; margin:0 0 2px 0; letter-spacing:2px; }
    .print-header .print-no { color:#999; font-size:10px; }
    .print-section { margin-bottom:5px; }
    .print-section h3 { font-size:11px; border-bottom:1.5px solid #333; padding-bottom:2px; margin-bottom:3px; }
    table th, table td { border:1px solid #333; padding:2px 4px; text-align:left; font-size:9px; }
    table th { background:#f0f0f0; font-weight:bold; }
    .info-row { display:flex; margin-bottom:2px; font-size:10px; }
    .info-label { width:65px; color:#666; flex-shrink:0; }
    .info-value { flex:1; }
    .signature-area { display:flex; justify-content:space-between; margin-top:10px; }
    .signature-item { text-align:center; font-size:10px; }
    .signature-line { width:110px; border-bottom:1px solid #333; margin-top:10px; margin-bottom:2px; }
  `)
}

export function printMeasurement(order) {
  openPrintWindow(generateMeasurementHtml(order))
}


// ─── 加工单 ──────────────────────────────────────────────────

export function generateProcessingHtml(order) {
  const itemsHtml = (order.items || []).map(item => `
    <tr>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.width || 0}</td>
      <td>${item.height || 0}</td>
      <td>${item.fold_ratio || 2.0}</td>
      <td>${item.qty || 0}</td>
      <td>${item.unit || '米'}</td>
      <td>${item.open_type || '-'}</td>
      <td>${item.process_desc || '-'}</td>
      <td>${item.note || '-'}</td>
    </tr>
  `).join('')

  return printTemplate('加工单', `
    <div style="text-align:center;margin-bottom:6px">
      <h1 style="font-size:15px;margin:0;letter-spacing:2px">金典软装 · 加工单</h1>
      <div style="color:#999;font-size:10px;margin-top:1px">订单编号：${order.order_no || ''}</div>
    </div>

    <div style="margin-bottom:5px">
      <h3 style="font-size:11px;border-bottom:1.5px solid #333;padding-bottom:2px;margin-bottom:3px">订单信息</h3>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:80px;color:#666;flex-shrink:0">客户：</span><span>${order.customer_name || ''} &nbsp; ${order.customer_phone || ''}</span></div>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:80px;color:#666;flex-shrink:0">交货日期：</span><span>${order.delivery_date || '-'}</span></div>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:80px;color:#666;flex-shrink:0">交货方式：</span><span>${order.delivery_method || ''}</span></div>
    </div>

    <div style="margin-bottom:5px">
      <h3 style="font-size:11px;border-bottom:1.5px solid #333;padding-bottom:2px;margin-bottom:3px">加工明细</h3>
      <table style="width:100%;border-collapse:collapse;margin-bottom:8px">
        <thead>
          <tr><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">空间</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">产品</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">宽(m)</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">高(m)</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">倍率</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">数量</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">单位</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">开合</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">工艺</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">备注</th></tr>
        </thead>
        <tbody>${itemsHtml}</tbody>
      </table>
    </div>

    <div style="display:flex;justify-content:space-between;margin-top:10px">
      <div style="text-align:center;font-size:10px"><div style="width:110px;border-bottom:1px solid #333;margin-top:10px;margin-bottom:2px"></div><div>加工人</div></div>
      <div style="text-align:center;font-size:10px"><div style="width:110px;border-bottom:1px solid #333;margin-top:10px;margin-bottom:2px"></div><div>验收人</div></div>
      <div style="text-align:center;font-size:10px"><div style="width:110px;border-bottom:1px solid #333;margin-top:10px;margin-bottom:2px"></div><div>日期</div></div>
    </div>
  `)
}

export function printProcessing(order) {
  openPrintWindow(generateProcessingHtml(order))
}


// ─── 安装派工单 ──────────────────────────────────────────────

export function generateInstallationHtml(order) {
  const itemsHtml = (order.items || []).map(item => `
    <tr>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.qty || 0}</td>
      <td>${item.unit || '米'}</td>
      <td>${item.note || '-'}</td>
    </tr>
  `).join('')

  return printTemplate('安装派工单', `
    <div style="text-align:center;margin-bottom:6px">
      <h1 style="font-size:15px;margin:0;letter-spacing:2px">金典软装 · 安装派工单</h1>
      <div style="color:#999;font-size:10px;margin-top:1px">订单编号：${order.order_no || ''} &nbsp;&nbsp; 派工日期：${new Date().toLocaleDateString('zh-CN')}</div>
    </div>

    <div style="margin-bottom:5px">
      <h3 style="font-size:11px;border-bottom:1.5px solid #333;padding-bottom:2px;margin-bottom:3px">客户信息</h3>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:65px;color:#666;flex-shrink:0">客户姓名：</span><span>${order.customer_name || ''}</span></div>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:65px;color:#666;flex-shrink:0">联系电话：</span><span>${order.customer_phone || ''}</span></div>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:65px;color:#666;flex-shrink:0">安装地址：</span><span>${order.install_address || ''}</span></div>
      <div style="display:flex;margin-bottom:2px;font-size:10px"><span style="width:65px;color:#666;flex-shrink:0">预约安装：</span><span>${order.install_date || ''} ${order.install_time_slot || ''}</span></div>
    </div>

    <div style="margin-bottom:5px">
      <h3 style="font-size:11px;border-bottom:1.5px solid #333;padding-bottom:2px;margin-bottom:3px">安装产品</h3>
      <table style="width:100%;border-collapse:collapse;margin-bottom:8px">
        <thead><tr><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">空间</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">产品名称</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">数量</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">单位</th><th style="border:1px solid #333;padding:2px 4px;background:#f0f0f0;font-size:9px">备注</th></tr></thead>
        <tbody>${itemsHtml}</tbody>
      </table>
    </div>

    <div style="margin-bottom:5px">
      <h3 style="font-size:11px;border-bottom:1.5px solid #333;padding-bottom:2px;margin-bottom:3px">安装确认</h3>
      <div style="font-size:10px">安装完成时间：________ 年 ____ 月 ____ 日  ____ : ____</div>
      <div style="margin-top:4px;font-size:10px">
        <label><input type="checkbox" disabled /> 安装完成，客户验收合格</label>&nbsp;&nbsp;
        <label><input type="checkbox" disabled /> 有遗留问题：________________</label>
      </div>
    </div>

    <div style="display:flex;justify-content:space-between;margin-top:10px">
      <div style="text-align:center;font-size:10px"><div style="width:110px;border-bottom:1px solid #333;margin-top:10px;margin-bottom:2px"></div><div>安装工签字</div></div>
      <div style="text-align:center;font-size:10px"><div style="width:110px;border-bottom:1px solid #333;margin-top:10px;margin-bottom:2px"></div><div>客户签字</div></div>
    </div>
  `)
}

export function printInstallation(order) {
  openPrintWindow(generateInstallationHtml(order))
}


// ─── 公共 ────────────────────────────────────────────────────

function openPrintWindow(html) {
  const w = window.open('', '_blank', 'width=900,height=700')
  if (w) {
    w.document.write(html)
    w.document.close()
  }
}
