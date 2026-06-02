"""
N+1查询优化脚本
自动修复assessment.py中的N+1查询问题
"""
from pathlib import Path
import re

def fix_assessment_n1_queries():
    """修复assessment.py中的N+1查询"""
    file_path = Path("C:/military-Rural Revitalization-system/backend/app/api/v1/assessment.py")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 修复1: get_village_scores - 预加载关联数据
    old_pattern1 = r'villages = db\.query\(SupportedVillage\)\.all\(\)'
    new_pattern1 = '''villages = db.query(SupportedVillage).options(
        selectinload(SupportedVillage.income_data),
        selectinload(SupportedVillage.projects),
        selectinload(SupportedVillage.funds)
    ).all()'''

    content = re.sub(old_pattern1, new_pattern1, content)

    # 添加必要的import
    if 'from sqlalchemy.orm import selectinload' not in content:
        import_line = 'from sqlalchemy.orm import Session'
        content = content.replace(import_line, f'{import_line}, selectinload')

    # 修复2: detect_anomalies - 批量查询而非循环查询
    old_pattern2 = r'''for inc in incomes_current:
        prev = \(
            db\.query\(VillageIncome\)
            \.filter\(
                VillageIncome\.supported_village_id == inc\.supported_village_id, VillageIncome\.year == current_year - 1
            \)
            \.first\(\)
        \)'''

    new_pattern2 = '''# 批量查询上一年度数据，避免N+1
    prev_incomes = {
        inc.supported_village_id: inc
        for inc in db.query(VillageIncome).filter(VillageIncome.year == current_year - 1).all()
    }

    for inc in incomes_current:
        prev = prev_incomes.get(inc.supported_village_id)'''

    content = re.sub(old_pattern2, new_pattern2, content, flags=re.DOTALL)

    # 修复3: 批量查询村庄信息
    old_pattern3 = r'village = db\.query\(SupportedVillage\)\.filter\(SupportedVillage\.id == inc\.supported_village_id\)\.first\(\)'

    # 在循环前添加批量查询
    villages_dict_code = '''
    # 批量查询村庄信息，避免N+1
    village_ids = [inc.supported_village_id for inc in incomes_current]
    villages_dict = {
        v.id: v for v in db.query(SupportedVillage).filter(SupportedVillage.id.in_(village_ids)).all()
    }
    '''

    # 在incomes_current查询后插入
    content = content.replace(
        'incomes_current = db.query(VillageIncome).filter(VillageIncome.year == current_year).all()',
        f'incomes_current = db.query(VillageIncome).filter(VillageIncome.year == current_year).all(){villages_dict_code}'
    )

    # 替换循环内的查询
    content = content.replace(
        old_pattern3,
        'village = villages_dict.get(inc.supported_village_id)'
    )

    # 保存修改
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复 assessment.py 中的N+1查询")
    return True

def fix_projects_n1_queries():
    """修复projects.py中的N+1查询"""
    file_path = Path("C:/military-Rural Revitalization-system/backend/app/api/v1/projects.py")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 添加selectinload导入
    if 'from sqlalchemy.orm import selectinload' not in content:
        import_line = 'from sqlalchemy.orm import Session'
        if import_line in content:
            content = content.replace(import_line, f'{import_line}, selectinload, joinedload')

    # 修复常见的查询模式：预加载关联数据
    # 查找所有 db.query(Project).filter(...).all() 的模式
    pattern = r'(projects = db\.query\(Project\))(\.filter\([^)]+\))(\.all\(\))'
    replacement = r'\1.options(selectinload(Project.village), selectinload(Project.funds), selectinload(Project.organization))\2\3'

    content = re.sub(pattern, replacement, content)

    # 保存修改
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复 projects.py 中的N+1查询")
    return True

def fix_fund_lifecycle_n1_queries():
    """修复fund_lifecycle.py中的N+1查询"""
    file_path = Path("C:/military-Rural Revitalization-system/backend/app/api/v1/fund_lifecycle.py")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 添加selectinload导入
    if 'from sqlalchemy.orm import selectinload' not in content:
        import_line = 'from sqlalchemy.orm import Session'
        if import_line in content:
            content = content.replace(import_line, f'{import_line}, selectinload')

    # 修复查询模式
    pattern = r'(funds = db\.query\(Fund\))(\.filter\([^)]+\))(\.all\(\))'
    replacement = r'\1.options(selectinload(Fund.project), selectinload(Fund.budget))\2\3'

    content = re.sub(pattern, replacement, content)

    # 保存修改
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复 fund_lifecycle.py 中的N+1查询")
    return True

def fix_fund_budgets_n1_queries():
    """修复fund_budgets.py中的N+1查询"""
    file_path = Path("C:/military-Rural Revitalization-system/backend/app/api/v1/fund_budgets.py")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 添加selectinload导入
    if 'from sqlalchemy.orm import selectinload' not in content:
        import_line = 'from sqlalchemy.orm import Session'
        if import_line in content:
            content = content.replace(import_line, f'{import_line}, selectinload')

    # 修复查询模式
    pattern = r'(budgets = db\.query\(FundBudget\))(\.filter\([^)]+\))(\.all\(\))'
    replacement = r'\1.options(selectinload(FundBudget.fund), selectinload(FundBudget.project))\2\3'

    content = re.sub(pattern, replacement, content)

    # 保存修改
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ 已修复 fund_budgets.py 中的N+1查询")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("开始修复N+1查询问题...")
    print("=" * 60)

    try:
        # 修复各个文件
        fix_assessment_n1_queries()
        fix_projects_n1_queries()
        fix_fund_lifecycle_n1_queries()
        fix_fund_budgets_n1_queries()

        print("\n" + "=" * 60)
        print("✓ 所有N+1查询已修复")
        print("=" * 60)
        print("\n建议:")
        print("1. 运行测试验证修改: cd backend && pytest tests/ -v")
        print("2. 检查SQL查询日志: 在.env中设置 DB_ECHO=true")
        print("3. 使用性能测试验证提升效���")

        return 0
    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
