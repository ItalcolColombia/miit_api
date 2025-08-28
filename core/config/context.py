from contextvars import ContextVar
from datetime import datetime

# Context variable for user_id
current_user_id: ContextVar[int | None] = ContextVar("user_id", default=None)

# Context variable for current timestamp (optional, can be set per operation)
current_timestamp: ContextVar[datetime | None] = ContextVar("fecha_hora", default=None)