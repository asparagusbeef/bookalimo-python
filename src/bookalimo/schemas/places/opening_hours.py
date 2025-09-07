from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

from .common import Date, Timestamp


class OpeningHours(BaseModel):
    class SecondaryHoursType(int):
        SECONDARY_HOURS_TYPE_UNSPECIFIED = 0
        DRIVE_THROUGH = 1
        HAPPY_HOUR = 2
        DELIVERY = 3
        TAKEOUT = 4
        KITCHEN = 5
        BREAKFAST = 6
        LUNCH = 7
        DINNER = 8
        BRUNCH = 9
        PICKUP = 10
        ACCESS = 11
        SENIOR_HOURS = 12
        ONLINE_SERVICE_HOURS = 13

    class Period(BaseModel):
        class Point(BaseModel):
            model_config = ConfigDict(extra="forbid")

            day: Optional[int] = Field(default=None, description="0=Sun … 6=Sat")
            hour: Optional[int] = None
            minute: Optional[int] = None
            date: Optional[Date] = None
            truncated: Optional[bool] = None

            @model_validator(mode="after")
            def _ranges(self) -> Self:
                if self.day is not None and not (0 <= self.day <= 6):
                    raise ValueError("day must be in 0..6")
                if self.hour is not None and not (0 <= self.hour <= 23):
                    raise ValueError("hour must be in 0..23")
                if self.minute is not None and not (0 <= self.minute <= 59):
                    raise ValueError("minute must be in 0..59")
                return self

        model_config = ConfigDict(extra="forbid")

        open_: OpeningHours.Period.Point
        close: OpeningHours.Period.Point

    model_config = ConfigDict(extra="forbid")

    open_now: Optional[bool] = None
    periods: List[Period] = Field(default_factory=list)
    weekday_descriptions: List[str] = Field(default_factory=list)
    secondary_hours_type: Optional[int] = Field(
        default=None, description="See SecondaryHoursType"
    )
    special_days: List[OpeningHours.SpecialDay] = Field(default_factory=list)
    next_open_time: Optional[Timestamp] = None
    next_close_time: Optional[Timestamp] = None

    class SpecialDay(BaseModel):
        model_config = ConfigDict(extra="forbid")
        date: Date

    @model_validator(mode="after")
    def _weekday_descs(self) -> Self:
        # Locales vary, but we keep the array reasonable
        if len(self.weekday_descriptions) > 7:
            raise ValueError(
                "weekday_descriptions should not contain more than 7 entries"
            )
        return self
