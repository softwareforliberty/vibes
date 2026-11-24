# Wizard plan: set up Acme Pay

Title: Set up Acme Pay for this project

## Stage 1: Create a new secret key

- Page: https://dashboard.acmepay.example/keys
- Value: ACMEPAY_SECRET_KEY. The person finds it on the page once they've
  created the key. It's a secret. Save it in .env and as the GitHub secret
  ACMEPAY_SECRET_KEY.
- Note: research/acme-pay-keys.md

## Stage 2: Revoke the old key

- Page: https://dashboard.acmepay.example/keys
- No value. Revoking can't be undone: anything still using the old key
  stops working at once.
- Note: research/acme-pay-keys.md

## Stage 3: Copy the account id

- Page: https://dashboard.acmepay.example/settings/account
- Value: ACMEPAY_ACCOUNT_ID. Shown on the page. Not a secret. Save it in
  .env and as the GitHub variable ACMEPAY_ACCOUNT_ID.
- Note: research/acme-pay-account.md
