from decimal import Decimal
from typing import List

from sqlalchemy import select, update as sqlalchemy_update
from starlette import status

from core.config.context import current_user_id
from core.contracts.auditor import Auditor
from core.exceptions.base_exception import BasedException
from database.connection import DatabaseConfiguration
from database.models import VAlmMateriales, Movimientos, AlmacenamientosMateriales, Ajustes
from repositories.ajustes_repository import AjustesRepository
from repositories.almacenamientos_materiales_repository import AlmacenamientosMaterialesRepository
from repositories.almacenamientos_repository import AlmacenamientosRepository
from repositories.movimientos_repository import MovimientosRepository
from schemas.ajustes_schema import AjusteCreate, AjusteResponse
from schemas.logs_auditoria_schema import LogsAuditoriaCreate
from services.logs_auditoria_service import DatabaseAuditor
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil
from utils.time_util import now_local

log = LoggerUtil()

DEFAULT_MOTIVO = "Ajuste automático"

class AjustesService:

    def __init__(self, ajustes_repo: AjustesRepository, movimientos_repo: MovimientosRepository, alm_mat_repo: AlmacenamientosMaterialesRepository, alm_repo: AlmacenamientosRepository, auditor: Auditor) -> None:
        self._repo = ajustes_repo
        self.mov_repo = movimientos_repo
        self.alm_mat_repo = alm_mat_repo
        self.alm_repo = alm_repo
        self.auditor = auditor

    async def create_ajuste(self, ajuste: AjusteCreate) -> List[AjusteResponse]:
        try:
            # Normalizar motivo: si no viene, usar mensaje por defecto
            motivo_final = (ajuste.motivo or "").strip()
            if not motivo_final:
                motivo_final = DEFAULT_MOTIVO

            # Resolver nombre de almacenamiento a ID
            alm_id = await self.alm_repo.get_alm_id_by_name(ajuste.almacenamiento)
            if alm_id is None:
                raise BasedException(
                    message=f"No se encontró el almacenamiento con nombre '{ajuste.almacenamiento}'",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Lista de auditorías fallback (LogsAuditoriaCreate) en caso de que la inserción en la sesión falle
            fallback_audits: list[LogsAuditoriaCreate] = []
            respuestas: List[AjusteResponse] = []

            # Iniciar sesión transaccional
            async with DatabaseConfiguration._async_session() as session:
                async with session.begin():
                    # Obtener todos los registros material-almacenamiento de la vista
                    res = await session.execute(
                        select(VAlmMateriales).where(VAlmMateriales.almacenamiento_id == alm_id)
                    )
                    filas = res.scalars().all()

                    if not filas:
                        raise BasedException(
                            message=f"No se encontraron materiales asociados al almacenamiento '{ajuste.almacenamiento}' (id={alm_id})",
                            status_code=status.HTTP_404_NOT_FOUND
                        )

                    saldo_nuevo = Decimal(ajuste.saldo_nuevo)

                    for vrow in filas:
                        material_id = int(getattr(vrow, 'material_id'))
                        saldo_anterior = Decimal(getattr(vrow, 'saldo', 0) or 0)
                        delta = saldo_nuevo - saldo_anterior

                        if delta == 0:
                            log.info(f"Ajuste omitido para almacenamiento {alm_id}, material {material_id}: saldo ya es {saldo_nuevo}")
                            continue

                        tipo = 'Entrada' if delta > 0 else 'Salida'

                        # Crear ajuste ORM
                        ajuste_obj = Ajustes(
                            almacenamiento_id=alm_id,
                            material_id=material_id,
                            saldo_anterior=saldo_anterior,
                            saldo_nuevo=saldo_nuevo,
                            delta=delta,
                            motivo=motivo_final,
                            usuario_id=current_user_id.get()
                        )
                        session.add(ajuste_obj)
                        await session.flush()
                        await session.refresh(ajuste_obj)

                        # Crear movimiento asociado
                        mov_obj = Movimientos(
                            transaccion_id=None,
                            almacenamiento_id=alm_id,
                            material_id=material_id,
                            tipo=tipo,
                            accion='Ajuste',
                            observacion=f"Ajuste #{getattr(ajuste_obj, 'id', None)}: {motivo_final[:50]}",
                            peso=abs(delta),
                            saldo_anterior=saldo_anterior,
                            saldo_nuevo=saldo_nuevo,
                            usuario_id=current_user_id.get()
                        )
                        session.add(mov_obj)
                        await session.flush()
                        await session.refresh(mov_obj)

                        # Vincular ajuste con movimiento
                        ajuste_obj.movimiento_id = getattr(mov_obj, 'id', None)
                        await session.flush()

                        # Actualizar saldo en almacenamientos_materiales
                        try:
                            update_stmt = (
                                sqlalchemy_update(AlmacenamientosMateriales)
                                .where(AlmacenamientosMateriales.c.almacenamiento_id == alm_id)
                                .where(AlmacenamientosMateriales.c.material_id == material_id)
                                .values(saldo=saldo_nuevo, fecha_hora=now_local(), usuario_id=current_user_id.get())
                            )
                            await session.execute(update_stmt)
                        except Exception as e_update_alm:
                            log.error(f"Error actualizando almacenamientos_materiales para almacen {alm_id}, material {material_id}: {e_update_alm}")

                        # Registrar auditoría para ajuste
                        try:
                            try:
                                valor_nuevo_aj = AnyUtils.serialize_data({
                                    'id': getattr(ajuste_obj, 'id', None),
                                    'almacenamiento_id': getattr(ajuste_obj, 'almacenamiento_id', None),
                                    'material_id': getattr(ajuste_obj, 'material_id', None),
                                    'saldo_anterior': getattr(ajuste_obj, 'saldo_anterior', None),
                                    'saldo_nuevo': getattr(ajuste_obj, 'saldo_nuevo', None),
                                    'delta': getattr(ajuste_obj, 'delta', None),
                                    'motivo': getattr(ajuste_obj, 'motivo', None),
                                    'usuario_id': getattr(ajuste_obj, 'usuario_id', None),
                                    'movimiento_id': getattr(ajuste_obj, 'movimiento_id', None),
                                    'fecha_hora': getattr(ajuste_obj, 'fecha_hora', None),
                                })
                            except Exception as e_ser_aj:
                                log.error(f"Fallo serializando ajuste para auditoría, usar fallback minimal: {e_ser_aj}", exc_info=True)
                                valor_nuevo_aj = AnyUtils.serialize_data({
                                    'id': getattr(ajuste_obj, 'id', None),
                                    'saldo_nuevo': str(getattr(ajuste_obj, 'saldo_nuevo', None))
                                })

                            fallback_audits.append(LogsAuditoriaCreate(
                                entidad='ajustes',
                                entidad_id=str(getattr(ajuste_obj, 'id', None) or ''),
                                accion='CREATE',
                                valor_anterior=None,
                                valor_nuevo=valor_nuevo_aj,
                                fecha_hora=now_local(),
                                usuario_id=current_user_id.get()
                            ))
                            log.info(f"Fallback audit encolado para ajustes id={getattr(ajuste_obj, 'id', None)}")
                        except Exception as e_aud:
                            log.error(f"No se pudo preparar auditoría para ajuste {getattr(ajuste_obj, 'id', None)}: {e_aud}", exc_info=True)

                        # Registrar auditoría para movimiento
                        try:
                            try:
                                valor_nuevo_mov = AnyUtils.serialize_data({
                                    'id': getattr(mov_obj, 'id', None),
                                    'transaccion_id': getattr(mov_obj, 'transaccion_id', None),
                                    'almacenamiento_id': getattr(mov_obj, 'almacenamiento_id', None),
                                    'material_id': getattr(mov_obj, 'material_id', None),
                                    'tipo': getattr(mov_obj, 'tipo', None),
                                    'accion': getattr(mov_obj, 'accion', None),
                                    'observacion': getattr(mov_obj, 'observacion', None),
                                    'peso': getattr(mov_obj, 'peso', None),
                                    'saldo_anterior': getattr(mov_obj, 'saldo_anterior', None),
                                    'saldo_nuevo': getattr(mov_obj, 'saldo_nuevo', None),
                                    'usuario_id': getattr(mov_obj, 'usuario_id', None),
                                    'fecha_hora': getattr(mov_obj, 'fecha_hora', None),
                                })
                            except Exception as e_ser_mov:
                                log.error(f"Fallo serializando movimiento para auditoría, usar fallback minimal: {e_ser_mov}", exc_info=True)
                                valor_nuevo_mov = AnyUtils.serialize_data({
                                    'id': getattr(mov_obj, 'id', None),
                                    'peso': str(getattr(mov_obj, 'peso', None))
                                })

                            fallback_audits.append(LogsAuditoriaCreate(
                                entidad='movimientos',
                                entidad_id=str(getattr(mov_obj, 'id', None) or ''),
                                accion='CREATE',
                                valor_anterior=None,
                                valor_nuevo=valor_nuevo_mov,
                                fecha_hora=now_local(),
                                usuario_id=current_user_id.get()
                            ))
                            log.info(f"Fallback audit encolado para movimiento id={getattr(mov_obj, 'id', None)}")
                        except Exception as e_aud_mov:
                            log.error(f"No se pudo preparar auditoría para movimiento asociado a ajuste {getattr(ajuste_obj, 'id', None)}: {e_aud_mov}", exc_info=True)

                        # Refrescar y agregar a respuestas
                        await session.refresh(ajuste_obj)
                        respuestas.append(AjusteResponse.model_validate(ajuste_obj))

                    # Si todos los materiales tenían delta 0
                    if not respuestas:
                        raise BasedException(
                            message=f"Todos los materiales del almacenamiento '{ajuste.almacenamiento}' ya tienen saldo {saldo_nuevo}",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )

                    # Forzar flush final
                    try:
                        await session.flush()
                    except Exception as e_flush:
                        log.error(f"Error al flush de auditoría en sesión: {e_flush}", exc_info=True)

            # Fin de sesión transaccional

            # Ejecutar fallback audits fuera de la transacción
            if fallback_audits:
                log.info(f"Ejecutando {len(fallback_audits)} fallback audit(s) para ajuste de almacenamiento '{ajuste.almacenamiento}'")
                for audit_create in fallback_audits:
                    try:
                        async with DatabaseConfiguration._async_session() as fallback_session:
                            fallback_auditor = DatabaseAuditor(fallback_session)
                            await fallback_auditor.log_audit(audit_log_data=audit_create)
                            log.info(f"Fallback audit registrado para {audit_create.entidad} {audit_create.entidad_id}")
                    except Exception as e_fallback:
                        log.error(f"Fallo al registrar audit fallback para {audit_create.entidad} {audit_create.entidad_id}: {e_fallback}", exc_info=True)

            return respuestas

        except BasedException:
            raise
        except Exception as e:
            log.error(f"Error al crear ajuste: {e}")
            raise BasedException(message=f"Error inesperado al crear el ajuste: {e}", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
