"""Takes payments through Acme Pay."""

import os

SECRET_KEY = os.environ["ACMEPAY_SECRET_KEY"]
ACCOUNT_ID = os.environ["ACMEPAY_ACCOUNT_ID"]
