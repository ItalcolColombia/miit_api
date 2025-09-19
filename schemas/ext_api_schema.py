from decimal import Decimal
from typing import Optional
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