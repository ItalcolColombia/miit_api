import uuid
from typing import List, Optional

from fastapi_pagination import Page, Params
from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.db_exception import DatabaseSQLAlchemyException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.models import Pesadas, Transacciones
from repositories.pesadas_corte_repository import PesadasCorteRepository
from repositories.pesadas_repository import PesadasRepository
from schemas.pesadas_corte_schema import PesadasCalculate, PesadasCorteCreate, PesadasRange, \
    PesadaCorteRetrieve
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate, VPesadasAcumResponse
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class PesadasService:

    def __init__(self, pesada_repository: PesadasRepository, pesadas_corte_repository: PesadasCorteRepository) -> None:
        self._repo = pesada_repository
        self._repo_corte = pesadas_corte_repository

    async def create_pesada(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
        Create a new pesada in the database.

        Args:
            pesada_data (PesadaCreate): The data for the pesada to be created.

        Returns:
            PesadaResponse: The created pesada object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            pesada_model = Pesadas(**pesada_data.model_dump())
            created_pesada = await self._repo.create(pesada_model)
            log.info(f"Pesada creada con referencia: {created_pesada.referencia}")
            return PesadaResponse.model_validate(created_pesada)
        except Exception as e:
            log.error(f"Error al crear pesada: {e}")
            raise BasedException(
                message="Error inesperado al crear la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update_pesada(self, pesada_id: int, pesada: PesadaUpdate) -> Optional[PesadaResponse]:
        """
        Update an existing pesada in the database.

        Args:
            pesada_id (int): The ID of the pesada to update.
            pesada (PesadaUpdate): The updated pesada data.

        Returns:
            Optional[PesadaResponse]: The updated pesada object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            pesada_model = Pesadas(**pesada.model_dump())
            updated_pesada = await self._repo.update(pesada_id, pesada_model)
            log.info(f"Pesada actualizada con ID: {pesada_id}")
            return PesadaResponse.model_validate(updated_pesada) if updated_pesada else None
        except Exception as e:
            log.error(f"Error al actualizar pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete_pesada(self, pesada_id: int) -> bool:
        """
        Delete a pesada from the database.

        Args:
            pesada_id (int): The ID of the pesada to delete.

        Returns:
            bool: True if the pesada was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(pesada_id)
            log.info(f"Pesada eliminada con ID: {pesada_id}")
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_pesada(self, pesada_id: int) -> Optional[PesadaResponse]:
        """
        Retrieve a pesada by its ID.

        Args:
            pesada_id (int): The ID of the pesada to retrieve.

        Returns:
            Optional[PesadaResponse]: The pesada object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            pesada = await self._repo.get_by_id(pesada_id)
            return PesadaResponse.model_validate(pesada) if pesada else None
        except Exception as e:
            log.error(f"Error al obtener pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la pesada.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_pesadas(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[PesadaResponse]:
        """
        Retrieve paginated pesadas, optionally filtered by transaction ID.

        Args:
            tran_id (Optional[int]): The ID of the transaction to filter by, if provided.
            params (Params): Pagination parameters.

        Returns:
            Page[PesadaResponse]: A paginated list of pesada objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Pesadas)

            if tran_id is not None:
                query = query.where(Pesadas.transaccion_id == tran_id)

            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener pesadas paginadas con tran_id {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener las pesadas paginadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_pesadas(self) -> List[PesadaResponse]:
        """
        Retrieve all pesadas from the database.

        Returns:
            List[PesadaResponse]: A list of all pesada objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            pesadas = await self._repo.get_all()
            return [PesadaResponse.model_validate(p) for p in pesadas]
        except Exception as e:
            log.error(f"Error al obtener todas las pesadas: {e}")
            raise BasedException(
                message="Error inesperado al obtener las pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_pesada_if_not_exists(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
        Check if a pesada with the same transaction ID and consecutivo already exists. If not, create a new one.

        Args:
            pesada_data (PesadaCreate): The data for the pesada to be created.

        Returns:
            PesadaResponse: The existing or newly created pesada object.

        Raises:
            EntityAlreadyRegisteredException: If a pesada with the same transaction ID and consecutivo already exists.
            BasedException: For unexpected errors during the creation process.
        """
        try:
            # 1. Validar si transacción ya existe
            if await self._repo.find_one(transaccion_id=pesada_data.transaccion_id,
                                         consecutivo=pesada_data.consecutivo):
                raise EntityAlreadyRegisteredException(f"En la transacción {pesada_data.transaccion_id} ya existe una pesada con ese consecutivo '{pesada_data.consecutivo}'")

            # 2. Se crea transacción si esta no existe en la BD
            pesada_nueva = await self._repo.create(pesada_data)
            return pesada_nueva
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(
                f"Error al crear pesada para transacción {pesada_data.transaccion_id} con consecutivo {pesada_data.consecutivo}: {e}")
            raise BasedException(
                message="Error inesperado al crear la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def create_pesadas_corte_if_not_exists(self, acum_data: List[PesadasCalculate]) -> List[PesadasCorteCreate]:
        """
        Check if a pesadas_corte record with the same transaction ID and consecutivo already exists. If not, create a new one.

        Args:
            acum_data(PesadasCalculate): The data of accumulated weight.

        Returns:
            List[PesadasCorteCreate]: The list of existing or newly created pesadas_corte records.

        Raises:
            EntityAlreadyRegisteredException: If pesadas_corte already exists.
            BasedException: For unexpected errors during creation or retrieval.
        """
        try:
            if not acum_data:
                raise ValueError("No hay pesaje por procesar")

            log.info(f"create_pesadas_corte_if_not_exists: recibidos {len(acum_data)} acumulados")

            # STEP 1: Preparar cortes calculando el siguiente consecutivo por transacción
            pesadas_corte_data = []
            # next_map mantiene el siguiente consecutivo esperado por transacción durante la preparación del batch
            next_map: dict[int, int] = {}
            for item in acum_data:
                try:
                    tran = getattr(item, 'transaccion', None)
                    # Calcular el siguiente consecutivo por transacción usando conteo de registros existentes
                    next_consec = 1
                    if tran is not None:
                        try:
                            tkey = int(tran)
                            if tkey not in next_map:
                                existing_count = await self._repo_corte.count_by_transaccion(tkey)
                                next_map[tkey] = int(existing_count)
                            # el siguiente consecutivo es el contador actual + 1
                            next_consec = next_map[tkey] + 1
                            # reservar/incrementar para próximos items del mismo tran en este batch
                            next_map[tkey] = next_map[tkey] + 1
                        except Exception:
                            next_consec = 1

                    puerto_prefix = (item.puerto_id.split('-')[0] if getattr(item, 'puerto_id', None) else 'REF')
                    # Generar ref definitivo usando consecutivo por transacción
                    # Usar uuid5 determinístico por transacción para que la parte intermedia sea constante entre registros de la misma transacción
                    if tran is not None:
                        try:
                            token_mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(int(tran)))).replace('-', '')[:8].upper()
                        except Exception:
                            token_mid = str(uuid.uuid4())[:8].upper()
                    else:
                        token_mid = str(uuid.uuid4())[:8].upper()
                    new_ref = f"{puerto_prefix}-{token_mid}-{next_consec}"

                    # Preparar campos con conversiones explícitas para evitar problemas de tipo
                    puerto_val = getattr(item, 'puerto_id', None) or ''
                    trans_val = getattr(item, 'transaccion', None)
                    pit_val = getattr(item, 'pit', None)
                    material_val = getattr(item, 'material', '') or ''
                    peso_val = getattr(item, 'peso', None)
                    fecha_val = getattr(item, 'fecha_hora', None)
                    usuario_val = getattr(item, 'usuario_id', None)

                    from decimal import Decimal
                    try:
                        peso_dec = Decimal(str(peso_val)) if peso_val is not None else None
                    except Exception:
                        peso_dec = None

                    # El campo 'consecutivo' en la respuesta representa viaje_id (no es un contador).
                    viaje_id_val = getattr(item, 'consecutivo', None)
                    pesadas_corte_data.append(
                        PesadasCorteCreate(
                            puerto_id=puerto_val,
                            transaccion=int(trans_val) if trans_val is not None else None,
                            # usar viaje_id en el campo consecutivo
                            consecutivo=int(viaje_id_val) if viaje_id_val is not None else None,
                            pit=int(pit_val) if pit_val is not None else None,
                            material=material_val,
                            peso=peso_dec,
                            ref=new_ref,
                            enviado=True,
                            fecha_hora=fecha_val,
                            usuario_id=int(usuario_val) if usuario_val is not None else None,
                        )
                    )
                    log.info(f"Prepared pesadas_corte_data item: puerto={puerto_val} transaccion={trans_val} consecutivo={next_consec} peso={peso_dec} fecha_hora={fecha_val}")
                except Exception as inner_e:
                    log.error(f"Error preparando pesadas_corte para item {item}: {inner_e}", exc_info=True)

            if not pesadas_corte_data:
                try:
                    preview_acum = [
                        (a.model_dump() if hasattr(a, 'model_dump') else dict(a))
                        for a in acum_data[:5]
                    ]
                except Exception:
                    preview_acum = [str(a) for a in acum_data[:5]]
                log.warning(f"create_pesadas_corte_if_not_exists: no se prepararon registros para crear en pesadas_corte. preview acum_data={preview_acum}")

            try:
                # Antes de lanzar create_bulk, registrar cantidad y ejemplos para diagnóstico
                try:
                    preview = [
                        {"puerto_id": getattr(p, 'puerto_id', None), "transaccion": getattr(p, 'transaccion', None), "consecutivo": getattr(p, 'consecutivo', None)}
                        for p in pesadas_corte_data[:5]
                    ]
                except Exception:
                    preview = []
                log.info(f"create_pesadas_corte_if_not_exists: intentando create_bulk con {len(pesadas_corte_data)} items; ejemplos={preview}")

                # Crear registros y obtener sus IDs (ya vienen con ref y consecutivo correctos)
                creada_intermedia = await self._repo_corte.create_bulk(pesadas_corte_data)

                created_count = len(creada_intermedia) if creada_intermedia else 0
                log.info(f"create_pesadas_corte_if_not_exists: create_bulk devolvió {created_count} registros")

                # Si create_bulk no creó todos los registros esperados, intentar creación individual
                if not creada_intermedia or (isinstance(creada_intermedia, list) and len(creada_intermedia) < len(pesadas_corte_data)):
                    log.warning("create_pesadas_corte_if_not_exists: create_bulk no creó todos los registros, intentando crear individualmente")
                    created_individual = []
                    for idx, item_to_create in enumerate(pesadas_corte_data):
                        try:
                            created_single = await self._repo_corte.create(item_to_create)
                            created_individual.append(created_single)
                            log.info(f"create_pesadas_corte_if_not_exists: creado individual {idx+1}/{len(pesadas_corte_data)} -> transaccion={getattr(item_to_create,'transaccion',None)} consecutivo={getattr(item_to_create,'consecutivo',None)}")
                        except Exception as ex_single:
                            log.error(f"Error creando pesadas_corte individual para transaccion={getattr(item_to_create,'transaccion',None)}: {ex_single}", exc_info=True)

                    if created_individual:
                        log.info(f"create_pesadas_corte_if_not_exists: creación individual devolvió {len(created_individual)} registros")
                        return created_individual
                    else:
                        log.warning("create_pesadas_corte_if_not_exists: creación individual no produjo registros")

                return creada_intermedia
            except Exception as e:
                # Si la creación falla, intentamos recuperar los cortes existentes (fallback)
                log.error(f"create_bulk falló para pesadas_corte: {e}", exc_info=True)
                recovered = []
                for item in acum_data:
                    try:
                        existing = await self._repo_corte.find_many(puerto_id=item.puerto_id, transaccion=item.transaccion)
                        if existing:
                            recovered.extend(existing)
                    except Exception as ex_inner:
                        log.error(f"Error al recuperar pesadas_corte existentes para puerto {item.puerto_id} transaccion {item.transaccion}: {ex_inner}", exc_info=True)

                if recovered:
                    log.info(f"Se recuperaron {len(recovered)} pesadas_corte existentes tras fallo de creación.")
                    return recovered
                else:
                    # No pudimos recuperar nada: volver a elevar excepción para que sea tratado arriba
                    raise

        except ValueError as e:
            log.error(f"Validation error for pesadas_corte: {e}")
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error al registrar pesadas_corte : {e}", exc_info=True)
            raise BasedException(
                message=f"Error inesperado al registrar pesadas_corte: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def gen_pesada_identificador(self, pesada_data: PesadaCorteRetrieve) -> str:
        """
            Generate a unique identifier for a pesada_corte record.

            Args:
                pesada_data (PesadaCorteRetrieve): The data used to generate the identifier.

            Returns:
                str: The generated pesada identifier.

            Raises:
                BasedException: For validation or unexpected errors.
        """

        try:
            pesada_id: str

            # 1. Calcular siguiente consecutivo por transacción usando count_by_transaccion
            tran = getattr(pesada_data, 'transaccion', None)
            next_consec = 1
            if tran is not None:
                try:
                    existing_count = await self._repo_corte.count_by_transaccion(int(tran))
                    next_consec = int(existing_count) + 1
                except Exception:
                    next_consec = 1

            puerto_prefix = pesada_data.puerto_id.split('-')[0] if pesada_data.puerto_id else 'REF'
            # usar uuid5 para que sea estable por transacción
            if tran is not None:
                try:
                    token_mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(int(tran)))).replace('-', '')[:8].upper()
                except Exception:
                    token_mid = str(uuid.uuid4())[:8].upper()
            else:
                token_mid = str(uuid.uuid4())[:8].upper()
            pesada_id = f"{puerto_prefix}-{token_mid}-{next_consec}"

            return pesada_id

        except Exception as e:
            log.error(f"Error al generar identificador para pesada_corte: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al generar el identificador de la pesada.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pesadas_acumuladas(self, puerto_id: str, tran_id: Optional[int] = None) -> List[VPesadasAcumResponse]:
        """
        Obtener y procesar pesadas acumuladas para un puerto (y opcionalmente una transacción).

        Flujo:
        1) Obtener acumulado agrupado de pesadas no leídas (repo.get_sumatoria_pesadas)
        2) Validar que hay acumulados (si no, lanzar EntityNotFoundException)
        3) Construir rangos (primera/ultima) y crear registros en pesadas_corte (creación robusta)
        4) Marcar las pesadas dentro de los rangos como leídas
        5) Construir y devolver la lista de VPesadasAcumResponse a partir de los registros de pesadas_corte
        """
        try:
            # 1. Obtener acumulado
            acumulado = await self._repo.get_sumatoria_pesadas(puerto_id, tran_id)
            if not acumulado:
                raise EntityNotFoundException("No hay pesadas nuevas por reportar.")

            # 2. Construir rangos para marcar como leídas (solo donde existan ids válidos)
            pesada_range = [
                PesadasRange(primera=acum.primera, ultima=acum.ultima, transaccion=acum.transaccion)
                for acum in acumulado
                if getattr(acum, 'primera', None) is not None and getattr(acum, 'ultima', None) is not None and getattr(acum, 'transaccion', None) is not None
            ]

            # 3. Intentar crear registros en pesadas_corte y usar esos registros para construir la respuesta.
            pesadas_corte_records = None
            try:
                pesadas_corte_records = await self.create_pesadas_corte_if_not_exists(acumulado)
            except Exception as e_create:
                log.error(f"No fue posible crear pesadas_corte (no crítico): {e_create}", exc_info=True)

            # 4. Marcar las pesadas como leídas solo si existen rangos
            if pesada_range:
                ids_marcados = await self._repo.mark_pesadas(pesada_range)
                log.info(f"{len(ids_marcados)} Pesadas marcadas como leído.")

            # 5. Construir la respuesta: preferir registros de pesadas_corte (tienen la ref con el consecutivo por transacción)
            response: List[VPesadasAcumResponse] = []
            from decimal import Decimal
            from datetime import datetime

            # Mapear acumulado por transaccion para poder mantener 'consecutivo' (viaje) en la respuesta
            acum_map = {int(getattr(a, 'transaccion')): a for a in acumulado}

            if pesadas_corte_records:
                # pesadas_corte_records pueden ser Pydantic models o listas de dicts/schemas
                for corte in pesadas_corte_records:
                    try:
                        # obtener atributos del corte
                        ref = getattr(corte, 'ref', None) or (corte.get('ref') if isinstance(corte, dict) else None)
                        trans = getattr(corte, 'transaccion', None) or (corte.get('transaccion') if isinstance(corte, dict) else None)
                        pit = getattr(corte, 'pit', None) or (corte.get('pit') if isinstance(corte, dict) else None)
                        material = getattr(corte, 'material', None) or (corte.get('material') if isinstance(corte, dict) else None) or ''
                        peso_val = getattr(corte, 'peso', None) or (corte.get('peso') if isinstance(corte, dict) else None)
                        puerto = getattr(corte, 'puerto_id', None) or (corte.get('puerto_id') if isinstance(corte, dict) else None) or puerto_id
                        fecha_hora = getattr(corte, 'fecha_hora', None) or (corte.get('fecha_hora') if isinstance(corte, dict) else None) or datetime.now()
                        usuario_id = getattr(corte, 'usuario_id', None) or (corte.get('usuario_id') if isinstance(corte, dict) else None) or 0

                        # Mantener 'consecutivo' del acumulado (viaje)
                        viaje_consec = None
                        if trans is not None and int(trans) in acum_map:
                            viaje_consec = int(getattr(acum_map[int(trans)], 'consecutivo', 0) or 0)
                            usuario = getattr(acum_map[int(trans)], 'usuario', "") or ""
                        else:
                            viaje_consec = 0
                            usuario = ""

                        try:
                            peso = Decimal(peso_val) if peso_val is not None else Decimal('0')
                        except Exception:
                            peso = Decimal('0')

                        resp = VPesadasAcumResponse(
                            referencia=ref,
                            consecutivo=int(viaje_consec),
                            transaccion=int(trans) if trans is not None else 0,
                            pit=int(pit) if pit is not None else 0,
                            material=material,
                            peso=peso,
                            puerto_id=puerto,
                            fecha_hora=fecha_hora,
                            usuario_id=int(usuario_id),
                            usuario=usuario,
                        )
                        response.append(resp)
                    except Exception as e_map:
                        log.error(f"Error mapeando pesadas_corte a VPesadasAcumResponse: {e_map} - corte: {corte}", exc_info=True)

                log.info(f"Se han procesado {len(response)} pesadas cortes a partir de registros en pesadas_corte.")
                return response

            # Si no se generaron registros en pesadas_corte, construir desde acumulado y generar una ref por transaccion
            for acum in acumulado:
                try:
                    transaccion = int(getattr(acum, 'transaccion', 0) or 0)
                    viaje_consec = int(getattr(acum, 'consecutivo', 0) or 0)
                    pit = int(getattr(acum, 'pit', 0) or 0)
                    material = getattr(acum, 'material', '') or ''
                    peso_val = getattr(acum, 'peso', None)
                    try:
                        peso = Decimal(peso_val) if peso_val is not None else Decimal('0')
                    except Exception:
                        peso = Decimal('0')
                    puerto = getattr(acum, 'puerto_id', None) or puerto_id
                    fecha_hora = getattr(acum, 'fecha_hora', None) or datetime.now()
                    usuario_id = int(getattr(acum, 'usuario_id', 0) or 0)

                    # generar referencia por transacción (serie 1,2,3...) usando gen_pesada_identificador
                    try:
                        gen_req = PesadaCorteRetrieve(puerto_id=puerto, transaccion=transaccion)
                        ref_gen = await self.gen_pesada_identificador(gen_req)
                    except Exception as e_ref:
                        log.error(f"No fue posible generar referencia para transaccion {transaccion}: {e_ref}", exc_info=True)
                        ref_gen = None

                    resp = VPesadasAcumResponse(
                        referencia=ref_gen,
                        consecutivo=viaje_consec,
                        transaccion=transaccion,
                        pit=pit,
                        material=material,
                        peso=peso,
                        puerto_id=puerto,
                        fecha_hora=fecha_hora,
                        usuario_id=usuario_id,
                        usuario=getattr(acum, 'usuario', "") or "",
                    )
                    response.append(resp)
                except Exception as e_map:
                    log.error(f"Error mapeando acumulado a VPesadasAcumResponse (fallback): {e_map} - acum: {acum}", exc_info=True)

            log.info(f"Se han procesado {len(response)} pesadas cortes de un total de {len(acumulado)} registros acumulados (fallback desde acumulado).")
            return response

        except EntityNotFoundException:
            raise
        except Exception as e:
            log.error(f"Error al obtener suma de pesadas para puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al obtener la suma de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_envio_final(self, puerto_id: Optional[str] = None) -> List[VPesadasAcumResponse]:
        """
        Retorna el último registro de `pesadas_corte` para el `puerto_id` indicado.
        """
        try:
            from sqlalchemy import select
            query = select(self._repo_corte.model).where(self._repo_corte.model.puerto_id == puerto_id).order_by(self._repo_corte.model.fecha_hora.desc()).limit(1)
            result = await self._repo_corte.db.execute(query)
            last_corte = result.scalars().first()

            if not last_corte:
                raise EntityNotFoundException("No hay pesadas nuevas por reportar. no encontrada.")

            # Extraer atributos del ORM usando getattr
            ref = getattr(last_corte, 'ref', None)
            corte_id = getattr(last_corte, 'id', None)
            transaccion = getattr(last_corte, 'transaccion', None) or 0
            pit = getattr(last_corte, 'pit', None) or 0
            material = getattr(last_corte, 'material', None) or ""
            peso = getattr(last_corte, 'peso', None)
            puerto = getattr(last_corte, 'puerto_id', None) or puerto_id
            fecha_hora = getattr(last_corte, 'fecha_hora', None)
            usuario_id = getattr(last_corte, 'usuario_id', None) or 0

            # Ensure types compatible with VPesadasAcumResponse
            from decimal import Decimal
            if peso is None:
                peso = Decimal('0')
            else:
                try:
                    peso = Decimal(peso)
                except Exception:
                    peso = Decimal('0')

            if fecha_hora is None:
                from datetime import datetime
                fecha_hora = datetime.now()

            referencia = f"{ref}F" if ref else (f"{corte_id}F" if corte_id is not None else None)

            # Obtener viaje_id desde la transacción relacionada para que 'consecutivo' represente viaje_id
            viaje_id = 0
            try:
                if transaccion:
                    from sqlalchemy import select
                    q = select(Transacciones).where(Transacciones.id == int(transaccion))
                    r = await self._repo_corte.db.execute(q)
                    tran_rec = r.scalars().first()
                    if tran_rec and getattr(tran_rec, 'viaje_id', None) is not None:
                        viaje_id = int(getattr(tran_rec, 'viaje_id'))
            except Exception:
                viaje_id = 0

            # Para el envío final la transacción queda como 00000 para indicar que es la última
            resp_data = {
                'referencia': referencia,
                'consecutivo': int(viaje_id),
                'transaccion': 00000,
                'pit': int(pit),
                'material': material,
                'peso': peso,
                'puerto_id': puerto,
                'fecha_hora': fecha_hora,
                'usuario_id': int(usuario_id),
                'usuario': "",
            }

            response_item = VPesadasAcumResponse(**resp_data)
            return [response_item]

        except EntityNotFoundException:
            raise
        except Exception as e:
            log.error(f"Error al obtener envio final para puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al obtener envio final.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_pesadas_corte(self, acum_data: List[PesadasCalculate]) -> List[PesadasCorteCreate]:
        """
        Crea registros en pesadas_corte a partir de datos acumulados, manejando referencias y errores de forma robusta.

        Flujo:
        1. Para cada registro en acum_data, intenta crear un nuevo registro en pesadas_corte.
        2. Si la creación es exitosa, genera una referencia única y actualiza el registro.
        3. Si la creación falla por clave duplicada, intenta recuperar el registro existente.
        4. Devuelve la lista de registros creados o recuperados.

        Args:
            acum_data (List[PesadasCalculate]): Lista de datos acumulados para crear registros en pesadas_corte.

        Returns:
            List[PesadasCorteCreate]: Lista de registros creados o recuperados en pesadas_corte.

        Raises:
            BasedException: Para errores inesperados durante el proceso de creación.
        """
        try:
            if not acum_data:
                raise ValueError("No hay datos acumulados para procesar.")

            registros_creados = []

            for data in acum_data:
                try:
                    # Calcular siguiente consecutivo para la transacción
                    tran = getattr(data, 'transaccion', None)
                    next_consec = 1
                    if tran is not None:
                        try:
                            existing_count = await self._repo_corte.count_by_transaccion(int(tran))
                            next_consec = int(existing_count) + 1
                        except Exception:
                            next_consec = 1

                    puerto_prefix = (data.puerto_id.split('-')[0] if getattr(data, 'puerto_id', None) else 'REF')
                    # generar token determinístico por transacción para mantener la parte intermedia constante
                    if tran is not None:
                        try:
                            token_mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(int(tran)))).replace('-', '')[:8].upper()
                        except Exception:
                            token_mid = str(uuid.uuid4())[:8].upper()
                    else:
                        token_mid = str(uuid.uuid4())[:8].upper()
                    referencia_unica = f"{puerto_prefix}-{token_mid}-{next_consec}"

                    # 1. Intentar crear un nuevo registro en pesadas_corte con ref calculado y usar viaje_id como 'consecutivo'
                    viaje_id_val = getattr(data, 'consecutivo', None)
                    nuevo_registro = PesadasCorteCreate(
                        **data.model_dump(exclude={'primera', 'ultima', 'referencia'}),
                        ref=referencia_unica,
                        consecutivo=int(viaje_id_val) if viaje_id_val is not None else None,
                        enviado=True,
                    )
                    creado = await self._repo_corte.create(nuevo_registro)

                    registros_creados.append(creado)
                    log.info(f"Registro creado y referencia asignada: {referencia_unica}")
                except Exception as e:
                    log.error(f"Error al crear registro en pesadas_corte: {e}", exc_info=True)
                    # 3. Intentar recuperar el registro existente en caso de error
                    try:
                        existentes = await self._repo_corte.find_many(puerto_id=data.puerto_id, transaccion=data.transaccion)
                        if existentes:
                            registros_creados.extend(existentes)
                            log.info(f"Registros recuperados existentes: {len(existentes)}")
                    except Exception as ex_recuperar:
                        log.error(f"Error al recuperar registros existentes: {ex_recuperar}", exc_info=True)

            return registros_creados

        except ValueError as e:
            log.error(f"Error de validación: {e}")
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error inesperado en create_pesadas_corte: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al crear registros en pesadas_corte.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pesada_acumulada(self, puerto_id: Optional[str] = None,
                                   tran_id: Optional[int] = None) -> VPesadasAcumResponse:
        """
        Retrieve the sum of pesadas related to a puerto_id.

        Args:
            puerto_id (str): The optional ID of the puerto to filter pesadas by.
            tran_id (int): The optional ID of the transaction to filter pesadas by.

        Returns:
            VPesadasAcumResponse: An object containing the accumulated pesada data.

        Raises:
            EntityNotFoundException: If no pesadas are found for the given puerto_id.
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_sumatoria_pesada(puerto_id, tran_id)
        except EntityNotFoundException as e:
            raise e
        except DatabaseSQLAlchemyException:
            raise
        except Exception as e:
            log.error(f"Error al obtener suma de pesadas para puerto_id {puerto_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la suma de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )