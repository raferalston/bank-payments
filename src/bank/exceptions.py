from src.exceptions import ExternalServiceError


class BankAPIError(ExternalServiceError):
    def __init__(self, detail: str = "Bank API error"):
        super().__init__(detail=detail)


class BankPaymentNotFoundError(ExternalServiceError):
    def __init__(self):
        super().__init__(detail="Bank payment not found")


class BankConnectionError(ExternalServiceError):
    def __init__(self):
        super().__init__(detail="Failed to connect to bank API")
