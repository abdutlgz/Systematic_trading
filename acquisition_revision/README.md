# Acquisition-filer strategy: corrected research package

This is a separate revision of `notes/quant_note.pdf`, based on the acquisition-filer strategy that the note actually presents. The original note, `event8k/` selection grid and other momentum research are preserved. No new best parameter was selected. Read the revised five-page note at `output/pdf/quant_note_revised.pdf` and exact metrics in `output/results.json`.

The idea is to short a company after an acquisition-agreement 8-K and buy SPY as a market hedge for 60 sessions. Possible acquisition overpayment and integration costs motivate the hypothesis. The current signal identifies acquisition **filers**, not verified buyers, and the evidence does not yet establish profitable buyer-specific drift.

## New evidence addendum

[Evidence upgrade](evidence_upgrade/README.md) adds 30 exact-accession assistant source reviews, a locally frozen verified-buyer forward protocol, and a fresh licensed-input reconstruction that exactly matches the original four ledgers and 100 placebos. The five-page PDF remains the historical audit edition; read the [addendum](evidence_upgrade/EVIDENCE_ADDENDUM.md) for the current evidence. Labels were not used to refilter historical portfolios. Independent human validation, external freeze publication and future performance remain pending.

## What changed

- Fixed share quantities replace the original constant daily portfolio-weight calculation. NAV now reconciles to free cash, restricted short proceeds, dividends, stock liabilities and SPY holdings.
- Dividends, actual traded-notional fees, calendar-day borrow and debit financing are charged explicitly. The headline Sharpe subtracts RF. Annual arithmetic return, CAGR and total-return Sharpe are separate fields.
- A source-linked corporate-action journal closes cash mergers, carries stock obligations into successor symbols and joins one-for-one ticker changes. CVRs use maximum-liability reserves; BLD delivery remains a lender-election proxy. These assumptions are not described as verified broker execution.
- The original event-slot rules and a new issuer-controlled variant are reported separately. The latter rejects issuer overlap, sizes after fees and trims marked issuer/short exposure with costs. Unexecutable trims and missing marks remain visible.
- Four fixed configurations, 100 seeded ordinary-date placebos, consistently defined FF5+momentum attribution and prior-date ADV diagnostics are saved. This is an audit, not another optimization sweep.
- A 30-event manual-review worksheet uses filing text alone, retains `unknown`, and contains no invented classifier accuracy. Broader trial counts and protocol deviations are documented.
- Sixteen deterministic accounting tests and a keyless metric/ledger verification runner support reproducibility. Raw data availability remains separate from output replay.

## Reproduce existing local inputs

From the repository root, with the existing virtual environment:

The recorded run used Python 3.9.10; `requirements.txt` pins the five installed research dependencies.

```sh
.venv/bin/python -m unittest discover -s acquisition_revision/tests -v
.venv/bin/python acquisition_revision/run.py --placebos 100
.venv/bin/python acquisition_revision/evidence.py
.venv/bin/python acquisition_revision/build_note.py
.venv/bin/python acquisition_revision/verify.py
```

The full simulation and placebos are offline once `data/` is prepared. It reruns financial accounting; it does not repeat strategy selection. `build_note.py` produces HTML and a text companion directly from the current result JSON. Printing the HTML to Letter PDF with browser headers/footers disabled produces the five-page artifact. PDF production requires a local browser; the generated document is included.

For judges who have derived outputs but no vendor license/key:

```sh
python -m pip install -r acquisition_revision/requirements.txt
python acquisition_revision/verify.py
```

That command recomputes reported metrics and balance identities from saved daily ledgers and runs the 16 synthetic tests. It **does not** independently reconstruct signals or raw prices. `output/artifact_manifest.json` fingerprints code and results; `output/input_manifest.json` fingerprints local raw inputs, protocol and journal. Public evidence sheets with supporting text are excluded from redistribution.

## Collect/rebuild licensed inputs

Requires the repository's existing `event8k/data/grid_events.csv`, `grid_prices.csv`, `acq_dollar_volume.csv`, French daily factor files and cached 8-K disclosures. Their original builders and vendor entitlements remain necessary for a fresh checkout. Supply `MASSIVE_API_KEY` through the environment or the existing ignored starter `.env`; credentials are never placed in outputs.

```sh
python acquisition_revision/prepare.py --dividends
python acquisition_revision/actions.py
python acquisition_revision/fx.py --download
python acquisition_revision/actions.py
python acquisition_revision/prepare.py
python acquisition_revision/run.py --placebos 100
```

The first action pass snapshots original dividends/prices. FX normalization then applies source-linked overrides on the second action pass; the last preparation refreshes hashes after these deliberate corrections. Current vendor snapshots may differ from the recorded files. A license and the saved licensed snapshot are required for exact raw-input reproduction. Do not redistribute `data/`, `cache/` or licensed filing-text sheets.

## Limits of this revision

The historical test was examined before these corrections and is not a pristine holdout. Future-informed split normalization, same-close sizing/fills, current vendor histories and the manual action journal remain point-in-time/execution limitations. Results include a conservative CVR liability bound, not mark-to-market fair values. No historical stock-locate, recall, maintenance-margin or paying-agent cash model exists. The one-day CLSK missing quote causes a logged issuer-cap breach. Enbridge and CNHI 2022 currency conversions are proxies, although those dividends have no held exposure in the issuer-controlled candidate. September 2026 uses the last observed French RF value; the test ending August is reported alongside the full window.

Do not claim a demonstrated $100-150M capacity, a validated live Sharpe, verified acquisition-buyer classification or an unqualified competition cap-rule pass. Read `DEVIATIONS.md`, `PROTOCOL.md` and `TRIAL_LEDGER.md` for the audit boundary. Next research decisions should be frozen before new forward data and verified issuer labels are examined.
