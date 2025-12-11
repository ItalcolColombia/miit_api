from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityAlreadyRegisteredException
from schemas.pesadas_schema import PesadaCreate, PesadaResponse
from services.pesadas_service import PesadasService


@pytest.mark.asyncio
async def test_create_pesada_success_updates_transaccion():
    # Preparar input
    pesada_input = PesadaCreate(transaccion_id=123, consecutivo=1, peso_real=Decimal('100.0'), leido=False)

    # Mock repositories
    mock_repo = Mock()
    mock_repo.find_one = AsyncMock(return_value=None)
    created = PesadaResponse(id=1, transaccion_id=123, consecutivo=1, peso_real=Decimal('100.0'), leido=False)
    mock_repo.create = AsyncMock(return_value=created)

    mock_pesadas_corte_repo = Mock()
    mock_trans_repo = Mock()
    mock_trans_repo.update = AsyncMock(return_value=Mock())

    svc = PesadasService(mock_repo, mock_pesadas_corte_repo, mock_trans_repo)

    result = await svc.create_pesada(pesada_input)

    assert isinstance(result, PesadaResponse)
    mock_repo.find_one.assert_awaited_once()
    mock_repo.create.assert_awaited_once()
    # Verificar que se intentó actualizar la transacción a 'Proceso'
    assert mock_trans_repo.update.await_count == 1
    called_args = mock_trans_repo.update.call_args.args
    assert called_args[0] == 123
    assert hasattr(called_args[1], 'estado') and called_args[1].estado == 'Proceso'


@pytest.mark.asyncio
async def test_create_pesada_missing_transaccion_id_raises_basedexception():
    pesada_input = PesadaCreate(consecutivo=1, peso_real=Decimal('100.0'), leido=False)

    mock_repo = Mock()
    svc = PesadasService(mock_repo, Mock(), Mock())

    with pytest.raises(BasedException):
        await svc.create_pesada(pesada_input)


@pytest.mark.asyncio
async def test_create_pesada_duplicate_raises_entity_already_registered():
    pesada_input = PesadaCreate(transaccion_id=123, consecutivo=1, peso_real=Decimal('100.0'), leido=False)

    mock_repo = Mock()
    # Simular que ya existe una pesada con la misma transacción y consecutivo
    mock_repo.find_one = AsyncMock(return_value=PesadaResponse(id=2, transaccion_id=123, consecutivo=1, peso_real=Decimal('50.0'), leido=False))
    mock_repo.create = AsyncMock()

    svc = PesadasService(mock_repo, Mock(), Mock())

    with pytest.raises(EntityAlreadyRegisteredException):
        await svc.create_pesada(pesada_input)

