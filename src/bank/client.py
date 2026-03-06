from decimal import Decimal

import httpx

from src.bank.config import bank_settings
from src.bank.exceptions import BankAPIError, BankConnectionError, BankPaymentNotFoundError
from src.bank.schemas import AcquiringCheckResponse, AcquiringStartResponse


class BankClient:
    def __init__(self) -> None:
        self._base_url = bank_settings.BANK_API_URL
        self._timeout = bank_settings.BANK_REQUEST_TIMEOUT

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        )

    async def acquiring_start(self, order_id: int, amount: Decimal) -> AcquiringStartResponse:
        """Инициировать платёж через банковский эквайринг."""
        try:
            async with self._get_client() as client:
                response = await client.post(
                    "/acquiring_start",
                    json={"order_id": order_id, "amount": str(amount)},
                )
        except httpx.ConnectError as e:
            raise BankConnectionError() from e
        except httpx.TimeoutException as e:
            raise BankConnectionError() from e

        if response.status_code != 200:
            data = getattr(response, "json", lambda: {})()
            raise BankAPIError(detail=data.get("error", "Unknown bank error"))
        return AcquiringStartResponse(**response.json())

    async def acquiring_check(self, bank_payment_id: str) -> AcquiringCheckResponse:
        """Проверить статус платежа в банке."""
        try:
            async with self._get_client() as client:
                response = await client.get(
                    "/acquiring_check",
                    params={"bank_payment_id": bank_payment_id},
                )
        except httpx.ConnectError as e:
            raise BankConnectionError() from e
        except httpx.TimeoutException as e:
            raise BankConnectionError() from e

        if response.status_code == 404:
            raise BankPaymentNotFoundError()

        if response.status_code != 200:
            data = getattr(response, "json", lambda: {})()
            raise BankAPIError(detail=data.get("error", "Unknown bank error"))
        return AcquiringCheckResponse(**response.json())


bank_client = BankClient()
