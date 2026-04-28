from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Channel = Literal["email", "sms", "call"]


class Student(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    locale: str = "fr-FR"


class Progress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: str
    session_id: str
    session_time_sec: int
    last_activity_at: datetime
    validated: bool = False


class Session(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    student_id: str
    session_type: str
    starting_date: date
    ending_date: date
    product_duration_h: float
    status: str


class QuietHours(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    tz: str


class AppliesTo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_type: str


class GlobalRules(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiet_hours: QuietHours | None = None
    no_sunday_for_channels: list[Channel] = Field(default_factory=list)
    dedupe_window_days_per_channel: dict[Channel, int] = Field(default_factory=dict)


class ActionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Channel
    template_id: str


class Profile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    when_progress_ratio: tuple[float | None, float | None]
    actions: list[ActionSpec] = Field(default_factory=list)

    @field_validator("when_progress_ratio", mode="before")
    @classmethod
    def _coerce_ratio(cls, v: object) -> tuple[float | None, float | None]:
        if isinstance(v, (list, tuple)) and len(v) == 2:
            def to_f(x: object) -> float | None:
                if x is None:
                    return None
                return float(x)

            return (to_f(v[0]), to_f(v[1]))
        raise ValueError("when_progress_ratio must be [low, high]")


class Checkpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    at_session_progress: float = Field(ge=0.0, le=1.0)
    profiles: list[Profile]


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: int
    scenario_id: str
    version: int
    effective_from: date | None = None
    applies_to: AppliesTo
    checkpoints: list[Checkpoint]
    global_: GlobalRules = Field(alias="global")


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: str
    opt_out_per_channel: dict[Channel, bool] = Field(default_factory=dict)
    quiet_hours_start: time | None = None
    quiet_hours_end: time | None = None
    tz: str = "Europe/Paris"


class ActionLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: str
    scenario_id: str
    checkpoint_id: str
    channel: Channel
    template_id: str
    sent_at: datetime
    dedup_key: str


class PlannedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: str
    scenario_id: str
    checkpoint_id: str
    profile_id: str
    channel: Channel
    template_id: str
    scheduled_at: datetime
    dedup_key: str


class ProcessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: str
    scenario_id: str
    planned: list[PlannedAction] = Field(default_factory=list)
    delivered: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
