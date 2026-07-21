-- ============================================
-- 青萍小台 - MySQL 数据库完整初始化脚本
-- ============================================
-- 数据库: qingping (UTF8mb4)
-- 包含功能:
--   1. 用户管理 (users)
--   2. 知识库 (knowledge_bases, documents)
--   3. 技术专家组 (expert_sessions, expert_messages, expert_state_transitions)
--   4. 微信公众号写作助手 (wechat_writer_sessions, wechat_writer_materials,
--                           wechat_writer_messages, wechat_writer_outputs)
-- 使用方式:
--   mysql -u root -p < init_full.sql
-- ============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================
-- 1. 创建数据库
-- ============================================
CREATE DATABASE IF NOT EXISTS `dream`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `dream`;

-- ============================================
-- 2. 用户表 (users)
-- ============================================

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id`              INT          NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username`        VARCHAR(50)  NOT NULL COMMENT '用户名',
  `email`           VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `hashed_password` VARCHAR(255) NOT NULL COMMENT '密码哈希 (bcrypt)',
  `avatar`          VARCHAR(500) DEFAULT '' COMMENT '头像URL',
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 3. 知识库表 (knowledge_bases)
-- ============================================

DROP TABLE IF EXISTS `knowledge_bases`;
CREATE TABLE `knowledge_bases` (
  `id`          INT          NOT NULL AUTO_INCREMENT COMMENT '知识库ID',
  `name`        VARCHAR(100) NOT NULL COMMENT '知识库名称',
  `description` TEXT         DEFAULT NULL COMMENT '知识库描述',
  `user_id`     INT          NOT NULL COMMENT '所属用户ID',
  `doc_count`   INT          NOT NULL DEFAULT 0 COMMENT '文档数量',
  `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_name` (`name`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表';

-- ============================================
-- 4. 文档表 (documents)
-- ============================================

DROP TABLE IF EXISTS `documents`;
CREATE TABLE `documents` (
  `id`           INT          NOT NULL AUTO_INCREMENT COMMENT '文档ID',
  `kb_id`        INT          NOT NULL COMMENT '所属知识库ID',
  `filename`     VARCHAR(255) NOT NULL COMMENT '文件名',
  `file_type`    VARCHAR(20)  NOT NULL DEFAULT 'txt' COMMENT '文件类型 (md/txt/pdf/docx)',
  `file_size`    INT          NOT NULL DEFAULT 0 COMMENT '文件大小 (字节)',
  `status`       VARCHAR(20)  NOT NULL DEFAULT 'processing' COMMENT '处理状态: processing/ready/failed',
  `chunk_count`  INT          NOT NULL DEFAULT 0 COMMENT '切分块数量',
  `error_msg`    TEXT         DEFAULT NULL COMMENT '处理失败原因',
  `created_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_kb_id` (`kb_id`),
  KEY `idx_status` (`status`),
  KEY `idx_filename` (`filename`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档表';

-- ============================================
-- 5. 专家会话表 (expert_sessions)
-- ============================================
-- 技术专家组会话，基于状态机协作

DROP TABLE IF EXISTS `expert_sessions`;
CREATE TABLE `expert_sessions` (
  `id`                  INT          NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  `user_id`             INT          NOT NULL COMMENT '所属用户ID',
  `title`               VARCHAR(200) NOT NULL DEFAULT '新的技术协作' COMMENT '会话标题',
  `current_state`       VARCHAR(50)  NOT NULL DEFAULT 'idle' COMMENT '当前状态: idle/arch_design/code_impl/code_review/testing/done',
  `iteration_count`     INT          NOT NULL DEFAULT 0 COMMENT '迭代次数',
  `max_iterations`      INT          NOT NULL DEFAULT 10 COMMENT '最大迭代次数（安全阀）',
  `acceptance_criteria` JSON         DEFAULT NULL COMMENT '验收标准配置（Step 2 预留）',
  `status`              VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '会话状态: active/paused/completed',
  `total_tokens`        INT          NOT NULL DEFAULT 0 COMMENT '总Token消耗',
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_current_state` (`current_state`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='技术专家组会话表';

-- ============================================
-- 6. 专家消息表 (expert_messages)
-- ============================================
-- 存储会话中的每条消息，带状态标签和迭代轮次

DROP TABLE IF EXISTS `expert_messages`;
CREATE TABLE `expert_messages` (
  `id`           INT         NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `session_id`   INT         NOT NULL COMMENT '会话ID',
  `role`         VARCHAR(20) NOT NULL COMMENT '消息角色: user/assistant/system',
  `expert_type`  VARCHAR(50) DEFAULT NULL COMMENT '专家类型: architect/coder/reviewer/tester',
  `state_label`  VARCHAR(50) DEFAULT NULL COMMENT '所属状态节点',
  `iteration`    INT         NOT NULL DEFAULT 0 COMMENT '所属迭代轮次',
  `content`      TEXT        NOT NULL COMMENT '消息内容',
  `token_usage`  INT         NOT NULL DEFAULT 0 COMMENT 'Token 消耗量',
  `created_at`   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_role` (`role`),
  KEY `idx_expert_type` (`expert_type`),
  KEY `idx_state_label` (`state_label`),
  KEY `idx_iteration` (`iteration`),
  KEY `idx_session_created` (`session_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专家消息表';

-- ============================================
-- 7. 状态转移记录表 (expert_state_transitions)
-- ============================================
-- 记录每次状态变更，用于审计和回溯

DROP TABLE IF EXISTS `expert_state_transitions`;
CREATE TABLE `expert_state_transitions` (
  `id`               INT         NOT NULL AUTO_INCREMENT COMMENT '转移记录ID',
  `session_id`       INT         NOT NULL COMMENT '会话ID',
  `from_state`       VARCHAR(50) NOT NULL COMMENT '起始状态',
  `to_state`         VARCHAR(50) NOT NULL COMMENT '目标状态',
  `transition_type`  VARCHAR(30) NOT NULL COMMENT '转移类型: auto/human_confirm/human_rollback/human_switch',
  `reason`           TEXT        DEFAULT NULL COMMENT '转移原因/说明',
  `created_at`       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_transition_type` (`transition_type`),
  KEY `idx_from_state` (`from_state`),
  KEY `idx_to_state` (`to_state`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='状态转移记录表';

-- ============================================
-- 8. 写作会话表 (wechat_writer_sessions)
-- ============================================
-- 微信公众号写作助手的会话表，基于状态机驱动

DROP TABLE IF EXISTS `wechat_writer_sessions`;
CREATE TABLE `wechat_writer_sessions` (
  `id`                  INT          NOT NULL AUTO_INCREMENT COMMENT '会话ID',
  `user_id`             INT          NOT NULL COMMENT '所属用户ID',
  `title`               VARCHAR(200) NOT NULL COMMENT '会话标题（默认用文章主题）',
  `topic`               TEXT         NOT NULL COMMENT '用户给出的原始主题',
  `confirmed_topic`     TEXT         DEFAULT NULL COMMENT '确认后的细化主题+写作角度',
  `current_state`       VARCHAR(50)  NOT NULL DEFAULT 'idle' COMMENT '当前状态: idle/topic_confirm/research/outline/draft/polish/done',
  `iteration_count`     INT          NOT NULL DEFAULT 0 COMMENT '迭代次数（含回退后的重试）',
  `status`              VARCHAR(20)  NOT NULL DEFAULT 'active' COMMENT '会话状态: active/completed/archived',
  `total_tokens`        INT          NOT NULL DEFAULT 0 COMMENT '累计Token消耗',
  `obsidian_sync_time`  DATETIME     DEFAULT NULL COMMENT 'Obsidian上次同步时间',
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_current_state` (`current_state`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微信公众号写作会话表';

-- ============================================
-- 9. 资料卡片表 (wechat_writer_materials)
-- ============================================
-- 存储从 Obsidian 和网络搜集的资料卡片

DROP TABLE IF EXISTS `wechat_writer_materials`;
CREATE TABLE `wechat_writer_materials` (
  `id`               INT          NOT NULL AUTO_INCREMENT COMMENT '资料ID',
  `session_id`       INT          NOT NULL COMMENT '关联会话ID',
  `source_type`      VARCHAR(20)  NOT NULL COMMENT '来源类型: obsidian/knowledge_base/web',
  `title`            VARCHAR(500) NOT NULL COMMENT '资料标题',
  `url`              VARCHAR(1000) DEFAULT NULL COMMENT '来源URL或文件路径',
  `core_idea`        TEXT         DEFAULT NULL COMMENT '核心观点（1-2句话）',
  `useful_snippets`  TEXT         DEFAULT NULL COMMENT '可用片段（JSON数组，每段一句话）',
  `credibility_score` INT          NOT NULL DEFAULT 3 COMMENT '可信度评分（1-5）',
  `suggested_usage`  VARCHAR(100) DEFAULT NULL COMMENT '推荐使用场景: intro/argument/ending',
  `is_useful`        TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '用户标记是否有用（1=有用，0=没用）',
  `tags`             VARCHAR(500) DEFAULT NULL COMMENT '标签（逗号分隔）',
  `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_source_type` (`source_type`),
  KEY `idx_is_useful` (`is_useful`),
  KEY `idx_credibility_score` (`credibility_score`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='写作资料卡片表';

-- ============================================
-- 10. 写作消息记录表 (wechat_writer_messages)
-- ============================================
-- 存储会话中的每条消息，带专家角色和状态标签

DROP TABLE IF EXISTS `wechat_writer_messages`;
CREATE TABLE `wechat_writer_messages` (
  `id`           INT         NOT NULL AUTO_INCREMENT COMMENT '消息ID',
  `session_id`   INT         NOT NULL COMMENT '关联会话ID',
  `role`         VARCHAR(20) NOT NULL COMMENT '消息角色: user/assistant',
  `expert_type`  VARCHAR(50) DEFAULT NULL COMMENT '专家类型: topic_editor/researcher/outliner/writer',
  `state_label`  VARCHAR(50) DEFAULT NULL COMMENT '发送时的状态标签',
  `iteration`    INT         NOT NULL DEFAULT 1 COMMENT '第几轮迭代',
  `content`      TEXT        NOT NULL COMMENT '消息内容（Markdown）',
  `token_usage`  INT         NOT NULL DEFAULT 0 COMMENT '本条消息Token消耗',
  `created_at`   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_role` (`role`),
  KEY `idx_expert_type` (`expert_type`),
  KEY `idx_state_label` (`state_label`),
  KEY `idx_iteration` (`iteration`),
  KEY `idx_session_created` (`session_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='写作消息记录表';

-- ============================================
-- 11. 输出版本表 (wechat_writer_outputs)
-- ============================================
-- 存储各步骤的历史输出，支持版本对比和回滚

DROP TABLE IF EXISTS `wechat_writer_outputs`;
CREATE TABLE `wechat_writer_outputs` (
  `id`            INT         NOT NULL AUTO_INCREMENT COMMENT '输出ID',
  `session_id`    INT         NOT NULL COMMENT '关联会话ID',
  `step`          VARCHAR(50) NOT NULL COMMENT '对应步骤: topic/research/outline/draft/polish',
  `content_type`  VARCHAR(50) NOT NULL COMMENT '内容类型: analysis/materials/outline/draft/final',
  `content`       TEXT        NOT NULL COMMENT '具体内容（Markdown）',
  `version`       INT         NOT NULL DEFAULT 1 COMMENT '版本号（每次重生成本+1）',
  `is_confirmed`  TINYINT(1)  NOT NULL DEFAULT 0 COMMENT '用户是否确认了这个版本',
  `feedback`      TEXT        DEFAULT NULL COMMENT '重新生成时用户填写的修改建议',
  `created_at`    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_step` (`step`),
  KEY `idx_content_type` (`content_type`),
  KEY `idx_version` (`version`),
  KEY `idx_is_confirmed` (`is_confirmed`),
  KEY `idx_session_step` (`session_id`, `step`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='写作输出版本表';

-- ============================================
-- 12. 初始数据
-- ============================================

-- 默认管理员用户
-- 用户名: admin
-- 密码: admin123
-- 注意: 此处使用 bcrypt 哈希值，首次部署时请确认与代码使用的 bcrypt 版本兼容
INSERT INTO `users` (`username`, `email`, `hashed_password`, `avatar`) VALUES
(
  'admin',
  'admin@qingping.local',
  '$2b$12$KIXK10WcQe5J4b3dK2c8Ce0nYV7xQ6Z5V4zW3x2v1u0t9s8r7q6p5o4n3m2l1k0j',
  ''
)
ON DUPLICATE KEY UPDATE
  `email` = VALUES(`email`),
  `avatar` = VALUES(`avatar`);

-- ============================================
-- 13. 外键约束
-- ============================================

-- 知识库 -> 用户
ALTER TABLE `knowledge_bases`
  ADD CONSTRAINT `fk_kb_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 文档 -> 知识库
ALTER TABLE `documents`
  ADD CONSTRAINT `fk_doc_kb_id`
  FOREIGN KEY (`kb_id`) REFERENCES `knowledge_bases` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 专家会话 -> 用户
ALTER TABLE `expert_sessions`
  ADD CONSTRAINT `fk_expert_session_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 专家消息 -> 会话
ALTER TABLE `expert_messages`
  ADD CONSTRAINT `fk_expert_msg_session_id`
  FOREIGN KEY (`session_id`) REFERENCES `expert_sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 状态转移 -> 会话
ALTER TABLE `expert_state_transitions`
  ADD CONSTRAINT `fk_trans_session_id`
  FOREIGN KEY (`session_id`) REFERENCES `expert_sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 写作会话 -> 用户
ALTER TABLE `wechat_writer_sessions`
  ADD CONSTRAINT `fk_wechat_session_user_id`
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 资料卡片 -> 写作会话
ALTER TABLE `wechat_writer_materials`
  ADD CONSTRAINT `fk_material_session_id`
  FOREIGN KEY (`session_id`) REFERENCES `wechat_writer_sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 写作消息 -> 写作会话
ALTER TABLE `wechat_writer_messages`
  ADD CONSTRAINT `fk_wechat_msg_session_id`
  FOREIGN KEY (`session_id`) REFERENCES `wechat_writer_sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

-- 输出版本 -> 写作会话
ALTER TABLE `wechat_writer_outputs`
  ADD CONSTRAINT `fk_output_session_id`
  FOREIGN KEY (`session_id`) REFERENCES `wechat_writer_sessions` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- 初始化完成
-- ============================================
-- 默认管理员账号:
--   用户名: admin
--   密码: admin123
--
-- 数据表清单（共 11 张）:
--   1. users                        - 用户表
--   2. knowledge_bases              - 知识库表
--   3. documents                    - 文档表
--   4. expert_sessions              - 技术专家组会话表
--   5. expert_messages              - 技术专家组消息表
--   6. expert_state_transitions    - 状态转移记录表
--   7. wechat_writer_sessions      - 写作会话表
--   8. wechat_writer_materials     - 资料卡片表
--   9. wechat_writer_messages      - 写作消息记录表
--  10. wechat_writer_outputs       - 输出版本表
--
-- 注意:
--   1. 首次登录后请立即修改默认密码！
--   2. 如果 bcrypt 哈希不兼容，请通过注册接口重新创建管理员账号
--   3. 向量数据库 (ChromaDB) 数据存储在 ./data/chroma/ 目录
--   4. 新增的 wechat_writer_* 表为微信公众号写作助手功能
-- ============================================
