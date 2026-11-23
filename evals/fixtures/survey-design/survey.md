# Survey: orders

Looked at: orders/pricing/ and its callers, the hotspots.

## Top recommendation

C1: pricing changes in most commits, and every change touches its callers.

## C1. Deepen pricing into one Price module: Strong

- **Files:** orders/pricing/base_price.py, discount.py, tax.py,
  rounding.py and calculator.py, and their callers orders/checkout.py,
  orders/invoice.py and orders/quote.py.
- **Problem:** each caller runs the base price, discount, tax and rounding
  steps itself, and orders/invoice.py:11 runs tax before the discount, so
  invoices disagree with checkout. PriceCalculator must have set_customer
  and set_region called before total.
- **Deletion test:** deleting the four step modules would barely change
  the callers, which already hold the sequence: the modules are shallow.
- **Proposal:** one module that prices lines for a customer, holding the
  steps and their order, so callers make one call.
- **Benefits:** the sequence lives in one place; tests drive real prices
  through it instead of each step alone.
- **Cost and risk:** small: three callers and one test file.
- **Decision records:** none.

## Left alone

- orders/storage.py: deep already, and kept by
  docs/adr/0001-keep-the-store-behind-one-interface.md.
