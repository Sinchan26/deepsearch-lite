from pydantic import Field, model_validator

from app.domain.models import Limits, Model


class Settings(Model):
    ceilings: Limits = Field(default_factory=Limits)
    active_runs: int = Field(default=2, gt=0, le=2)
    retained_runs: int = Field(default=20, gt=0, le=20)
    terminal_ttl: float = Field(default=900, gt=0, le=900)
    event_count: int = Field(default=512, gt=0, le=512)
    event_bytes: int = Field(default=1048576, ge=65536, le=1048576)
    subscribers_per_run: int = Field(default=4, gt=0, le=4)
    heartbeat_seconds: float = Field(default=15, gt=0, le=15)
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")

    @model_validator(mode="after")
    def hard_ceilings(self) -> "Settings":
        defaults = Limits()
        if any(getattr(self.ceilings, key) > getattr(defaults, key) for key in Limits.model_fields):
            raise ValueError("server ceilings cannot exceed the architecture limits")
        if "*" in self.cors_origins:
            raise ValueError("CORS requires explicit origins")
        return self
