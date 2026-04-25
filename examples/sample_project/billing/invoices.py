# REFACTOR: convert format_invoice to use f-strings and add type hints
from core.types import Order


def format_invoice(order):
    return "Invoice #" + str(order.id) + " total=$" + str(order.total_cents / 100)


def discount(order, pct):
    return order.total_cents - (order.total_cents * pct / 100)
