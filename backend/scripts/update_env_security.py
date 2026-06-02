#!/usr/bin/env python3
"""
安全配置更新脚本
用于修复.env文件中的安全问题
"""
import os
import secrets
import shutil
from datetime import datetime

def backup_env():
    """备份当前.env文件"""
    if os.path.exists('.env'):
        backup_name = f'.env.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        shutil.copy('.env', backup_name)
        print(f"✓ 已备份.env到: {backup_name}")
        return backup_name
    return None

def generate_secret_key():
    """生成安全的密钥"""
    return secrets.token_urlsafe(64)

def fix_cors_origins(content):
    """修复CORS配置，移除0.0.0.0"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.startswith('CORS_ORIGINS='):
            # 移除0.0.0.0相关的源
            origins = line.split('=', 1)[1]
            origin_list = [o.strip() for o in origins.split(',')]
            # 过滤掉包含0.0.0.0的源
            filtered = [o for o in origin_list if '0.0.0.0' not in o]
            fixed_line = 'CORS_ORIGINS=' + ','.join(filtered)
            fixed_lines.append(fixed_line)
            print(f"✓ 修复CORS配置: 移除了0.0.0.0源")
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def add_security_warnings(content):
    """添加安全警告注释"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # 在SECRET_KEY前添加警告
        if line.startswith('SECRET_KEY=') and i > 0:
            if '警告' not in lines[i-1]:
                fixed_lines.append('# 警告：生产环境应从环境变量或密钥管理系统获取密钥')
        
        # 在CORS_ORIGINS前添加警告
        if line.startswith('CORS_ORIGINS=') and i > 0:
            if '警告' not in lines[i-1]:
                fixed_lines.append('# 警告：生产环境应仅包含实际的前端域名')
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def main():
    """主函数"""
    print("=" * 60)
    print("安全配置更新脚本")
    print("=" * 60)
    
    if not os.path.exists('.env'):
        print("✗ 错误: .env文件不存在")
        return 1
    
    # 1. 备份
    backup_file = backup_env()
    
    # 2. 读取当前配置
    with open('.env', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 3. 修复CORS配置
    content = fix_cors_origins(content)
    
    # 4. 添加安全警告
    content = add_security_warnings(content)
    
    # 5. 写入修复后的配置
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 已更新.env文件")
    print()
    print("=" * 60)
    print("修复完成！")
    print("=" * 60)
    print()
    print("重要提示:")
    print("1. 请检查.env文件确认修改正确")
    print("2. 生产环境应使用环境变量管理密钥")
    print("3. 确保.env文件不被提交到版本控制")
    print(f"4. 如需回滚，使用备份文件: {backup_file}")
    print()
    print("建议的密钥管理方式:")
    print("  export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')")
    print("  export CSRF_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')")
    
    return 0

if __name__ == '__main__':
    exit(main())
