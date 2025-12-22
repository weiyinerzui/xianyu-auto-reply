#!/usr/bin/env python3
"""
知识库字段迁移脚本
添加 knowledge_base 和 kb_updated_at 字段到 item_info 表
"""
import sqlite3
import sys
from pathlib import Path

def migrate():
    # 使用正确的数据库路径
    db_path = Path(__file__).parent.parent / 'data' / 'xianyu_data.db'
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    print(f"📁 数据库路径: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ 数据库包含 {len(tables)} 个表: {', '.join(tables)}")
        
        # 查找包含 item 的表
        item_tables = [t for t in tables if 'item' in t.lower()]
        if not item_tables:
            print("❌ 未找到商品相关表")
            return False
            
        target_table = item_tables[0]
        print(f"📋 目标表: {target_table}")
        
        # 检查字段是否已存在
        cursor.execute(f"PRAGMA table_info({target_table});")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        print(f"📊 现有字段: {list(columns.keys())}")
        
        # 添加字段
        if 'knowledge_base' not in columns:
            print("➕ 添加 knowledge_base 字段...")
            cursor.execute(f"ALTER TABLE {target_table} ADD COLUMN knowledge_base TEXT;")
            print("✅ knowledge_base 字段添加成功")
        else:
            print("⚠️  knowledge_base 字段已存在")
            
        if 'kb_updated_at' not in columns:
            print("➕ 添加 kb_updated_at 字段...")
            cursor.execute(f"ALTER TABLE {target_table} ADD COLUMN kb_updated_at TIMESTAMP;")
            print("✅ kb_updated_at 字段添加成功")
        else:
            print("⚠️  kb_updated_at 字段已存在")
        
        conn.commit()
        
        # 验证
        cursor.execute(f"PRAGMA table_info({target_table});")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n✅ 迁移完成！最终字段列表:")
        for col in final_columns:
            print(f"  - {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
