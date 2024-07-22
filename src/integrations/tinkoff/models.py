import hmac
from uuid import UUID

from pendulum import DateTime
from pydantic import computed_field, Field, field_serializer

from base_objects.models import BasePascalModel
from integrations.tinkoff.utils import hash_string
from settings import Settings


class BasePaymentModel(BasePascalModel):
    token: str | None = None

    @property
    @computed_field
    def terminal_key(self):
        return Settings().env.tinkoff_integration.terminal_key

    def generate_token(self):
        data = self.model_dump(exclude={'token'}, exclude_none=True, by_alias=True)
        token_data = {}
        for key, value in data.items():
            if not isinstance(value, dict | list):
                converted_value = str(value).lower() if isinstance(value, bool) else str(value)
                token_data.update({key: converted_value})

        token_data.update({'Password': Settings().env.tinkoff_integration.password})
        token_data = sorted(token_data.items(), key=lambda x: x[0])
        return hash_string(''.join(str(i[1]) for i in token_data))


class ReceiptItem(BasePascalModel):
    name: str
    price: int
    quantity: int
    amount: int
    tax: str = 'none'


class Receipt(BasePascalModel):
    email: str
    phone: str
    taxation: str = 'usn_income_outcome'
    items: list[ReceiptItem]


class InitPaymentRequest(BasePaymentModel):
    amount: int
    order_id: UUID
    description: str
    token: str | None = None
    redirect_due_date: DateTime | None
    notification_url: str = Field(
        alias='NotificationURL',
        default=Settings().env.public_host.unicode_string() + 'api/callback/notifications/payment-status',
    )
    # customer_key: str
    # success_url: str = Field(alias='SuccessURL')
    # fail_url: str = Field(alias='FailURL')
    data: dict = Field(alias='DATA')
    receipt: Receipt

    @field_serializer('order_id')
    def uuid_serializer(self, value: UUID) -> str:
        return str(value)

    @field_serializer('redirect_due_date')
    def dt_serializer(self, value: DateTime, _info) -> str:
        return value.for_json()


class InitPaymentResponse(BasePascalModel):
    terminal_key: str
    status: str
    payment_id: int
    order_id: UUID
    amount: int
    payment_url: str = Field(alias='PaymentURL')


class PaymentStatusNotification(BasePaymentModel):
    amount: int
    card_id: int
    error_code: str
    exp_date: str
    invoice_id: UUID = Field(alias='OrderId')
    pan: str
    payment_id: int
    status: str
    success: bool

    def verify(self) -> bool:
        return hmac.compare_digest(self.token, self.generate_token())
