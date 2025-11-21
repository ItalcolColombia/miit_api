from decimal import Decimal
from typing import Optional, Any, List
from pydantic import  ConfigDict
from schemas.base_schema import BaseSchema


class NotificationCargue(BaseSchema):
    truckPlate: Optional[str] = None
    truckTransaction: Optional[str] = None
    weighingPitId: Optional[int] = None
    weight: Optional[Decimal] = None


    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "truckPlate": "SVX789",
                "truckTransaction": "CamionPrueba1",
                "weighingPitId": 2,
                "weight": 18742,
            }
        }
    )

class NotificationBuque(BaseSchema):
    voyage: Optional[str]
    status: Optional[str]
    data: Optional[List[Any]] = None,


    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "voyage": "VOY2024049",
                "status": "Finished",
            }
        }
    )

class NotificationPitCargue(BaseSchema):
    cargoPit: Optional[int] = None

    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "cargoPit": 2,
            }
        }
    )

class NotificationBlsPeso(BaseSchema):
    noBL: Optional[str] = None
    voyage: Optional[str] = None
    weightBl: Optional[Decimal] = None

    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "noBL": 'SSPRUEBA001',
                "voyage": "VOY2024049",
                "weightBl": Decimal('125498'),
            }
        }
    )

class NotificationEnvioFinal(BaseSchema):
    voyage: Optional[str] = None
    referencia: Optional[str] = None
    consecutivo: Optional[int] = None
    transaccion: Optional[int] = None
    pit: Optional[int] = None
    material: Optional[str] = None
    peso: Optional[str] = None
    puerto_id: Optional[str] = None
    fecha_hora: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario: Optional[str] = None

    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "voyage": "NBK1-0005",
                "referencia": "NBK1-0AC793EF-3F",
                "consecutivo": 25096,
                "transaccion": 1,
                "pit": 3,
                "material": "CR",
                "peso": "109180.00",
                "puerto_id": "NBK1-0005",
                "fecha_hora": "2025-11-20T21:12:07.989Z",
                "usuario_id": 1,
                "usuario": ""
            }
        }
    )
