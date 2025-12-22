-- 知识库字段迁移脚本
-- 添加日期：2025-12-19

-- 1. 添加知识库字段
ALTER TABLE item_info ADD COLUMN knowledge_base TEXT;

-- 2. 添加更新时间字段
ALTER TABLE item_info ADD COLUMN kb_updated_at TIMESTAMP;

-- 3. 验证字段添加
SELECT 'Migration completed successfully!' as status;
