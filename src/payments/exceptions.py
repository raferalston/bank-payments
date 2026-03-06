from src.exceptions import BadRequestError, NotFoundError


class PaymentNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__(detail="Payment not found")


class PaymentAmountExceededError(BadRequestError):
    def __init__(self):
        super().__init__(detail="Payment amount exceeds remaining order balance")


class PaymentAlreadyRefundedError(BadRequestError):
    def __init__(self):
        super().__init__(detail="Payment is already refunded")


class UnsupportedPaymentTypeError(BadRequestError):
    def __init__(self, payment_type: str):
        super().__init__(detail=f"Unsupported payment type: {payment_type}")


class PaymentNotDepositedError(BadRequestError):
    def __init__(self):
        super().__init__(detail="Only deposited payments can be refunded")


class OrderAlreadyPaidError(BadRequestError):
    def __init__(self):
        super().__init__(detail="Order is already fully paid")
