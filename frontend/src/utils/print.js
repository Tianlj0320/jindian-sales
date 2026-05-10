/**
 * 打印工具 - 生成打印内容并打开打印窗口
 */

/**
 * 生成打印 HTML 模板
 */
function printTemplate(title, contentHtml) {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>${title}</title>
      <style>
        @page { margin: 15mm; }
        body { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 14px; color: #333; }
        .print-header { text-align: center; margin-bottom: 24px; }
        .print-header h1 { font-size: 22px; margin: 0 0 6px 0; }
        .print-header .print-no { color: #999; font-size: 13px; }
        .print-section { margin-bottom: 20px; }
        .print-section h3 { font-size: 16px; border-bottom: 2px solid #333; padding-bottom: 6px; margin-bottom: 12px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
        table th, table td { border: 1px solid #333; padding: 8px 10px; text-align: left; font-size: 13px; }
        table th { background: #f0f0f0; font-weight: bold; }
        .info-row { display: flex; margin-bottom: 8px; }
        .info-label { width: 100px; color: #666; flex-shrink: 0; }
        .info-value { flex: 1; }
        .amount-row { text-align: right; margin-top: 12px; font-size: 15px; }
        .amount-row strong { font-size: 18px; }
        .print-footer { text-align: center; color: #999; font-size: 12px; margin-top: 30px; border-top: 1px dashed #ddd; padding-top: 10px; }
        .signature-area { display: flex; justify-content: space-between; margin-top: 30px; }
        .signature-item { text-align: center; }
        .signature-line { width: 160px; border-bottom: 1px solid #333; margin-top: 40px; margin-bottom: 4px; }
        @media print {
          .no-print { display: none; }
          button { display: none; }
        }
      </style>
    </head>
    <body>
      ${contentHtml}
      <div class="no-print" style="text-align:center;margin-top:20px">
        <button onclick="window.print()" style="padding:10px 30px;font-size:16px;cursor:pointer;background:#409eff;color:#fff;border:0;border-radius:4px">打印</button>
        <button onclick="window.close()" style="padding:10px 30px;font-size:16px;cursor:pointer;background:#909399;color:#fff;border:0;border-radius:4px;margin-left:10px">关闭</button>
      </div>
    </body>
    </html>
  `
}

/**
 * 打印订货合同
 */
export function printContract(order) {
  const itemsHtml = (order.items || []).map(item => `
    <tr>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.width || 0}m × ${item.height || 0}m</td>
      <td>${item.fold_ratio || 2.0}</td>
      <td>${item.qty || 0}</td>
      <td>${item.unit || '米'}</td>
      <td style="text-align:right">¥${(item.unit_price || 0).toFixed(2)}</td>
      <td style="text-align:right">¥${(item.amount || 0).toFixed(2)}</td>
    </tr>
  `).join('')

  const html = printTemplate('订货合同', `
    <div class="print-header">
      <h1>金典软装 · 订货合同</h1>
      <div class="print-no">合同编号：${order.order_no || ''} &nbsp;&nbsp; 日期：${order.order_date || ''}</div>
    </div>

    <div class="print-section">
      <h3>客户信息</h3>
      <div class="info-row"><span class="info-label">客户姓名：</span><span class="info-value">${order.customer_name || ''}</span></div>
      <div class="info-row"><span class="info-label">联系电话：</span><span class="info-value">${order.customer_phone || ''}</span></div>
      <div class="info-row"><span class="info-label">安装地址：</span><span class="info-value">${order.install_address || ''}</span></div>
      <div class="info-row"><span class="info-label">业务员：</span><span class="info-value">${order.salesperson_name || ''}</span></div>
    </div>

    <div class="print-section">
      <h3>产品明细</h3>
      <table>
        <thead>
          <tr><th>空间</th><th>产品名称</th><th>尺寸</th><th>褶皱倍数</th><th>数量</th><th>单位</th><th>单价</th><th>金额</th></tr>
        </thead>
        <tbody>${itemsHtml}</tbody>
      </table>
    </div>

    <div class="print-section">
      <h3>金额结算</h3>
      <div class="amount-row">
        报价金额：¥${(order.quote_amount || 0).toFixed(2)} &nbsp;&nbsp;
        优惠：¥${(order.discount_amount || 0).toFixed(2)} &nbsp;&nbsp;
        抹零：¥${(order.round_amount || 0).toFixed(2)} &nbsp;&nbsp;
        <strong>应收合计：¥${(order.amount || 0).toFixed(2)}</strong>
      </div>
      <div class="amount-row" style="font-size:13px;color:#666">
        已收定金：¥${(order.received || 0).toFixed(2)} &nbsp;&nbsp;
        欠款：¥${((order.debt || 0)).toFixed(2)}
      </div>
    </div>

    <div class="signature-area">
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>客户签字</div>
      </div>
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>业务员</div>
      </div>
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>公司盖章</div>
      </div>
    </div>

    <div class="print-footer">
      金典软装 · 杭州古墩路欧亚达家居广场 &nbsp;|&nbsp; 电话：13800000000
    </div>
  `)

  openPrintWindow(html)
}

/**
 * 打印测量记录单
 */
export function printMeasurement(order) {
  const itemsHtml = (order.items || []).map((item, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.width || 0}</td>
      <td>${item.height || 0}</td>
      <td>${(item.width || 0) * (item.fold_ratio || 2.0)}</td>
      <td></td>
      <td></td>
    </tr>
  `).join('')

  const html = printTemplate('测量记录单', `
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

    <div style="margin-top:16px">
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
  `)

  openPrintWindow(html)
}

/**
 * 打印加工单
 */
export function printProcessing(order) {
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

  const html = printTemplate('加工单', `
    <div class="print-header">
      <h1>金典软装 · 加工单</h1>
      <div class="print-no">订单编号：${order.order_no || ''}</div>
    </div>

    <div class="print-section">
      <h3>订单信息</h3>
      <div class="info-row"><span class="info-label">客户：</span><span class="info-value">${order.customer_name || ''} &nbsp; ${order.customer_phone || ''}</span></div>
      <div class="info-row"><span class="info-label">交货日期：</span><span class="info-value">${order.delivery_date || '-'}</span></div>
      <div class="info-row"><span class="info-label">交货方式：</span><span class="info-value">${order.delivery_method || ''}</span></div>
    </div>

    <div class="print-section">
      <h3>加工明细</h3>
      <table>
        <thead>
          <tr><th>空间</th><th>产品</th><th>宽(m)</th><th>高(m)</th><th>倍率</th><th>数量</th><th>单位</th><th>开合</th><th>工艺</th><th>备注</th></tr>
        </thead>
        <tbody>${itemsHtml}</tbody>
      </table>
    </div>

    <div class="signature-area">
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>加工人</div>
      </div>
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>验收人</div>
      </div>
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>日期</div>
      </div>
    </div>
  `)

  openPrintWindow(html)
}

/**
 * 打印安装派工单
 */
export function printInstallation(order) {
  const itemsHtml = (order.items || []).map(item => `
    <tr>
      <td>${item.room || ''}</td>
      <td>${item.product_name || ''}</td>
      <td>${item.qty || 0}</td>
      <td>${item.unit || '米'}</td>
      <td>${item.note || '-'}</td>
    </tr>
  `).join('')

  const html = printTemplate('安装派工单', `
    <div class="print-header">
      <h1>金典软装 · 安装派工单</h1>
      <div class="print-no">订单编号：${order.order_no || ''} &nbsp;&nbsp; 派工日期：${new Date().toLocaleDateString('zh-CN')}</div>
    </div>

    <div class="print-section">
      <h3>客户信息</h3>
      <div class="info-row"><span class="info-label">客户姓名：</span><span class="info-value">${order.customer_name || ''}</span></div>
      <div class="info-row"><span class="info-label">联系电话：</span><span class="info-value">${order.customer_phone || ''}</span></div>
      <div class="info-row"><span class="info-label">安装地址：</span><span class="info-value">${order.install_address || ''}</span></div>
      <div class="info-row"><span class="info-label">预约安装：</span><span class="info-value">${order.install_date || ''} ${order.install_time_slot || ''}</span></div>
    </div>

    <div class="print-section">
      <h3>安装产品</h3>
      <table>
        <thead><tr><th>空间</th><th>产品名称</th><th>数量</th><th>单位</th><th>备注</th></tr></thead>
        <tbody>${itemsHtml}</tbody>
      </table>
    </div>

    <div class="print-section">
      <h3>安装确认</h3>
      <div>安装完成时间：________ 年 ____ 月 ____ 日  ____ : ____</div>
      <div style="margin-top:8px">
        <label><input type="checkbox" disabled /> 安装完成，客户验收合格</label>&nbsp;&nbsp;
        <label><input type="checkbox" disabled /> 有遗留问题：________________</label>
      </div>
    </div>

    <div class="signature-area">
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>安装工签字</div>
      </div>
      <div class="signature-item">
        <div class="signature-line"></div>
        <div>客户签字</div>
      </div>
    </div>
  `)

  openPrintWindow(html)
}

function openPrintWindow(html) {
  const w = window.open('', '_blank', 'width=900,height=700')
  if (w) {
    w.document.write(html)
    w.document.close()
  }
}
