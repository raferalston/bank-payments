from src.exceptions import NotFoundError


class OrderNotFoundError(NotFoundError):
    def __init__(self):
        super().__init__(detail="Order not found")
