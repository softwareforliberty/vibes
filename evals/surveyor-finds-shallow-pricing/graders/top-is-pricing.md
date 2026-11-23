---
type: llm
---

PASS if the top recommendation is to deepen the pricing: the base price, discount, tax and rounding pieces and the PriceCalculator become one module that owns the whole calculation, so the callers stop combining the steps themselves; and it cites callers such as orders/checkout.py or orders/invoice.py doing that combining today.
FAIL otherwise.
