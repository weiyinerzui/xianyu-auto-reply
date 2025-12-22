-- 添加知识库字段到 item_info 表
ALTER TABLE item_info ADD COLUMN knowledge_base TEXT;
ALTER TABLE item_info ADD COLUMN kb_updated_at TIMESTAMP;
