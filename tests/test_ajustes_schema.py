import unittest
from decimal import Decimal

from schemas.ajustes_schema import AjusteCreate


class TestAjusteCreateSchema(unittest.TestCase):
    def test_permite_saldo_nuevo_negativo(self):
        data = AjusteCreate(
            almacenamiento="Silo Horizontal 1",
            saldo_nuevo=Decimal("-10.50"),
            motivo="Ajuste negativo de prueba",
        )
        self.assertEqual(data.saldo_nuevo, Decimal("-10.50"))


if __name__ == "__main__":
    unittest.main()

