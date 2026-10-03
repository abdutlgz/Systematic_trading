# API access for the next experiments

Current public-data experiments require no API keys. No orders are submitted.

## Gemini (first priority)
1. Visit https://aistudio.google.com/apikey and sign in.
2. Create a key in the hackathon/Google Cloud project you want to use. If your team received Gemini credits, follow the organizers' redemption instructions for that project.
3. In a terminal run:

```sh
cd /Users/atoleugazin/Documents/Projects/QGHACKS
python3 experiments/setup_keys.py gemini
```

Paste the key into the hidden prompt. It is saved to `.secrets/gemini.json` with owner-only permissions, excluded by `.gitignore`. The script does not contact Google or incur usage. This is a local development file, not an encrypted secret vault. Tell the assistant only that setup is complete.

Official instructions: https://ai.google.dev/gemini-api/docs/api-key

## Webull (start the application now)
1. Follow https://developer.webull.com/apis/docs/getting-started/ and its Individual Application Process link. The documentation says review typically takes 1–2 business days. Ask organizers whether they provide preapproved hackathon access.
2. Once approved, generate App Key and App Secret in Webull's portal.
3. Check the OpenAPI market-data entitlements. Mobile/desktop subscriptions do not automatically apply to OpenAPI. In the Advanced Quotes Center choose OpenAPI Advanced Quotes. Stock intraday OHLCV is the first requirement; do not buy options data solely on the assumption it includes historical expired-contract quotes.
4. Save credentials locally:

```sh
cd /Users/atoleugazin/Documents/Projects/QGHACKS
python3 experiments/setup_keys.py webull
```

Only app credentials are needed in this file, not your password or trade PIN. Saving keys does not establish historical coverage or authorize live orders.

Subscription instructions: https://developer.webull.com/apis/docs/market-data-api/subscribe-quotes/

## Data still required

| Experiment | Required fields / coverage |
|---|---|
| Intraday semantic volume | Minute OHLCV for the 10 pilot stocks, ideally >=60 sessions; feed coverage; original article text, first-publication UTC, ingestion UTC, ticker, source URL, revision timestamp. SEC filing text can be a narrower public-source starting point. |
| Dynamic hedging | Historical option bid/ask, quote UTC, underlying bid/ask, strike, expiration, call/put, contract multiplier; Greeks or enough data for a documented valuation model; historical spreads and available sizes. |
| Prediction-market corporate events | Exact matching contracts, historical rules, event source timestamps, pre-event bid/ask and depth. |
| Political portfolio backtest | Parsed transaction PDFs with original transaction date, filing date and verified public posting time, transaction type, ticker/identifier, reported amount interval, amendment linkage. Public index is downloaded but not sufficient. |
| Satellite parking | Repeated georeferenced high-resolution images, acquisition timestamps, comparable store coverage, cloud masks and usage permission. No counts are synthesized. |

Gemini is not itself a historical news database. Webull data access is not proof that a historical news archive is included.

No Solana wallet/private key is required for these experiments. Add a devnet commitment demo after a useful forecast result.

ARCC is not used yet. These pilots run locally on CPU. Later provide the approved login hostname and allocation/queue instructions, and clarify whether 2,000 GPU / 10,000 CPU means allocation hours or available processors. Do not send passwords.
