import unittest

from core.exceptions.base_exception import BasedException
from services.reportes.reportes_service import ReportesService


class DummyReportesRepo:
    pass


class TestReportesFiltrosOperadores(unittest.TestCase):
    def setUp(self):
        self.service = ReportesService(reportes_repo=DummyReportesRepo())

    def test_normaliza_operador_eq_boolean(self):
        filtros = {
            "filtros_explicitos": {
                "en_puerto": {"eq": "TrUe"}
            }
        }

        normalizados = self.service._normalizar_filtros_dinamicos("RPT_PERMANENCIA", filtros)
        self.assertEqual(len(normalizados["filtros_operadores"]), 1)
        self.assertEqual(normalizados["filtros_operadores"][0]["campo"], "en_puerto")
        self.assertEqual(normalizados["filtros_operadores"][0]["operador"], "eq")
        self.assertIs(normalizados["filtros_operadores"][0]["valor"], True)

    def test_conflicto_en_puerto_con_fecha_salida(self):
        filtros = {
            "filtros_explicitos": {
                "en_puerto": {"eq": "true"},
                "fecha_salida_puerto": {"is_not_null": "true"}
            }
        }

        normalizados = self.service._normalizar_filtros_dinamicos("RPT_PERMANENCIA", filtros)

        with self.assertRaises(BasedException) as context:
            self.service._aplicar_regla_permanencia_activa("RPT_PERMANENCIA", normalizados)

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail["code"], "CONFLICTING_FILTERS")

    def test_aplica_regla_en_puerto_activo(self):
        filtros = {
            "filtros_explicitos": {
                "en_puerto": {"eq": "true"}
            }
        }

        normalizados = self.service._normalizar_filtros_dinamicos("RPT_PERMANENCIA", filtros)
        aplicados = self.service._aplicar_regla_permanencia_activa("RPT_PERMANENCIA", normalizados)

        filtros_operadores = aplicados["filtros_operadores"]
        campos_operadores = {(f["campo"], f["operador"]) for f in filtros_operadores}

        # Una cita activa es cualquiera sin fecha_salida_puerto, sin importar la llegada
        self.assertIn(("fecha_salida_puerto", "is_null"), campos_operadores)
        self.assertNotIn(("fecha_llegada_puerto", "gte"), campos_operadores)
        self.assertNotIn(("fecha_llegada_puerto", "lte"), campos_operadores)


if __name__ == "__main__":
    unittest.main()
