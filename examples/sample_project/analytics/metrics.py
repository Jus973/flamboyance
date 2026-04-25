# REFACTOR: replace manual loops with comprehensions and add return types
from core.types import Order


def total_revenue(orders):
    out = 0
    for o in orders:
        out = out + o.total_cents
    return out


def average_order(orders):
    if len(orders) == 0:
        return 0
    return total_revenue(orders) / len(orders)
