# Evidence upgrade

This extends the acquisition-filer research package without changing historical portfolios or selecting another winning parameter. Read [the evidence addendum](EVIDENCE_ADDENDUM.md) alongside the existing five-page PDF.

Three concrete improvements are included:

- **Source-reviewed roles:** 30 frozen, stratified cases were checked against exact-accession 8-K Items retrieved from licensed Massive inputs. There are 19 buyers, 10 targets and one complex combination. Fourteen qualify as new buyer agreements under the prospective rule. CRC was incorrectly suggested as a target; WillScot's sampled filing is a termination. Roles and event status now have separate labels and source anchors.
- **Frozen prospective rules:** a new verified-buyer paper test admits events October 5, 2026 through October 4, 2027. It fixes the eligibility, receipt timing, pre-close share sizing, costs, risk controls and primary statistic before outcomes. `forward_freeze.json` pins the code and protocol; the journal chains timestamped observations, reviews, decisions and paper fills.
- **Independent input reconstruction:** 4,080 fresh licensed responses, plus public factor/FX sources, rebuilt 1,109 events and 715 price columns. All four historical daily-return series, reported metrics and 100 placebos matched exactly. The same public accounting implementation and manual corporate-action journal were reused; this is independent input collection, not an independently written trading engine.

These are assistant source reviews, **not independent human gold labels** or estimated population accuracy. Parsed Items do not guarantee full exhibits. The 30 cases do not establish a profitable buyer effect and were not used to refilter historical results. The old historical test remains previously examined. No forward returns exist yet. The freeze is local; external publication/registration is still needed for an independently witnessed timestamp.

## Verify without a license

From the repository root, install `acquisition_revision/requirements.txt` in your Python environment, then run:

```sh
python acquisition_revision/verify.py
python acquisition_revision/evidence_upgrade/forward.py check
python acquisition_revision/evidence_upgrade/verify_upgrade.py
```

The first command checks 16 accounting fixtures and saved financial ledgers. The last checks 16 evidence fixtures, public label consistency, saved reconstruction reports and frozen hashes. If ignored licensed files exist locally, it additionally verifies filing anchors and the 4,080 response hashes. Without them, it explicitly reports that source-text verification was unavailable. Checking a saved reconstruction report is not a fresh reconstruction.

## Reconstruct from licensed inputs

Requires Massive entitlements to disclosures, parsed 8-K Items, historical ticker reference data, daily bars and dividends. Set `MASSIVE_API_KEY` in the environment; the existing ignored starter `.env` is also supported. No API key is included in artifacts. Start with a new isolated directory for fresh collection:

```sh
python acquisition_revision/evidence_upgrade/collect_reviews.py
python acquisition_revision/evidence_upgrade/audit_labels.py
python acquisition_revision/evidence_upgrade/reconstruct.py --workspace acquisition_revision/evidence_upgrade/data/new_reconstruction --simulate --placebos 100
```

`collect_reviews.py` uses the included frozen sample even when original raw research files are absent. The rebuild does not require the parent `data/`, price grid or disclosure cache. It downloads source responses into its own cache, constructs inputs, then compares results with the supplied public historical outputs. The manual public corporate-action journal remains a declared input. New vendor snapshots may differ; preserve and explain differences rather than adjusting rules to recover a match.

To replay the already collected isolated cache without network access:

```sh
python acquisition_revision/evidence_upgrade/reconstruct.py --workspace acquisition_revision/evidence_upgrade/data/clean_reconstruction --offline --simulate --placebos 100
```

`data/`, `cache/` and `runtime/` are ignored. Do not include licensed full response/filing collections in a GitHub upload. The public review CSV contains only short evidence anchors and original SEC source URLs.

## Operate the forward test

Read [FORWARD_PROTOCOL.md](FORWARD_PROTOCOL.md) first. Version 1 is already frozen: do not rerun a modified protocol under the same version. Save/publish `forward_freeze.json` and its pinned files before the first admission. Future fixes need a new version and dated incident record.

The command interface accepts operator JSON packets via `--input PATH`. Observation and review timestamps come from the actual clock, not a supplied backdated receipt. Calls must occur when information is received; entries are allowed only on the first session after both filing and observation dates.

1. `forward.py observe`: accession number, issuer CIK, ticker, timezone-aware `filing_utc`, and source URL. Supply the actual SEC acceptance timestamp, not midnight inferred from a date-only vendor field. Candidate discovery can use Massive, but this runner does not schedule automatic polling.
2. `forward.py review`: accession, CIK, `role`, `event_kind`, `source_file` relative to the packet, `evidence_anchor`, named `reviewer`, and `review_method` (`assistant` or `independent_human`). Include `ambiguous` and `human_signoff` accurately. The interface checks the anchor against the saved source and records its hash. Independently adjudicate ambiguous cases or skip them.
3. `forward.py decide`: accession plus `market` and `state` objects. Field names and a complete synthetic packet are in `tests/test_evidence.py::fixture`. Record contemporaneous quotes, beta history, prior-session cap/20-session ADV, dated locate capacity/borrow rate, margin approval and reconciled NAV balances. The journal supplies prior admissions. Commit during the five-minute cutoff window; missing, stale or excluded inputs produce a recorded skip.
4. `forward.py fill`: accession, `filled_utc`, stock/SPY filled shares and prices, `execution_mode: paper_auction_model`, closing-auction `source_file`, and any extra broker fee. Quantities cannot exceed the committed order. This records documented paper fills and never sends orders.

The harness supplies an entry planner and evidence journal, not an automated broker or a complete forward NAV engine. Reconciled daily accounting, cash/debit rates, dividend/action obligations, recalls, exits and risk reductions must be collected and implemented under the frozen protocol before a primary performance claim. Log operational gaps; do not fabricate locates or forward P&L. Minimum 30 executed entries and 200 reconciled sessions are required; evaluate only after final fixed exits.
