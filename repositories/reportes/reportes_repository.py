from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import text, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Reporte, ReporteColumna, PermisoReporte


class ReportesRepository:
    """
    Repositorio para acceso a datos de reportes.
    Maneja todas las operaciones de base de datos relacionadas con reportes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================
    # CATÁLOGO DE REPORTES
    # ========================================================

    async def get_all_reportes(self, solo_activos: bool = True) -> List[Reporte]:
        """
        Obtiene todos los reportes del catálogo.

        Args:
            solo_activos: Si True, solo retorna reportes activos

        Returns:
            Lista de reportes ordenados por 'orden'
        """
        query = select(Reporte)

        if solo_activos:
            query = query.where(Reporte.activo == True)

        query = query.order_by(Reporte.orden)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_reporte_by_codigo(self, codigo: str) -> Optional[Reporte]:
        """
        Obtiene un reporte por su código único.

        Args:
            codigo: Código del reporte (ej: 'RPT_BASCULA')

        Returns:
            Reporte o None si no existe
        """
        query = select(Reporte).where(Reporte.codigo == codigo)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_reporte_by_id(self, reporte_id: int) -> Optional[Reporte]:
        """
        Obtiene un reporte por su ID.

        Args:
            reporte_id: ID del reporte

        Returns:
            Reporte o None si no existe
        """
        query = select(Reporte).where(Reporte.id == reporte_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_reportes_con_permisos(self, rol_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los reportes con información de permisos para un rol.

        Args:
            rol_id: ID del rol

        Returns:
            Lista de reportes con campos puede_ver y puede_exportar
        """
        query = text("""
                     SELECT *
                     FROM fn_obtener_reportes_por_rol(:rol_id)
                     """)

        result = await self.db.execute(query, {"rol_id": rol_id})
        rows = result.fetchall()

        # Conversión automática - evita errores de campos faltantes
        return [dict(row._mapping) for row in rows]

    # ========================================================
    # COLUMNAS DE REPORTES
    # ========================================================

    async def get_columnas_reporte(
            self,
            codigo_reporte: str,
            solo_visibles: bool = True
    ) -> List[ReporteColumna]:
        """
        Obtiene las columnas de un reporte.

        Args:
            codigo_reporte: Código del reporte
            solo_visibles: Si True, solo retorna columnas visibles

        Returns:
            Lista de columnas ordenadas
        """
        query = text("""
                     SELECT *
                     FROM fn_obtener_columnas_reporte(:codigo)
                     """)

        result = await self.db.execute(query, {"codigo": codigo_reporte})
        rows = result.fetchall()

        columnas = []
        for row in rows:
            columnas.append({
                "campo": row.campo,
                "nombre_mostrar": row.nombre_mostrar,
                "tipo_dato": row.tipo_dato,
                "orden": row.orden,
                "visible": row.visible,
                "ordenable": row.ordenable,
                "filtrable": row.filtrable,
                "es_totalizable": row.es_totalizable,
                "tipo_totalizacion": row.tipo_totalizacion,
                "alineacion": row.alineacion,
                "formato": row.formato,
                "prefijo": row.prefijo,
                "sufijo": row.sufijo,
                "decimales": row.decimales,
                "ancho_minimo": row.ancho_minimo
            })

        return columnas

    async def get_columnas_totalizables(self, codigo_reporte: str) -> List[Dict[str, Any]]:
        """
        Obtiene solo las columnas que son totalizables.

        Args:
            codigo_reporte: Código del reporte

        Returns:
            Lista de columnas totalizables con su tipo de totalización
        """
        query = text("""
                     SELECT rc.campo,
                            rc.tipo_totalizacion
                     FROM reportes_columnas rc
                              INNER JOIN reportes r ON rc.reporte_id = r.id
                     WHERE r.codigo = :codigo
                       AND rc.es_totalizable = true
                     ORDER BY rc.orden
                     """)

        result = await self.db.execute(query, {"codigo": codigo_reporte})
        return [{"campo": row.campo, "tipo": row.tipo_totalizacion} for row in result.fetchall()]

    # ========================================================
    # DATOS DE REPORTES (VISTAS MATERIALIZADAS)
    # ========================================================

    async def get_reporte_data(
            self,
            vista_nombre: str,
            campo_fecha: str,
            filtros: Dict[str, Any],
            page: int = 1,
            page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Consulta datos de una vista materializada con filtros y paginación.

        Args:
            vista_nombre: Nombre de la vista materializada
            campo_fecha: Nombre del campo de fecha para filtros
            filtros: Diccionario con filtros a aplicar
            page: Número de página
            page_size: Registros por página

        Returns:
            Tupla con (datos, total_registros)
        """
        # Construir consulta base
        where_clauses = []
        params = {}

        # Filtro por material
        if filtros.get('material_id'):
            # Obtener código del material
            codigo_material = await self._get_material_codigo(filtros['material_id'])
            if codigo_material:
                where_clauses.append("codigo_material = :codigo_material")
                params['codigo_material'] = codigo_material

        # Filtro por fecha inicio - usar CAST para compatibilidad con asyncpg
        if filtros.get('fecha_inicio'):
            where_clauses.append(f"{campo_fecha} >= CAST(:fecha_inicio AS timestamp)")
            params['fecha_inicio'] = filtros['fecha_inicio']

        # Filtro por fecha fin - usar CAST para compatibilidad con asyncpg
        if filtros.get('fecha_fin'):
            where_clauses.append(f"{campo_fecha} <= CAST(:fecha_fin AS timestamp)")
            params['fecha_fin'] = filtros['fecha_fin']

        # Filtros dinámicos de columna
        filtros_columna = filtros.get('filtros_columna', {})
        for campo, valor in filtros_columna.items():
            if valor:
                # Determinar tipo de filtro basado en configuración
                from core.config.filtros_reportes_config import get_filtros_reporte
                filtros_config = get_filtros_reporte(filtros.get('codigo_reporte', ''))
                filtro_info = next((f for f in filtros_config if f.campo == campo), None)

                if filtro_info and filtro_info.tipo_filtro == "search":
                    # Búsqueda parcial case-insensitive (ILIKE)
                    where_clauses.append(f"{campo} ILIKE :filtro_{campo}")
                    params[f'filtro_{campo}'] = f"%{valor}%"
                else:
                    # Coincidencia exacta para filtros tipo select
                    where_clauses.append(f"{campo} = :filtro_{campo}")
                    params[f'filtro_{campo}'] = valor

        # Construir WHERE
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Ordenamiento
        orden_sql = ""
        if filtros.get('orden_campo'):
            direccion = filtros.get('orden_direccion', 'DESC').upper()
            if direccion not in ('ASC', 'DESC'):
                direccion = 'DESC'
            orden_sql = f"ORDER BY {filtros['orden_campo']} {direccion}"
        else:
            orden_sql = f"ORDER BY {campo_fecha} DESC"

        # Contar total - optimización para tablas grandes
        # Si no hay filtros, usar estimación rápida de PostgreSQL
        if not where_clauses:
            # Usar estimación de pg_class para conteos rápidos en tablas grandes
            estimate_query = text("""
                SELECT reltuples::bigint AS estimate
                FROM pg_class
                WHERE relname = :vista_nombre
            """)
            try:
                estimate_result = await self.db.execute(
                    estimate_query,
                    {"vista_nombre": vista_nombre}
                )
                row = estimate_result.fetchone()
                if row and row.estimate > 0:
                    total_registros = int(row.estimate)
                else:
                    # Fallback a count real si la estimación falla
                    count_query = text(f"SELECT COUNT(*) as total FROM {vista_nombre}")
                    count_result = await self.db.execute(count_query, params)
                    total_registros = count_result.scalar() or 0
            except Exception:
                # Fallback a count real
                count_query = text(f"SELECT COUNT(*) as total FROM {vista_nombre}")
                count_result = await self.db.execute(count_query, params)
                total_registros = count_result.scalar() or 0
        else:
            # Con filtros, necesitamos count exacto
            count_query = text(f"""
                SELECT COUNT(*) as total 
                FROM {vista_nombre} 
                {where_sql}
            """)
            count_result = await self.db.execute(count_query, params)
            total_registros = count_result.scalar() or 0

        # Consulta con paginación
        offset = (page - 1) * page_size
        params['limit'] = page_size
        params['offset'] = offset

        data_query = text(f"""
            SELECT * 
            FROM {vista_nombre} 
            {where_sql}
            {orden_sql}
            LIMIT :limit OFFSET :offset
        """)

        result = await self.db.execute(data_query, params)
        datos = [dict(row._mapping) for row in result.fetchall()]

        return datos, total_registros

    async def get_totales_reporte(
            self,
            vista_nombre: str,
            campo_fecha: str,
            columnas_totalizables: List[Dict[str, Any]],
            filtros: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcula totales para las columnas totalizables.

        Args:
            vista_nombre: Nombre de la vista
            campo_fecha: Campo de fecha para filtros
            columnas_totalizables: Lista de columnas con su tipo de totalización
            filtros: Filtros a aplicar

        Returns:
            Diccionario con totales por campo
        """
        if not columnas_totalizables:
            return {}

        # Construir SELECT con agregaciones
        select_parts = []
        for col in columnas_totalizables:
            campo = col['campo']
            tipo = col.get('tipo', 'sum').upper()

            if tipo == 'SUM':
                select_parts.append(f"SUM({campo}) as {campo}")
            elif tipo == 'AVG':
                select_parts.append(f"AVG({campo}) as {campo}")
            elif tipo == 'COUNT':
                select_parts.append(f"COUNT({campo}) as {campo}")
            elif tipo == 'MIN':
                select_parts.append(f"MIN({campo}) as {campo}")
            elif tipo == 'MAX':
                select_parts.append(f"MAX({campo}) as {campo}")
            else:
                select_parts.append(f"SUM({campo}) as {campo}")

        select_sql = ", ".join(select_parts)

        # Construir WHERE
        where_clauses = []
        params = {}

        if filtros.get('material_id'):
            codigo_material = await self._get_material_codigo(filtros['material_id'])
            if codigo_material:
                where_clauses.append("codigo_material = :codigo_material")
                params['codigo_material'] = codigo_material

        if filtros.get('fecha_inicio'):
            where_clauses.append(f"{campo_fecha} >= CAST(:fecha_inicio AS timestamp)")
            params['fecha_inicio'] = filtros['fecha_inicio']

        if filtros.get('fecha_fin'):
            where_clauses.append(f"{campo_fecha} <= CAST(:fecha_fin AS timestamp)")
            params['fecha_fin'] = filtros['fecha_fin']

        # Filtros dinámicos de columna
        filtros_columna = filtros.get('filtros_columna', {})
        for campo, valor in filtros_columna.items():
            if valor:
                from core.config.filtros_reportes_config import get_filtros_reporte
                filtros_config = get_filtros_reporte(filtros.get('codigo_reporte', ''))
                filtro_info = next((f for f in filtros_config if f.campo == campo), None)

                if filtro_info and filtro_info.tipo_filtro == "search":
                    where_clauses.append(f"{campo} ILIKE :filtro_{campo}")
                    params[f'filtro_{campo}'] = f"%{valor}%"
                else:
                    where_clauses.append(f"{campo} = :filtro_{campo}")
                    params[f'filtro_{campo}'] = valor

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = text(f"""
            SELECT {select_sql}
            FROM {vista_nombre}
            {where_sql}
        """)

        result = await self.db.execute(query, params)
        row = result.fetchone()

        if row:
            return dict(row._mapping)
        return {}

    # ========================================================
    # PERMISOS
    # ========================================================

    async def get_permisos_rol(self, rol_id: int) -> List[PermisoReporte]:
        """
        Obtiene todos los permisos de reportes para un rol.

        Args:
            rol_id: ID del rol

        Returns:
            Lista de permisos
        """
        query = select(PermisoReporte).where(PermisoReporte.rol_id == rol_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def verificar_acceso(
            self,
            rol_id: int,
            codigo_reporte: str,
            requiere_exportacion: bool = False
    ) -> bool:
        """
        Verifica si un rol tiene acceso a un reporte.

        Args:
            rol_id: ID del rol
            codigo_reporte: Código del reporte
            requiere_exportacion: Si True, también verifica permiso de exportación

        Returns:
            True si tiene acceso
        """
        conditions = [
            PermisoReporte.rol_id == rol_id,
            PermisoReporte.codigo_reporte == codigo_reporte,
            PermisoReporte.puede_ver == True
        ]

        if requiere_exportacion:
            conditions.append(PermisoReporte.puede_exportar == True)

        query = select(PermisoReporte).where(and_(*conditions))
        result = await self.db.execute(query)

        return result.scalar_one_or_none() is not None

    async def asignar_permiso(
            self,
            rol_id: int,
            codigo_reporte: str,
            puede_ver: bool,
            puede_exportar: bool,
            usuario_id: Optional[int] = None
    ) -> PermisoReporte:
        """
        Crea o actualiza un permiso de reporte para un rol.

        Args:
            rol_id: ID del rol
            codigo_reporte: Código del reporte
            puede_ver: Permiso de visualización
            puede_exportar: Permiso de exportación
            usuario_id: ID del usuario que realiza el cambio

        Returns:
            Permiso creado/actualizado
        """
        # Buscar permiso existente
        query = select(PermisoReporte).where(
            and_(
                PermisoReporte.rol_id == rol_id,
                PermisoReporte.codigo_reporte == codigo_reporte
            )
        )
        result = await self.db.execute(query)
        permiso = result.scalar_one_or_none()

        if permiso:
            # Actualizar
            permiso.puede_ver = puede_ver
            permiso.puede_exportar = puede_exportar
            permiso.usuario_id = usuario_id
            permiso.fecha_hora = datetime.now()
        else:
            # Crear nuevo
            # Obtener reporte_id
            reporte = await self.get_reporte_by_codigo(codigo_reporte)
            reporte_id = reporte.id if reporte else None

            permiso = PermisoReporte(
                rol_id=rol_id,
                codigo_reporte=codigo_reporte,
                reporte_id=reporte_id,
                puede_ver=puede_ver,
                puede_exportar=puede_exportar,
                usuario_id=usuario_id
            )
            self.db.add(permiso)

        await self.db.commit()
        await self.db.refresh(permiso)
        return permiso

    async def eliminar_permiso(self, rol_id: int, codigo_reporte: str) -> bool:
        """
        Elimina un permiso de reporte.

        Args:
            rol_id: ID del rol
            codigo_reporte: Código del reporte

        Returns:
            True si se eliminó
        """
        query = select(PermisoReporte).where(
            and_(
                PermisoReporte.rol_id == rol_id,
                PermisoReporte.codigo_reporte == codigo_reporte
            )
        )
        result = await self.db.execute(query)
        permiso = result.scalar_one_or_none()

        if permiso:
            await self.db.delete(permiso)
            await self.db.commit()
            return True
        return False

    # ========================================================
    # MÉTODOS AUXILIARES
    # ========================================================

    async def _get_material_codigo(self, material_id: int) -> Optional[str]:
        """
        Obtiene el código de un material por su ID.

        Args:
            material_id: ID del material

        Returns:
            Código del material o None
        """
        query = text("SELECT codigo FROM materiales WHERE id = :material_id")
        result = await self.db.execute(query, {"material_id": material_id})
        row = result.fetchone()
        return row.codigo if row else None

    async def get_materiales_filtro(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de materiales para filtros.

        Returns:
            Lista de materiales con id, nombre y codigo
        """
        # Nota: Se eliminó el filtro WHERE estado = true porque la columna no existe
        # Si en el futuro se agrega una columna de estado, se puede volver a filtrar
        query = text("""
                     SELECT id, nombre, codigo
                     FROM materiales
                     ORDER BY nombre
                     """)
        result = await self.db.execute(query)
        return [
            {"id": row.id, "nombre": row.nombre, "codigo": row.codigo}
            for row in result.fetchall()
        ]

    async def get_rango_fechas_vista(
            self,
            vista_nombre: str,
            campo_fecha: str
    ) -> Dict[str, Any]:
        """
        Obtiene el rango de fechas disponible en una vista.

        Args:
            vista_nombre: Nombre de la vista
            campo_fecha: Campo de fecha

        Returns:
            Diccionario con fecha_minima y fecha_maxima
        """
        query = text(f"""
            SELECT 
                MIN({campo_fecha}) as fecha_minima,
                MAX({campo_fecha}) as fecha_maxima
            FROM {vista_nombre}
        """)
        result = await self.db.execute(query)
        row = result.fetchone()

        if row:
            return {
                "fecha_minima": row.fecha_minima,
                "fecha_maxima": row.fecha_maxima
            }
        return {"fecha_minima": None, "fecha_maxima": None}

    async def refresh_vista(self, vista_nombre: str) -> None:
        """
        Refresca una vista materializada.

        Args:
            vista_nombre: Nombre de la vista
        """
        query = text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {vista_nombre}")
        await self.db.execute(query)
        await self.db.commit()

    async def refresh_todas_vistas(self) -> None:
        """
        Refresca todas las vistas de reportes.
        """
        query = text("SELECT refresh_all_report_views()")
        await self.db.execute(query)
        await self.db.commit()

    # ========================================================
    # FILTROS DINÁMICOS
    # ========================================================

    async def get_valores_unicos_columna(
            self,
            vista_nombre: str,
            campo: str,
            limite: int = 1000
    ) -> List[Dict[str, str]]:
        """
        Obtiene los valores únicos de una columna para usar como opciones de filtro.

        Args:
            vista_nombre: Nombre de la vista materializada
            campo: Nombre del campo/columna
            limite: Límite máximo de valores a retornar

        Returns:
            Lista de diccionarios con {valor, etiqueta}
        """
        # Usar SQL parametrizado seguro (campo viene de configuración, no del usuario)
        query = text(f"""
            SELECT DISTINCT {campo} as valor
            FROM {vista_nombre}
            WHERE {campo} IS NOT NULL
            ORDER BY {campo}
            LIMIT :limite
        """)

        result = await self.db.execute(query, {"limite": limite})
        rows = result.fetchall()

        return [
            {"valor": str(row.valor), "etiqueta": str(row.valor)}
            for row in rows
        ]
