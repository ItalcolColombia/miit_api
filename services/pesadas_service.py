import uuid
from typing import List, Optional
from fastapi_pagination import Page, Params

from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.models import Pesadas
from repositories.pesadas_corte_repository import PesadasCorteRepository
from schemas.pesadas_corte_schema import PesadasCalculate, PesadasCorteCreate, PesadasRange, \
    PesadaCorteRetrieve, PesadaCorteUpdate, PesadasCorteResponse
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate, VPesadasAcumResponse
from repositories.pesadas_repository import PesadasRepository

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

            # STEP 1: Crear cortes inicialmente con un ref temporal (por ejemplo vacío) para obtener IDs
            pesadas_corte_data = [
                PesadasCorteCreate(
                    **item.model_dump(exclude={'primera', 'ultima', 'referencia'}),
                    ref="",  # valor temporal; se actualizará con el id asignado por la DB
                    enviado=True,
                )
                for item in acum_data
            ]

            try:
                # Crear registros y obtener sus IDs
                creada_intermedia = await self._repo_corte.create_bulk(pesadas_corte_data)

                # STEP 2: Para cada creada, generar ref definitivo usando su id y actualizar el registro
                updated_records = []
                for created in creada_intermedia:
                    try:
                        puerto_prefix = (created.puerto_id.split('-')[0] if getattr(created, 'puerto_id', None) else 'REF')
                        new_ref = f"{puerto_prefix}-{str(uuid.uuid4())[:8].upper()}-{getattr(created, 'id')}"
                        # Actualizar usando PesadaCorteUpdate (incluye peso=None para evitar advertencias)
                        upd = PesadaCorteUpdate(ref=new_ref, peso=None)
                        updated = await self._repo_corte.update(int(created.id), upd)
                        updated_records.append(updated)
                    except Exception as ex_upd:
                        log.error(f"Error al actualizar ref para pesada_corte id {getattr(created, 'id')}: {ex_upd}", exc_info=True)
                        # intentar recuperar el registro original si la update falla
                        try:
                            recovered = await self._repo_corte.find_many(puerto_id=created.puerto_id, transaccion=created.transaccion)
                            if recovered:
                                updated_records.extend(recovered)
                        except Exception:
                            pass

                log.info(f"Se registraron y actualizaron {len(updated_records)} pesadas corte para el viaje")
                return updated_records
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

            # 1. Buscar si la pesada ha sido procesada previamente: tomar la última pesada_corte para la transacción
            # usamos get_last_pesada_corte_for_transaccion para evitar excepciones si existen varias filas
            existing_list = await self._repo_corte.find_many(puerto_id=pesada_data.puerto_id, transaccion=pesada_data.transaccion)
            count_existing = len(existing_list) if existing_list else 0

            # 2. Generar ref de forma determinista y segura: <puertoPrefix>-<UUID8>-<count>
            puerto_prefix = pesada_data.puerto_id.split('-')[0] if pesada_data.puerto_id else 'REF'
            pesada_id = f"{puerto_prefix}-{str(uuid.uuid4())[:8].upper()}-{count_existing + 1}"

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

            # 3. Crear registros en pesadas_corte usando la función robusta
            pesadas_corte_records = await self.create_pesadas_corte_if_not_exists(acumulado)
            log.info(f"Se han registrado {len(pesadas_corte_records)} cortes de pesadas.")

            # 4. Marcar las pesadas como leídas solo si existen rangos
            if pesada_range:
                ids_marcados = await self._repo.mark_pesadas(pesada_range)
                log.info(f"{len(ids_marcados)} Pesadas marcadas como leído.")

            # 5. Construir la respuesta a partir de los registros de pesadas_corte
            response: List[VPesadasAcumResponse] = []
            for item in pesadas_corte_records:
                try:
                    # si es un Pydantic model, usamos model_dump
                    data = item.model_dump(exclude={'no_bl'})
                except Exception:
                    # si es dict o similar
                    data = dict(item)

                # asegurar claves esperadas y añadir referencia y usuario
                data['referencia'] = data.get('ref') or data.get('ref', None)
                data['usuario'] = data.get('usuario', "") or ""

                try:
                    response.append(VPesadasAcumResponse(**data))
                except Exception as e:
                    # registrar y omitir registros malformados
                    log.error(f"Error al mapear pesadas_corte a VPesadasAcumResponse: {e} - data: {data}", exc_info=True)

            log.info(f"Se han procesado {len(response)} pesadas cortes de un total de {len(acumulado)} registros acumulados.")
            return response

        except EntityNotFoundException:
            raise
        except Exception as e:
            log.error(f"Error al obtener suma de pesadas para puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al obtener la suma de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pesada_acumulada(self, puerto_id: Optional[str] = None, tran_id: Optional[int] = None) -> VPesadasAcumResponse:
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

    async def get_last_pesada_for_transaccion(self, tran_id: int) -> Optional[PesadasCorteResponse]:
        """
        Obtener la última entrada de `pesadas_corte` para la transacción indicada, ordenada por `fecha_hora`.
        Añade la marca 'F' al `ref` (o lo crea a partir del id si no existe).
        """
        try:
            pesada_corte = await self._repo_corte.get_last_pesada_corte_for_transaccion(tran_id)
            if not pesada_corte:
                return None

            resp = PesadasCorteResponse.model_validate(pesada_corte)
            if getattr(resp, 'ref', None):
                resp.ref = f"{resp.ref}F"
            else:
                resp.ref = f"{resp.id}F" if getattr(resp, 'id', None) is not None else None

            return resp
        except Exception as e:
            log.error(f"Error al obtener la última pesada corte para transacción {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la última pesada.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
