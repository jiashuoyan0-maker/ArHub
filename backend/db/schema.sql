CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    template TEXT NOT NULL,          -- idea_discovery | experiment_bridge | auto_review | paper_writing | full_pipeline
    title TEXT NOT NULL,             -- 用户输入的研究方向
    params TEXT DEFAULT '{}',        -- JSON: AUTO_PROCEED, HUMAN_CHECKPOINT 等
    status TEXT DEFAULT 'pending',   -- pending | running | paused | completed | failed
    current_step TEXT,               -- 当前执行的 skill 名称
    workspace_dir TEXT,              -- 工作区目录路径
    enable_checkpoints INTEGER DEFAULT 0,  -- 0=关闭检查点(自动连续执行) 1=开启检查点(步骤完成后暂停确认)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    skill_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',   -- pending | running | waiting_checkpoint | completed | failed | skipped
    has_checkpoint INTEGER DEFAULT 0,
    checkpoint_type TEXT,            -- idea_select | approve | feedback
    output_files TEXT DEFAULT '[]',  -- JSON array
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS workflow_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    step_name TEXT,
    level TEXT DEFAULT 'info',       -- info | warn | error | progress
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    step_name TEXT NOT NULL,
    checkpoint_type TEXT NOT NULL,
    data TEXT DEFAULT '{}',          -- JSON: 展示给用户的数据
    response TEXT,                   -- JSON: 用户的回复
    status TEXT DEFAULT 'pending',   -- pending | resolved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
