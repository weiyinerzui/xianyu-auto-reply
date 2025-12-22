# ==================== 知识库管理方法 ====================
# 添加于 2025-12-19：知识库字段支持

def get_item_knowledge_base(self, cookie_id: str, item_id: str) -> str:
    """获取商品知识库"""
    with self.lock:
        try:
            cursor = self.conn.cursor()
            self._execute_sql(cursor, '''
            SELECT knowledge_base FROM item_info 
            WHERE cookie_id = ? AND id = ?
            ''', (cookie_id, item_id))
            
            result = cursor.fetchone()
            kb = result[0] if result and result[0] else ''
            logger.debug(f"获取商品知识库: {cookie_id}/{item_id}, 长度: {len(kb)}")
            return kb
        except Exception as e:
            logger.error(f"获取商品知识库失败: {e}")
            return ''

def save_item_knowledge_base(self, cookie_id: str, item_id: str, knowledge_base: str) -> bool:
    """保存商品知识库"""
    with self.lock:
        try:
            cursor = self.conn.cursor()
            self._execute_sql(cursor, '''
            UPDATE item_info 
            SET knowledge_base = ?, kb_updated_at = CURRENT_TIMESTAMP
            WHERE cookie_id = ? AND id = ?
            ''', (knowledge_base, cookie_id, item_id))
            
            self.conn.commit()
            logger.info(f"保存商品知识库成功: {cookie_id}/{item_id}, 长度: {len(knowledge_base)}")
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"保存商品知识库失败: {e}")
            self.conn.rollback()
            return False

def get_item_info_with_kb(self, cookie_id: str, item_id: str) -> Optional[dict]:
    """获取商品信息（包含知识库）"""
    with self.lock:
        try:
            cursor = self.conn.cursor()
            self._execute_sql(cursor, '''
            SELECT id, title, price, desc, knowledge_base, kb_updated_at
            FROM item_info 
            WHERE cookie_id = ? AND id = ?
            ''', (cookie_id, item_id))
            
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'title': result[1],
                    'price': result[2],
                    'desc': result[3],
                    'knowledge_base': result[4] or '',
                    'kb_updated_at': result[5]
                }
            return None
        except Exception as e:
            logger.error(f"获取商品信息失败: {e}")
            return None

def batch_export_knowledge_bases(self, cookie_id: Optional[str] = None) -> dict:
    """批量导出知识库
    
    Args:
        cookie_id: 账号ID，如果为None则导出所有账号
    
    Returns:
        dict: {item_id: {title, knowledge_base, updated_at}}
    """
    with self.lock:
        try:
            cursor = self.conn.cursor()
            if cookie_id:
                query = '''
                SELECT id, title, knowledge_base, kb_updated_at
                FROM item_info 
                WHERE cookie_id = ? AND knowledge_base IS NOT NULL AND knowledge_base != ''
                '''
                self._execute_sql(cursor, query, (cookie_id,))
            else:
                query = '''
                SELECT id, title, knowledge_base, kb_updated_at, cookie_id
                FROM item_info 
                WHERE knowledge_base IS NOT NULL AND knowledge_base != ''
                '''
                self._execute_sql(cursor, query)
            
            results = cursor.fetchall()
            export_data = {}
            
            for row in results:
                item_data = {
                    'title': row[1],
                    'knowledge_base': row[2],
                    'updated_at': row[3]
                }
                if not cookie_id:
                    item_data['cookie_id'] = row[4]
                    
                export_data[row[0]] = item_data
            
            logger.info(f"导出知识库: {len(export_data)} 个商品")
            return export_data
        except Exception as e:
            logger.error(f"批量导出知识库失败: {e}")
            return {}

def bat_import_knowledge_bases(self, import_data: dict, cookie_id: str) -> tuple[int, int]:
    """批量导入知识库
    
    Args:
        import_data: {item_id: knowledge_base_text}
        cookie_id: 目标账号ID
    
    Returns:
        tuple: (成功数量, 失败数量)
    """
    with self.lock:
        success_count = 0
        fail_count = 0
        
        try:
            cursor = self.conn.cursor()
            
            for item_id, kb_text in import_data.items():
                try:
                    self._execute_sql(cursor, '''
                    UPDATE item_info 
                    SET knowledge_base = ?, kb_updated_at = CURRENT_TIMESTAMP
                    WHERE cookie_id = ? AND id = ?
                    ''', (kb_text, cookie_id, item_id))
                    
                    if cursor.rowcount > 0:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"导入知识库失败 {item_id}: {e}")
                    fail_count += 1
            
            self.conn.commit()
            logger.info(f"批量导入知识库: 成功 {success_count}, 失败 {fail_count}")
            return (success_count, fail_count)
            
        except Exception as e:
            logger.error(f"批量导入知识库失败: {e}")
            self.conn.rollback()
            return (0, len(import_data))
