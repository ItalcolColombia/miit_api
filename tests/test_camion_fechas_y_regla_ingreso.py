import unittest
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from api.v1.endpoints.operador import in_camion, out_camion
from services.viajes_service import ViajesService


class TestCamionFechasYReglaIngreso(unittest.IsolatedAsyncioTestCase):
    async def test_in_camion_usa_fecha_ingreso_del_parametro(self):
        fecha_ingreso = datetime(2026, 4, 30, 10, 15, 0)
        service = SimpleNamespace(
            chg_camion_ingreso=AsyncMock(return_value={"cargoPit": 1}),
            chg_estado_flota=AsyncMock(return_value=None),
        )

        await in_camion(
            puerto_id="TRK-001",
            peso_vacio=Decimal("12000"),
            peso_maximo=Decimal("30000"),
            fecha_ingreso=fecha_ingreso,
            service=service,
        )

        service.chg_camion_ingreso.assert_awaited_once()
        args, _ = service.chg_camion_ingreso.await_args
        self.assertEqual(args[1], fecha_ingreso)

    async def test_out_camion_usa_fecha_salida_del_parametro(self):
        fecha_salida = datetime(2026, 4, 30, 11, 45, 0)
        service = SimpleNamespace(
            chg_camion_salida=AsyncMock(return_value=None),
            chg_estado_flota=AsyncMock(return_value=None),
        )

        await out_camion(
            puerto_id="TRK-001",
            peso_real=Decimal("18500"),
            fecha_salida=fecha_salida,
            service=service,
        )

        service.chg_camion_salida.assert_awaited_once()
        args, _ = service.chg_camion_salida.await_args
        self.assertEqual(args[1], fecha_salida)

    async def test_chg_camion_ingreso_resetea_fecha_salida_si_peso_real_es_cero(self):
        repo = MagicMock()
        repo.update = AsyncMock(return_value=None)

        flotas_service = MagicMock()
        flotas_service.get_flota = AsyncMock(return_value=SimpleNamespace(tipo="camion"))

        service = ViajesService(
            viajes_repository=repo,
            mat_service=MagicMock(),
            flotas_service=flotas_service,
            feedback_service=MagicMock(),
            transacciones_service=MagicMock(),
            bl_service=MagicMock(),
            client_service=MagicMock(),
        )

        viaje = SimpleNamespace(
            id=10,
            puerto_id="TRK-002",
            flota_id=77,
            viaje_origen=None,
            peso_real=Decimal("0"),
        )
        service.get_viaje_by_puerto_id = AsyncMock(return_value=viaje)

        fecha = datetime(2026, 4, 30, 12, 0, 0)
        await service.chg_camion_ingreso(
            puerto_id="TRK-002",
            fecha=fecha,
            peso_vacio=Decimal("10000"),
            peso_maximo=Decimal("26000"),
        )

        repo.update.assert_awaited_once()
        _, kwargs = repo.update.await_args
        update_data = kwargs.get("update_data")
        if update_data is None:
            args, _ = repo.update.await_args
            update_data = args[1]

        self.assertIn("fecha_salida", update_data.model_fields_set)

    async def test_chg_camion_ingreso_no_resetea_fecha_salida_si_peso_real_es_mayor_a_cero(self):
        repo = MagicMock()
        repo.update = AsyncMock(return_value=None)

        flotas_service = MagicMock()
        flotas_service.get_flota = AsyncMock(return_value=SimpleNamespace(tipo="camion"))

        service = ViajesService(
            viajes_repository=repo,
            mat_service=MagicMock(),
            flotas_service=flotas_service,
            feedback_service=MagicMock(),
            transacciones_service=MagicMock(),
            bl_service=MagicMock(),
            client_service=MagicMock(),
        )

        viaje = SimpleNamespace(
            id=11,
            puerto_id="TRK-003",
            flota_id=78,
            viaje_origen=None,
            peso_real=Decimal("1500"),
        )
        service.get_viaje_by_puerto_id = AsyncMock(return_value=viaje)

        fecha = datetime(2026, 4, 30, 12, 30, 0)
        await service.chg_camion_ingreso(
            puerto_id="TRK-003",
            fecha=fecha,
            peso_vacio=Decimal("10000"),
            peso_maximo=Decimal("26000"),
        )

        repo.update.assert_awaited_once()
        _, kwargs = repo.update.await_args
        update_data = kwargs.get("update_data")
        if update_data is None:
            args, _ = repo.update.await_args
            update_data = args[1]

        self.assertNotIn("fecha_salida", update_data.model_fields_set)


if __name__ == "__main__":
    unittest.main()

