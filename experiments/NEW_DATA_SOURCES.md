# The three sources you supplied

All successful public downloads are cached with URLs, UTC retrieval times and SHA-256 hashes in `results/semantic_source_manifest.json`.

| Source | What is now available locally | Proper role |
|---|---|---|
| Kenneth French Data Library | Daily five factors plus risk-free rate; 480 rows in our Oct 2024–Aug 2026 window. Original percentage units normalized to decimal returns. | Ex-post risk attribution and market/style benchmarks. These current-vintage daily factors are not intraday prices or a news feed. |
| FRED | VIXCLS and T10Y2Y, Oct 2024–Sep 2026, including explicitly retained missing observations. | Market context. Historical predictive tests require publication-time/vintage handling; a date printed on a current FRED observation is not proof it was available then. |
| Databento | Documentation reviewed; no account/key or market-data download yet. | Potential replacement for Webull for historical intraday bars and options quotes, depending on entitlement and cost. |

The French factor file ends August 31, 2026. No September factors are invented or forward-filled. Same-day daily factor returns would leak future information into an intraday model, so they are not included in this volume predictor.

The FRED downloads are current snapshots, not ALFRED vintages. They are not inserted as real-time historical signals. The current pilot continues using original SEC filings and the already-working public stock-history endpoint.

## Databento setup if the organizers provide access

1. Sign in at https://databento.com/portal and open API keys. Check the hackathon's credit/redemption instructions and actual dataset permissions.
2. Save the key locally with:

```sh
python3 experiments/setup_keys.py databento
```

3. Tell the assistant the dataset name and whether credits are available. The next step should be metadata/entitlement checks and a cost estimate for a concrete request, not a bulk download.

Proposed first request: AMD, ADBE, CRM, ORCL, NFLX, COST; minute OHLCV around the 46 cached earnings filings, plus preceding same-time baseline windows. Dataset venue coverage must be explicit: single-exchange volume is not consolidated US market volume. For hedging, we additionally need historical option bid/ask, contract definitions and underlying quotes.

No Databento credential was assumed, purchased or used. The public documentation's example credentials/data are not research observations.

## Sources

- https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- https://databento.com/docs/quickstart/set-up
- https://databento.com/docs/api-reference-historical/metadata
