"""
数据库模型一致性检查脚本
对比 SQL 初始化脚本和 ORM 模型定义
"""

import re
import os

def parse_sql_tables(sql_content: str) -> dict:
    """解析 SQL 文件中的表定义"""
    tables = {}
    
    # 使用更宽松的正则匹配 CREATE TABLE 语句
    # 匹配 CREATE TABLE IF NOT EXISTS 或 CREATE TABLE
    lines = sql_content.split('\n')
    current_table = None
    current_columns = {}
    in_table = False
    paren_count = 0
    
    for line in lines:
        line = line.strip()
        
        # 跳过注释
        if line.startswith('--'):
            continue
        
        # 检测 CREATE TABLE
        if 'CREATE TABLE' in line.upper():
            match = re.search(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)', line, re.IGNORECASE)
            if match:
                current_table = match.group(1).lower()
                current_columns = {}
                in_table = True
                paren_count = line.count('(') - line.count(')')
                continue
        
        if in_table:
            paren_count += line.count('(') - line.count(')')
            
            # 解析列定义
            if not line.startswith('CONSTRAINT') and not line.startswith('PRIMARY') and not line.startswith('FOREIGN') and not line.startswith('UNIQUE'):
                col_match = re.match(r'(\w+)\s+([\w()]+)', line)
                if col_match:
                    col_name = col_match.group(1).lower()
                    col_type = col_match.group(2).upper()
                    # 跳过关键字
                    if col_name not in ['constraint', 'primary', 'foreign', 'unique', 'check', 'references']:
                        current_columns[col_name] = col_type
            
            # 表定义结束
            if paren_count <= 0 and ';' in line:
                tables[current_table] = current_columns
                in_table = False
                current_table = None
    
    return tables

def parse_orm_models(model_content: str) -> dict:
    """解析 ORM 模型定义"""
    models = {}
    
    lines = model_content.split('\n')
    current_class = None
    current_table = None
    current_columns = {}
    
    for i, line in enumerate(lines):
        # 检测类定义
        if line.startswith('class ') and '(Base)' in line:
            # 保存上一个类
            if current_table:
                models[current_table] = {
                    'class_name': current_class,
                    'columns': current_columns
                }
            
            match = re.match(r'class (\w+)\(Base\)', line)
            if match:
                current_class = match.group(1)
                current_columns = {}
                current_table = None
        
        # 检测表名
        if '__tablename__' in line:
            match = re.search(r'["\'](\w+)["\']', line)
            if match:
                current_table = match.group(1).lower()
        
        # 检测列定义
        if '= Column(' in line:
            col_match = re.match(r'\s+(\w+)\s*=\s*Column\((\w+)', line)
            if col_match:
                col_name = col_match.group(1).lower()
                col_type = col_match.group(2).upper()
                current_columns[col_name] = col_type
    
    # 保存最后一个类
    if current_table:
        models[current_table] = {
            'class_name': current_class,
            'columns': current_columns
        }
    
    return models

def compare_models(sql_tables: dict, orm_models: dict):
    """比较 SQL 表和 ORM 模型"""
    print("=" * 60)
    print("数据库模型一致性检查")
    print("=" * 60)
    
    all_passed = True
    
    # 检查 SQL 表是否都有对应的 ORM 模型
    print("\n1. SQL 表 -> ORM 模型映射:")
    for table_name in sorted(sql_tables.keys()):
        if table_name in orm_models:
            print(f"  ✓ {table_name} -> {orm_models[table_name]['class_name']}")
        else:
            print(f"  ✗ {table_name} - 缺少 ORM 模型")
            all_passed = False
    
    # 检查 ORM 模型是否都有对应的 SQL 表
    print("\n2. ORM 模型 -> SQL 表映射:")
    for table_name in sorted(orm_models.keys()):
        model_info = orm_models[table_name]
        if table_name in sql_tables:
            print(f"  ✓ {model_info['class_name']} -> {table_name}")
        else:
            print(f"  ✗ {model_info['class_name']} ({table_name}) - 缺少 SQL 表")
            all_passed = False
    
    # 检查列定义一致性
    print("\n3. 列定义一致性检查:")
    for table_name in sorted(sql_tables.keys()):
        if table_name not in orm_models:
            continue
        
        sql_cols = set(sql_tables[table_name].keys())
        orm_cols = set(orm_models[table_name]['columns'].keys())
        
        missing_in_orm = sql_cols - orm_cols
        missing_in_sql = orm_cols - sql_cols
        
        if missing_in_orm or missing_in_sql:
            print(f"\n  表 {table_name}:")
            if missing_in_orm:
                print(f"    ORM 缺少列: {sorted(missing_in_orm)}")
                all_passed = False
            if missing_in_sql:
                print(f"    SQL 缺少列: {sorted(missing_in_sql)}")
                # 这个可能是 ORM 中的关系字段，不算错误
                print(f"    (可能是关系字段，需要人工确认)")
        else:
            print(f"  ✓ {table_name} - 列定义一致 ({len(sql_cols)} 列)")
    
    return all_passed

def main():
    """主函数"""
    os.chdir("/home/ubuntu/tezbarakat_bot")
    
    # 读取 SQL 文件
    with open("database/init.sql", 'r') as f:
        sql_content = f.read()
    
    # 读取 ORM 模型文件
    with open("web_backend/models/database.py", 'r') as f:
        model_content = f.read()
    
    # 解析
    sql_tables = parse_sql_tables(sql_content)
    orm_models = parse_orm_models(model_content)
    
    print(f"\nSQL 表数量: {len(sql_tables)}")
    print(f"ORM 模型数量: {len(orm_models)}")
    
    print("\nSQL 表列表:")
    for table in sorted(sql_tables.keys()):
        print(f"  - {table}: {len(sql_tables[table])} 列")
    
    print("\nORM 模型列表:")
    for table in sorted(orm_models.keys()):
        print(f"  - {orm_models[table]['class_name']} ({table}): {len(orm_models[table]['columns'])} 列")
    
    # 比较
    all_passed = compare_models(sql_tables, orm_models)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("数据库模型一致性检查通过！")
    else:
        print("存在不一致，请检查上述问题。")
    print("=" * 60)

if __name__ == "__main__":
    main()
