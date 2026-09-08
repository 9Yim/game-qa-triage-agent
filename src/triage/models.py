"""表单

三张表：
  ReportSource —— 一条反馈的来源信息
  Evidence     —— AI 填某一格时给出的原文依据
  BugReport    —— AI 从留言里提取出来的事实

"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ReportSource(BaseModel):
    #Source from, bug platform can be deduced

    source_id: str
    platform: Literal["PC_Steam", "PS5", "Xbox", "Switch", "Mobile"] = "PC_Steam"
    posted_at: Optional[str] = None


class Evidence(BaseModel):
    # Quote evidence, by what AI conduct

    field: str = Field(description="Name of the field this evidence supports, e.g. actual_result.")

    quote: str = Field(
        description="The sentence from the original report that supports this value. Copy it verbatim - do not paraphrase, reword, or translate."
    )


class BugReport(BaseModel):
    """从玩家的一段原始留言里抽取出来的事实。由 AI 填写。"""

    title: str = Field(description="One-sentence summary of the problem, at most 15 words.")

    build_version: Optional[str] = Field(
        default=None, description="Game build version, e.g. 1.6.14. Leave empty if the report does not mention it."
    )

    repro_steps: list[str] = Field(
        default_factory=list, description="Steps to reproduce, one step per item. Empty list if the report describes none."
    )

    actual_result: str = Field(description="What actually happened.")

    expected_result: Optional[str] = Field(
        default=None, description="What the player expected to happen instead. Leave empty if not stated."
    )

    attempted_solutions: list[str] = Field(
        default_factory=list,
        description="Fixes the player says they have already tried, one per item. Empty list if none are mentioned.",
    )

    frequency: Literal["always", "often", "rare", "once", "unknown"] = Field(
        description="How often the problem occurs."
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
        # keep the exclusion list in sync when adding fields to this model
        description=(
            "Provide one entry per non-empty field, except title, evidence "
            "and extraction_confidence."
        ),
    )

    extraction_confidence: float = Field(
        ge=0.0, le=1.0, description="How confident you are in this extraction, from 0 to 1."
    )
