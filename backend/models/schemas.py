"""Public data contracts used by the ArHub API and workflow runtime."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_CHECKPOINT = "waiting_checkpoint"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_CHECKPOINT = "waiting_checkpoint"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TemplateType(str, Enum):
    IDEA_DISCOVERY = "idea_discovery"
    EXPERIMENT_BRIDGE = "experiment_bridge"
    AUTO_REVIEW = "auto_review"
    PAPER_WRITING = "paper_writing"
    PAPER_WRITING_ZH = "paper_writing_zh"
    NATURE_WRITING = "nature_writing"
    FULL_PIPELINE = "full_pipeline"
    COMP_CUMCM = "comp_cumcm"
    COMP_MCM = "comp_mcm"
    COMP_HUAWEI = "comp_huawei"
    COMP_MATHORCUP = "comp_mathorcup"
    COMP_APMCM = "comp_apmcm"
    COMP_APMCM_ZH = "comp_apmcm_zh"
    COMP_STATS = "comp_stats"
    COMP_TEDDY = "comp_teddy"
    COMP_CERTCUP = "comp_certcup"
    COMP_HUAZHONG = "comp_huazhong"
    COMP_HUADONG = "comp_huadong"
    COMP_WUYI = "comp_wuyi"
    COMP_SHUWEI = "comp_shuwei"
    COMP_ZHONGQING = "comp_zhongqing"
    COMP_YANGTZE = "comp_yangtze"
    COMP_DIANGONG = "comp_diangong"
    COMP_LIAONING = "comp_liaoning"
    COMP_SHENZHEN = "comp_shenzhen"
    COMP_HUASHU = "comp_huashu"
    COMP_TIANFU = "comp_tianfu"
    COMP_CERTCUP_EN = "comp_certcup_en"
    COMP_SHUWEI_EN = "comp_shuwei_en"
    THESIS_PROPOSAL = "thesis_proposal"
    LITERATURE_REVIEW = "literature_review"
    COURSE_PAPER = "course_paper"
    COURSE_REPORT = "course_report"
    PAPER_FROM_ASSETS = "paper_from_assets"


class WorkflowCreate(BaseModel):
    template: TemplateType
    title: str = Field(min_length=1, description="Research topic or task title")
    params: dict[str, Any] = Field(default_factory=dict)
    enable_checkpoints: bool = False


class StepInfo(BaseModel):
    id: int | None = None
    workflow_id: str | None = None
    skill_name: str
    display_name: str
    step_order: int
    status: StepStatus = StepStatus.PENDING
    has_checkpoint: bool = False
    checkpoint_type: str | None = None
    output_files: list[str] = Field(default_factory=list)
    primary_output: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class WorkflowInfo(BaseModel):
    id: str
    template: TemplateType
    title: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: str | None = None
    workspace_dir: str | None = None
    enable_checkpoints: bool = False
    steps: list[StepInfo] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LogEntry(BaseModel):
    id: int | None = None
    workflow_id: str | None = None
    step_name: str | None = None
    level: str = "info"
    message: str
    created_at: datetime | None = None


class CheckpointData(BaseModel):
    checkpoint_type: str
    step_name: str
    data: dict[str, Any] = Field(default_factory=dict)


class CheckpointResponse(BaseModel):
    action: str
    data: dict[str, Any] = Field(default_factory=dict)
