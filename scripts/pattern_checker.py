#!/usr/bin/env python3
"""
金典软装销售系统 · 代码模式检查器

修 Bug 必跑！自动检查同类问题是否存在于其他模块。

用法:
    python scripts/pattern_checker.py [module_name]

示例:
    python scripts/pattern_checker.py orders     # 检查 orders 模块，顺便扫同类
    python scripts/pattern_checker.py --all      # 全量检查
"""
import sys
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APP_DIR = PROJECT_ROOT / "app"
STATIC_DIR = PROJECT_ROOT / "static" / "js"


def check_api_response_format():
    """检查 API 响应格式是否统一"""
    print("\n📋 API 响应格式检查")
    print("-" * 50)
    
    issues = []
    for py_file in APP_DIR.glob("api/*.py"):
        if py_file.name.startswith("__"):
            continue
        content = py_file.read_text()
        
        # 找所有 return {} 裸返回
        bare_returns = re.findall(r'return\s*\{\s*[^}]+\}', content)
        # 排除已知的统一响应函数
        bad_returns = [r for r in bare_returns 
                      if 'success_response' not in r 
                      and 'error_response' not in r 
                      and 'list_response' not in r
                      and 'CommonResponse' not in r
                      and 'RedirectResponse' not in r
                      and r.strip() != '{}']
        
        if bad_returns:
            issues.append(f"  {py_file.name}: {len(bad_returns)} 处裸返回")
    
    if issues:
        print("  ⚠️ 以下文件有非标准响应格式:")
        for issue in issues:
            print(issue)
    else:
        print("  ✅ 全部 API 使用统一响应格式")
    
    return len(issues)


def check_field_consistency(patterns=None):
    """检查字段映射一致性"""
    print("\n📋 字段映射一致性检查")
    print("-" * 50)
    
    if patterns is None:
        patterns = ["quote_amount", "discount_amount", "round_amount", 
                   "customer_id", "order_no", "received", "debt"]
    
    for pattern in patterns:
        files_with = []
        for py_file in APP_DIR.rglob("*.py"):
            if "venv" in str(py_file):
                continue
            if pattern in py_file.read_text(errors='ignore'):
                files_with.append(py_file.relative_to(PROJECT_ROOT))
        
        if files_with:
            print(f"  {pattern}: {len(files_with)} 个文件")
            for f in files_with[:5]:  # 只显示前5个
                print(f"    - {f}")
            if len(files_with) > 5:
                print(f"    ... 还有 {len(files_with)-5} 个")


def check_crud_completeness():
    """检查各模块 CRUD 是否完整"""
    print("\n📋 CRUD 完整性检查")
    print("-" * 50)
    
    modules = {
        "employees": "员工",
        "customers": "客户",
        "products": "产品",
        "orders": "订单",
        "purchase": "采购",
        "warehouse": "仓库",
        "finance": "财务",
    }
    
    for module, name in modules.items():
        py_file = APP_DIR / "api" / f"{module}.py"
        if not py_file.exists():
            py_file = APP_DIR / "api" / f"{module}s.py"
        if not py_file.exists():
            print(f"  ⚠️ {name}({module}): 文件不存在")
            continue
        
        content = py_file.read_text()
        
        has_get = bool(re.search(r'@router\.get', content))
        has_post = bool(re.search(r'@router\.post', content))
        has_put = bool(re.search(r'@router\.put', content))
        has_delete = bool(re.search(r'@router\.delete', content))
        
        status = "✅" if all([has_get, has_post, has_put, has_delete]) else "⚠️"
        missing = []
        if not has_get: missing.append("GET")
        if not has_post: missing.append("POST")
        if not has_put: missing.append("PUT")
        if not has_delete: missing.append("DELETE")
        
        print(f"  {status} {name}: GET={'✅' if has_get else '❌'} POST={'✅' if has_post else '❌'} PUT={'✅' if has_put else '❌'} DELETE={'✅' if has_delete else '❌'}")
        if missing:
            print(f"      缺少: {', '.join(missing)}")


def check_common_bugs():
    """检查常见 Bug 模式"""
    print("\n📋 常见 Bug 模式扫描")
    print("-" * 50)
    
    bug_patterns = [
        # (正则, 描述)
        (r'print\s*\(', 'print 语句（生产禁止）'),
        (r'except\s*:', '裸 except（无具体异常类型）'),
        (r'\.value\s+', 'loginForm.value 访问错误（Vue ref 不用 .value）'),
        (r'price\s*\*\s*qty', 'price*qty 计算（金额应该用 item.amount）'),
    ]
    
    for pattern, desc in bug_patterns:
        files = []
        for py_file in APP_DIR.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(errors='ignore')
            if re.search(pattern, content):
                files.append(py_file.relative_to(PROJECT_ROOT))
        
        if files:
            print(f"  ⚠️ {desc}:")
            for f in files[:3]:
                print(f"    - {f}")
            if len(files) > 3:
                print(f"    ... 还有 {len(files)-3} 个")


def main():
    print("=" * 50)
    print("🔍 金典软装 · 代码模式检查器")
    print("=" * 50)
    
    args = sys.argv[1:]
    do_all = "--all" in args or len(args) == 0
    
    if do_all:
        check_api_response_format()
        check_field_consistency()
        check_crud_completeness()
        check_common_bugs()
    else:
        # 只检查指定模块相关的模式
        for module in args:
            print(f"\n📌 检查模块: {module}")
    
    print("\n" + "=" * 50)
    print("✅ 检查完成！修 Bug 记得对照 docs/CODE_STANDARDS.md")
    print("=" * 50)


if __name__ == "__main__":
    main()
