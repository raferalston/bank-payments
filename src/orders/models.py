from tortoise import fields
from tortoise.models import Model

from src.orders.constants import PaymentStatus


class Order(Model):
    id = fields.IntField(primary_key=True)
    amount = fields.DecimalField(max_digits=12, decimal_places=2)
    payment_status = fields.CharEnumField(PaymentStatus, default=PaymentStatus.NOT_PAID, max_length=20)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    payments: fields.ReverseRelation

    class Meta:
        table = "order"

    def __str__(self) -> str:
        return f"Order #{self.id} — {self.amount:.2f} ({self.payment_status})"
