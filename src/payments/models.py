from tortoise import fields
from tortoise.models import Model

from src.payments.constants import PaymentOperationStatus, PaymentType


class Payment(Model):
    id = fields.IntField(primary_key=True)
    order = fields.ForeignKeyField("models.Order", related_name="payments")
    amount = fields.DecimalField(max_digits=12, decimal_places=2)
    payment_type = fields.CharEnumField(PaymentType, max_length=20)
    operation_status = fields.CharEnumField(
        PaymentOperationStatus, default=PaymentOperationStatus.PENDING, max_length=20
    )
    bank_payment_id = fields.CharField(max_length=255, null=True)
    paid_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "payment"

    def __str__(self) -> str:
        return f"Payment #{self.id} — {self.amount} ({self.payment_type}, {self.operation_status})"
