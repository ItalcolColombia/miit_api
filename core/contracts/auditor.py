from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from schemas.logs_auditoria_schema import LogsAuditoriaCreate


class Auditor(ABC):
    @abstractmethod
    async def log_audit(self, audit_log_data: LogsAuditoriaCreate):
        """
        Logs an audit record for a data modification.

        Args:
            audit_log_data (LogsAuditoriaCreate): The validated data for the audit log.
        Returns:
            None: This method does not return a value.
        """
        pass