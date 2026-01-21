"""
Repositorio para gestión de roles.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional


class RolesRepository:
    """
    Repositorio para acceso a datos de roles.
    Maneja todas las operaciones de base de datos relacionadas con roles.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================
    # OPERACIONES CRUD DE ROLES
    # ========================================================

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los roles con cantidad de usuarios y permisos de reportes.

        Returns:
            Lista de roles con información adicional
        """
        query = text("""
            SELECT
                r.id,
                r.nombre,
                r.estado,
                (SELECT COUNT(*) FROM usuarios u WHERE u.rol_id = r.id) as cantidad_usuarios,
                COALESCE(
                    ARRAY_AGG(pr.codigo_reporte) FILTER (WHERE pr.puede_ver = true),
                    '{}'::varchar[]
                ) as permisos_reportes
            FROM roles r
            LEFT JOIN permisos_reportes pr ON pr.rol_id = r.id
            GROUP BY r.id, r.nombre, r.estado
            ORDER BY r.id
        """)

        result = await self.db.execute(query)
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]

    async def get_rol_by_id(self, rol_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un rol por su ID con información adicional.

        Args:
            rol_id: ID del rol

        Returns:
            Datos del rol o None si no existe
        """
        query = text("""
            SELECT
                r.id,
                r.nombre,
                r.estado,
                (SELECT COUNT(*) FROM usuarios u WHERE u.rol_id = r.id) as cantidad_usuarios,
                COALESCE(
                    ARRAY_AGG(pr.codigo_reporte) FILTER (WHERE pr.puede_ver = true),
                    '{}'::varchar[]
                ) as permisos_reportes
            FROM roles r
            LEFT JOIN permisos_reportes pr ON pr.rol_id = r.id
            WHERE r.id = :rol_id
            GROUP BY r.id, r.nombre, r.estado
        """)

        result = await self.db.execute(query, {"rol_id": rol_id})
        row = result.fetchone()

        if row:
            return dict(row._mapping)
        return None

    async def create_rol(self, nombre: str, estado: bool = True, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Crea un nuevo rol.

        Args:
            nombre: Nombre del rol
            estado: Estado del rol (activo/inactivo)
            usuario_id: ID del usuario que crea el rol

        Returns:
            Datos del rol creado
        """
        query = text("""
            INSERT INTO roles (nombre, estado, usuario_id, fecha_hora)
            VALUES (:nombre, :estado, :usuario_id, NOW())
            RETURNING id, nombre, estado
        """)

        result = await self.db.execute(query, {
            "nombre": nombre,
            "estado": estado,
            "usuario_id": usuario_id
        })
        await self.db.commit()

        row = result.fetchone()
        return {
            "id": row.id,
            "nombre": row.nombre,
            "estado": row.estado,
            "cantidad_usuarios": 0,
            "permisos_reportes": []
        }

    async def update_rol(
            self,
            rol_id: int,
            nombre: Optional[str] = None,
            estado: Optional[bool] = None,
            usuario_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un rol existente.

        Args:
            rol_id: ID del rol a actualizar
            nombre: Nuevo nombre (opcional)
            estado: Nuevo estado (opcional)
            usuario_id: ID del usuario que actualiza

        Returns:
            Datos del rol actualizado o None si no existe
        """
        # Verificar que existe
        rol_existente = await self.get_rol_by_id(rol_id)
        if not rol_existente:
            return None

        # Construir actualización dinámica
        updates = []
        params = {"rol_id": rol_id}

        if nombre is not None:
            updates.append("nombre = :nombre")
            params["nombre"] = nombre

        if estado is not None:
            updates.append("estado = :estado")
            params["estado"] = estado

        if usuario_id is not None:
            updates.append("usuario_id = :usuario_id")
            params["usuario_id"] = usuario_id

        updates.append("fecha_hora = NOW()")

        if not updates:
            return rol_existente

        update_sql = ", ".join(updates)
        query = text(f"""
            UPDATE roles
            SET {update_sql}
            WHERE id = :rol_id
            RETURNING id, nombre, estado
        """)

        result = await self.db.execute(query, params)
        await self.db.commit()

        # Retornar rol actualizado con info adicional
        return await self.get_rol_by_id(rol_id)

    async def delete_rol(self, rol_id: int) -> bool:
        """
        Elimina un rol (solo si no tiene usuarios asociados).

        Args:
            rol_id: ID del rol a eliminar

        Returns:
            True si se eliminó, False si no
        """
        # Verificar que no tiene usuarios
        check_query = text("""
            SELECT COUNT(*) as count FROM usuarios WHERE rol_id = :rol_id
        """)
        result = await self.db.execute(check_query, {"rol_id": rol_id})
        count = result.scalar()

        if count > 0:
            return False

        # Eliminar permisos asociados primero
        await self.db.execute(
            text("DELETE FROM permisos_reportes WHERE rol_id = :rol_id"),
            {"rol_id": rol_id}
        )

        # Eliminar rol
        delete_query = text("DELETE FROM roles WHERE id = :rol_id RETURNING id")
        result = await self.db.execute(delete_query, {"rol_id": rol_id})
        await self.db.commit()

        return result.fetchone() is not None

    # ========================================================
    # PERMISOS DE REPORTES
    # ========================================================

    async def get_permisos_rol(self, rol_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los permisos de reportes de un rol.

        Args:
            rol_id: ID del rol

        Returns:
            Lista de permisos
        """
        query = text("""
            SELECT
                pr.id,
                pr.rol_id,
                pr.codigo_reporte,
                pr.puede_ver,
                pr.puede_exportar,
                pr.fecha_hora
            FROM permisos_reportes pr
            WHERE pr.rol_id = :rol_id
            ORDER BY pr.codigo_reporte
        """)

        result = await self.db.execute(query, {"rol_id": rol_id})
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]

    async def asignar_permisos_rol(
            self,
            rol_id: int,
            permisos: List[Dict[str, Any]],
            usuario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Asigna o actualiza permisos de reportes para un rol.
        Usa estrategia DELETE + INSERT para simplicidad.

        Args:
            rol_id: ID del rol
            permisos: Lista de permisos a asignar
            usuario_id: ID del usuario que realiza la acción

        Returns:
            Resultado de la operación
        """
        # Eliminar permisos existentes
        await self.db.execute(
            text("DELETE FROM permisos_reportes WHERE rol_id = :rol_id"),
            {"rol_id": rol_id}
        )

        # Insertar nuevos permisos
        permisos_insertados = 0
        for permiso in permisos:
            query = text("""
                INSERT INTO permisos_reportes 
                (rol_id, codigo_reporte, puede_ver, puede_exportar, fecha_hora, usuario_id)
                VALUES (:rol_id, :codigo_reporte, :puede_ver, :puede_exportar, NOW(), :usuario_id)
            """)

            await self.db.execute(query, {
                "rol_id": rol_id,
                "codigo_reporte": permiso["codigo_reporte"],
                "puede_ver": permiso.get("puede_ver", False),
                "puede_exportar": permiso.get("puede_exportar", False),
                "usuario_id": usuario_id
            })
            permisos_insertados += 1

        await self.db.commit()

        return {
            "message": "Permisos actualizados correctamente",
            "permisos_actualizados": permisos_insertados
        }

    async def verificar_rol_existe(self, rol_id: int) -> bool:
        """
        Verifica si un rol existe.

        Args:
            rol_id: ID del rol

        Returns:
            True si existe, False si no
        """
        query = text("SELECT id FROM roles WHERE id = :rol_id")
        result = await self.db.execute(query, {"rol_id": rol_id})
        return result.fetchone() is not None
