"""App settings, read from environment variables or the repo-root .env file."""

from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env sits at the repo root, one level above backend/.
# In Docker, docker-compose passes the same values as real env vars instead.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def parse_reminder_time(value: str) -> tuple[int, int]:
    """Turn "20:00" into (20, 0). Raises ValueError for anything that isn't a 24-hour HH:MM."""
    hour_text, sep, minute_text = value.strip().partition(":")
    if not (sep and hour_text.isdigit() and minute_text.isdigit() and len(minute_text) == 2):
        raise ValueError(f"REMINDER_TIME={value!r} must look like 20:00 (24-hour HH:MM)")
    hour, minute = int(hour_text), int(minute_text)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"REMINDER_TIME={value!r} is not a real time of day")
    return hour, minute


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    leetcode_username: str = ""
    tz: str = "America/Chicago"
    database_url: str = "sqlite:///./data/tracker.db"
    daily_goal: int = Field(default=1, ge=1)

    # Background jobs (v2). Off by default; tests always run with them off.
    enable_scheduler: bool = False
    sync_interval_hours: float = Field(default=3, gt=0)
    reminder_time: str = "20:00"

    # Phone notifications through ntfy.sh. An empty topic means "don't send anything".
    ntfy_server: str = "https://ntfy.sh"
    ntfy_topic: str = ""

    # Browser origins allowed to call the API directly (comma-separated).
    # The tracker's own dev frontend uses the Vite proxy and doesn't need this; another
    # app (e.g. a dashboard on http://localhost:5173) does.
    cors_origins: str = "http://localhost:5174"

    @field_validator("tz")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        """Fail at startup if TZ is not a real IANA name like 'America/Toronto'."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(
                f"TZ={value!r} is not a valid IANA timezone (example: America/Toronto)"
            ) from error
        return value

    @field_validator("reminder_time")
    @classmethod
    def check_reminder_time(cls, value: str) -> str:
        parse_reminder_time(value)
        return value.strip()

    @property
    def reminder_hour_minute(self) -> tuple[int, int]:
        return parse_reminder_time(self.reminder_time)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


settings = Settings()
