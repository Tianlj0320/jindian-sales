/**
 * 占位测试 — 验证 Vitest 测试基础设施正常工作
 */

import { describe, it, expect } from 'vitest'

describe('测试基础设施', () => {
  it('基础断言工作', () => {
    expect(1 + 1).toBe(2)
  })

  it('import 工作', async () => {
    const vue = await import('vue')
    expect(vue.ref).toBeDefined()
  })

  it('localStorage mock 工作', () => {
    localStorage.setItem('test-key', 'test-value')
    expect(localStorage.getItem('test-key')).toBe('test-value')
  })
})
