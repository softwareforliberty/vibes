# How to create and revoke an Acme Pay secret key

Checked: 2026-11-24, against Acme Pay's dashboard documentation.

## Answer

Keys are created and revoked on the Keys page of the dashboard.

## Findings

- To create one: on the Keys page, click "Create secret key", name it,
  then click "Reveal" and copy it. It's shown only once. [1]
- To revoke one: on the Keys page, open the old key's "…" menu, choose
  "Revoke", and type the key's name to confirm. Revoking is immediate and
  permanent. [1]

## Sources

1. Acme Pay docs, "API keys", https://docs.acmepay.example/keys, read
   2026-11-24.

## Not settled

None.
