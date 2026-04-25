"""Top-level glue — imports from each module so the import graph is realistic."""

from billing.invoices import format_invoice
from notifications.email import send_welcome
from analytics.metrics import total_revenue
from core.types import User, Order


def demo():
    u = User(id=1, name="Ada", email="ada@example.com")
    o = Order(id=42, user_id=1, total_cents=1999)
    print(format_invoice(o))
    print(send_welcome(u))
    print(total_revenue([o]))
