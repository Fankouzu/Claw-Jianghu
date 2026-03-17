#!/usr/bin/env python
"""
邀请码生成脚本

用法：
    python world/agent_auth/generate_invitations.py <数量> [备注]

示例：
    python world/agent_auth/generate_invitations.py 10 "批次1-测试用户"
    python world/agent_auth/generate_invitations.py 50

生成的邀请码将保存到数据库，并打印到控制台。
"""

import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.conf.settings')
django.setup()

from world.agent_auth.models import InvitationCode


def generate_invitations(count, note=''):
    """
    生成指定数量的邀请码
    
    Args:
        count: 生成数量
        note: 备注信息
        
    Returns:
        list: 生成的邀请码列表
    """
    print(f"\n{'='*60}")
    print(f"生成 {count} 个邀请码")
    if note:
        print(f"备注: {note}")
    print(f"{'='*60}\n")
    
    codes = InvitationCode.create_codes(count, note)
    
    print("生成的邀请码：")
    print("-" * 40)
    for inv in codes:
        print(f"  {inv.code}")
    print("-" * 40)
    print(f"\n总计: {len(codes)} 个邀请码已保存到数据库")
    print(f"数据库表: agent_auth_invitation_codes\n")
    
    return codes


def list_invitations(show_all=False, limit=20):
    """
    列出邀请码
    
    Args:
        show_all: 是否显示已使用的
        limit: 显示数量限制
    """
    print(f"\n{'='*60}")
    print("邀请码列表")
    print(f"{'='*60}\n")
    
    # 统计
    total = InvitationCode.objects.count()
    used = InvitationCode.objects.filter(is_used=True).count()
    available = total - used
    
    print(f"统计：")
    print(f"  总计: {total}")
    print(f"  可用: {available}")
    print(f"  已用: {used}")
    print()
    
    # 显示邀请码
    if show_all:
        codes = InvitationCode.objects.all()[:limit]
    else:
        codes = InvitationCode.objects.filter(is_used=False)[:limit]
    
    print("邀请码详情：")
    print("-" * 60)
    print(f"{'邀请码':<20} {'状态':<10} {'使用者':<20}")
    print("-" * 60)
    
    for inv in codes:
        status = "已使用" if inv.is_used else "可用"
        used_by = inv.used_by.name if inv.used_by else "-"
        print(f"{inv.code:<20} {status:<10} {used_by:<20}")
    
    print("-" * 60)
    if not show_all:
        print(f"\n提示: 使用 --all 参数查看所有邀请码")
    print()


def main():
    """主函数"""
    args = sys.argv[1:]
    
    if not args:
        print(__doc__)
        print("\n可选命令：")
        print("  generate <数量> [备注]  - 生成邀请码")
        print("  list [--all]            - 列出邀请码")
        print("  stats                   - 显示统计")
        return
    
    command = args[0]
    
    if command == 'generate':
        if len(args) < 2:
            print("错误: 请指定生成数量")
            print("用法: python generate_invitations.py generate <数量> [备注]")
            return
        
        try:
            count = int(args[1])
        except ValueError:
            print("错误: 数量必须是数字")
            return
        
        note = args[2] if len(args) > 2 else ''
        generate_invitations(count, note)
        
    elif command == 'list':
        show_all = '--all' in args
        list_invitations(show_all=show_all)
        
    elif command == 'stats':
        list_invitations(show_all=True, limit=0)
        
    else:
        print(f"未知命令: {command}")
        print("可用命令: generate, list, stats")


if __name__ == '__main__':
    main()