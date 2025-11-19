from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.contracts.auditor import Auditor
from core.exceptions.base_exception import BasedException
from database.models import LogsAuditoria
from schemas.logs_auditoria_schema import LogsAuditoriaCreate
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class DatabaseAuditor(Auditor):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_audit(self, audit_log_data: LogsAuditoriaCreate) -> None:
        """
            Logs an audit record using a validated Pydantic model.

            Args:
                audit_log_data (LogsAuditoriaCreate): The validated data for the audit log.
        """
        try:

            audit_log = LogsAuditoria(**audit_log_data.model_dump(exclude_unset=True))

            self.db.add(audit_log)
            await self.db.commit()
            await self.db.refresh(audit_log)

        except Exception as e:
            log.error(f"Error al registrar log de auditoria: {str(e)}")
            raise BasedException(
                message="Error inesperado al registrar log de auditoria.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )