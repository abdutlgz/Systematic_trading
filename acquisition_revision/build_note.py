"""Build five explicitly paginated pages from the current verified result JSON."""
import html
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'output'
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'.mplconfig'))


def pct(x):return f'{100*x:.2f}%'
def num(x):return f'{x:.2f}'
def table(headers,rows):
    return '<table><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'


def main():
    r=json.loads((OUT/'results.json').read_text());role=json.loads((OUT/'classification_summary.json').read_text())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import pandas as pd
    fig,ax=plt.subplots(figsize=(9,2.65))
    for config,label in [('accounting_only','Original rules, corrected'),('issuer_controlled','Issuer controlled')]:
        d=pd.read_csv(OUT/f'{config}_daily.csv',index_col=0,parse_dates=True)
        ax.plot(d.index,d.nav,label=label,lw=1.6)
    ax.axvspan(pd.Timestamp('2025-10-01'),d.index[-1],color='gray',alpha=.12)
    ax.grid(alpha=.2);ax.set_ylabel('NAV, start = 1',fontsize=14);ax.tick_params(labelsize=13)
    ax.legend(fontsize=13,loc='upper left');fig.tight_layout();fig.savefig(OUT/'equity_note.png',dpi=180);plt.close(fig)
    m=r['metrics'];controlled=m['issuer_controlled'];is_=controlled['IS'];test=controlled['historical_test']
    obs=controlled['test_observed_rf_only'];p=r['placebo'];fac=r['factor_attribution']['issuer_controlled']
    actions=sum(1 for _ in (HERE/'corporate_actions.csv').open())-1
    performance=table(['Configuration / window','CAGR','Ann. vol.','Excess Sharpe','Max DD'],[
        ['Accounting / IS',pct(m['accounting_only']['IS']['cagr']),pct(m['accounting_only']['IS']['vol']),num(m['accounting_only']['IS']['excess_sharpe']),pct(m['accounting_only']['IS']['max_drawdown'])],
        ['Accounting / test',pct(m['accounting_only']['historical_test']['cagr']),pct(m['accounting_only']['historical_test']['vol']),num(m['accounting_only']['historical_test']['excess_sharpe']),pct(m['accounting_only']['historical_test']['max_drawdown'])],
        ['Controlled / IS',pct(is_['cagr']),pct(is_['vol']),num(is_['excess_sharpe']),pct(is_['max_drawdown'])],
        ['Controlled / test',pct(test['cagr']),pct(test['vol']),num(test['excess_sharpe']),pct(test['max_drawdown'])],
        ['Controlled / to Aug.',pct(obs['cagr']),pct(obs['vol']),num(obs['excess_sharpe']),pct(obs['max_drawdown'])]])
    stress=table(['Controlled diagnostic','IS Sharpe','Test Sharpe'],[
        ['Base',num(is_['excess_sharpe']),num(test['excess_sharpe'])],
        ['2x fees, 3% borrow',num(m['stress_2x_fees_3pct_borrow']['IS']['excess_sharpe']),num(m['stress_2x_fees_3pct_borrow']['historical_test']['excess_sharpe'])],
        ['Five additional sessions delay',num(m['delay_5_sessions']['IS']['excess_sharpe']),num(m['delay_5_sessions']['historical_test']['excess_sharpe'])]])
    factor=table(['Controlled attribution','Ann. alpha','NW alpha t','SMB loading','R-squared'],[
        [w,pct(fac[k]['alpha_annual']),num(fac[k]['coefficients']['alpha']['nw_t']),num(fac[k]['coefficients']['SMB']['coefficient']),num(fac[k]['r2'])]
        for w,k in [('IS','IS'),('Test to Aug. 31','historical_test')]])
    liquidity=table(['Illustrative AUM','95th % entry / ADV','Entries >5% ADV','Entries >3 days*'],[
        [f"${c['aum']/1e6:.0f}M",pct(c['p95_participation']),pct(c['share_over_5pct_adv']),pct(c['share_requiring_over_3_days_at_5pct_adv'])]
        for c in r['capacity_illustrative']])
    pages=[]
    pages.append(f'''<h1>Acquisition-filer short strategy</h1><p class="subtitle">Corrected accounting and retrospective risk study | October 3, 2026</p>
    <div class="callout"><b>Research conclusion.</b> Short acquisition-agreement 8-K filers and buy SPY to reduce market exposure. The corrected issuer-controlled variant has IS/test cash-excess Sharpe {num(is_['excess_sharpe'])}/{num(test['excess_sharpe'])}. The previously examined test is descriptive evidence, not fresh confirmation. Execution and issuer-role validation remain incomplete.</div>
    <h2>1. Economic foundation and testable prediction</h2>
    <p>Acquisitions can create overpayment, integration costs and financing risk. Investors may initially underweight those costs and reprice the buyer over subsequent months. The testable prediction is negative post-filing stock performance relative to a market hedge, after dividends, financing, borrow and trading costs.</p>
    <p>This is a hypothesis, not a demonstrated causal effect. Synergies can benefit buyers. Savor and Lu (2009) find evidence that successful stock-financed acquisitions can benefit acquirers relative to failed deals [1]; their work does not justify treating every acquisition as value destruction. The strategy is also exposed to short squeezes and takeover-target premiums.</p>
    <h2>2. Signal, timing and data</h2>
    <p>Massive acquisition-agreement 8-K disclosures supply filing dates, tickers, supporting text and source URLs. Existing prior-day market-cap inputs select filers with cap at least $2B. The retained input has {role['events']:,} event records. The first session close strictly after the filing date is the entry; same-day entry is excluded. An event receives up to 2% of current NAV in stock short and an entry-beta SPY long. Beta uses prior sessions [-260:-10], clipped to 0.5-1.5, with fallback 1 when history is insufficient. Scheduled exit is 60 sessions after entry.</p>
    <p><b>Windows:</b> development (IS), January 2022-September 2025; historical test, October 2025-September 2026. The test was already inspected before this revision. No candidate or parameter is reselected here. “Filer” is the executable label: it is not equivalent to “verified acquisition buyer.”</p>
    <p>Massive split-adjusted closes do not incorporate cash dividends [2]. Dividends are therefore accounted separately [3]. Current historical snapshots and split normalization are not proof of a point-in-time live feed.</p>''')
    pages.append(f'''<h1>Accounting and risk controls</h1><h2>3. A self-financing fixed-share ledger</h2>
    <p>The old calculation applied constant event weights to each day's percentage returns. This revision enters share quantities and holds them until an actual exit or a disclosed risk trim. NAV equals free cash + restricted cash + signed accrued obligations - marked stock shorts + marked SPY holdings. Short-sale proceeds are restricted, earn no rebate and cannot fund an additional unrestricted hedge.</p>
    <p>Stock trades cost 10 bps and SPY trades 2 bps on actual traded notional. Borrow is 1% annually on prior marked stock liability, charged for elapsed calendar days. Positive free cash earns French RF; negative cash pays RF plus 150 bps/year. Ex-date dividends create receivables or short liabilities, settled on pay-date. These are explicit modeling assumptions, not historical broker terms.</p>
    <p>The ledger includes {actions} source-linked action rows for cash mergers, ticker identities, successor obligations and the FBHS/MBC spinoff. Cash mergers close the short and hedge at the event session; stock/cash conversions preserve original expiry. CVRs are reserved at contractual maximum, a conservative liability bound rather than observed fair value. BLD uses an estimated cash-election proration; lender election and final delivery are unknown. MBC distributed short shares are bought back at the first regular-way close. These post-protocol accounting decisions are recorded in <code>DEVIATIONS.md</code>.</p>
    <h2>4. Original rules versus a new controlled variant</h2>
    <p><b>Accounting only:</b> retain the original 50-event limit and allow issuer overlap. Share-value drift means there is no enforceable 100%-NAV short or 2%-issuer limit. <b>Issuer controlled:</b> reject concurrent same-issuer entries, cap fee-aware entry stock exposure at 2% per issuer and 100% total short, and cover excess marked exposure with proportional paired-hedge sales. Trims incur costs. This changes the strategy retrospectively; it is reported separately without choosing a winner.</p>
    <p>Executable quotes are required. On November 8, 2024, CLSK's missing close causes a logged {pct(r['checks']['max_close_issuer_weight'])} carried issuer exposure rather than a fabricated trim. Same-close sizing and execution remain idealized. Broker locate, recall, margin and liquidation behavior are absent. Live deployment requires those inputs and a stale-feed entry stop.</p>
    <p>There are zero unresolved overdue exits in the four final configurations. Sixteen synthetic accounting tests pass, including dividend accrual, calendar-day borrow, corporate actions, insolvency and future-price invariance. Replayed NAV identities agree within 2 x 10<sup>-15</sup>. This verifies accounting arithmetic, not historical execution feasibility.</p>
    <p>Fixed diagnostics double fees with 3% borrow, or delay entry five additional sessions. Neither is a parameter search or multi-day-fill simulation. Original-note Sharpe figures use different accounting and benchmark definitions.</p>''')
    pages.append(f'''<h1>Corrected performance</h1><h2>5. Results after costs and cash accounting</h2>{performance}
    <p>IS has {is_['sessions']} sessions and the full test {test['sessions']}. Annualized Sharpe = mean(daily NAV return - RF) / standard deviation of that excess series x sqrt(252). CAGR compounds NAV; volatility uses total daily returns. Drawdown resets each displayed window with initial NAV included in the peak.</p>
    <p>The controlled test arithmetic annual return is {pct(test['arithmetic_return'])}; its total-return Sharpe is {num(test['total_return_sharpe'])}, distinct from cash-excess Sharpe {num(test['excess_sharpe'])}. French rates/factors stop August 31; {r['checks']['rf_proxy_sessions']} September sessions use the last RF observation. Through August, excess Sharpe is {num(obs['excess_sharpe'])}. The full-window positive result depends heavily on September returns, not merely the RF convention.</p>
    <img class="chart" src="equity_note.png" alt="Corrected full-path NAV; test window shaded">
    <p class="caption">Continuous NAV; test shaded. Series include maximum-CVR reserves and delivery proxies.</p>
    {stress}''')
    pages.append(f'''<h1>What the evidence establishes</h1><h2>6. Matched ordinary-date controls</h2>
    <p>One hundred seeded IS placebos use the same feasible issuer/event multiplicities, random available dates ending July 1, 2025 and exclusion of +/-90 calendar days around each issuer's acquisition filings. Seven records across KRMN, MIME and NLSN lack feasible control dates and are removed from both observed and control samples. The main candidate remains unchanged; the matched comparison has {p['matched_sample']['matched_events']} events.</p>
    <p>The matched observed cash-excess Sharpe is {num(p['observed_is_excess_sharpe'])}, versus placebo mean {num(p['mean'])} and 95th percentile {num(p['p95'])}. {p['number_ge_observed']} of {p['replicates']} placebos equal or exceed observed; the finite-sample tail fraction is (1 + count)/(1 + 100) = {p['finite_sample_tail_fraction']:.4f}. This is an encouraging date-specific contrast, not a family-wise significance result. Calendar conditions, event clustering, occupancy and execution availability need not be exchangeable. Rejection of these controls does not prove acquisition causality or a live trading edge.</p>
    <h2>7. Factor attribution and residual return</h2>{factor}
    <p>FF5 plus momentum regressions use the same cash-excess return as headline Sharpe, with Newey-West lag 5 errors. RF is not subtracted twice. Test attribution ends August 31 ({fac['historical_test']['sessions']} sessions); September is omitted rather than inventing factor data. Strong negative SMB exposure explains substantial variation, while residual alpha t-statistics are weak. The strategy may partly express a size/style exposure rather than acquisition-specific mispricing.</p>
    <h2>8. Buyer identification and research history</h2>
    <p>All {role['events']:,} records have cached supporting text and source URLs, but the transparent snippet heuristic suggests only {role['heuristic_role_counts']['acquirer_suggested']} buyers and {role['heuristic_role_counts']['target_suggested']} targets, leaving {role['heuristic_role_counts']['unknown']:,} unknown. No human labels exist; no classifier accuracy is claimed. A seeded 30-event review sheet is supplied. Suggestions use filing text alone and are not trading filters; future volatility cannot establish an ex-ante buyer label.</p>
    <p>The legacy grid declared 204 variants, 165 usable in its saved report. The project's separate discovery tables contain 36 rows and the momentum sweep 18 variants plus a reference. These are broader research exposures, not 32 independent trials. No project-wide multiplicity correction is claimed. The revision adds two accounting/control configurations and two diagnostics, without selection. Old selection statistics are not transplanted onto the new ledger.</p>''')
    pages.append(f'''<h1>Liquidity, reproducibility and decision</h1><h2>9. Capital is a feasibility question</h2>{liquidity}
    <p>*Share of entry-sized orders requiring more than three days at 5% of prior 20-session ADV, assuming constant ADV and price. The {r['capacity_illustrative'][0]['entries_with_adv']} IS entries have complete ADV. This is not an execution simulation; borrow and crowded demand can reduce deployable capital.</p>
    <p>At $100M, the largest entry is {pct(r['capacity_illustrative'][2]['max_participation'])} of prior ADV. An entry-based, two-sided square-root impact illustration gives {pct(r['capacity_illustrative'][2]['illustrative_two_sided_entry_based_impact_per_year'])} annually, in addition to fixed costs; it excludes separate trim/exit liquidity and is not deducted from headline NAV. There is no demonstrated $100-150M capacity.</p>
    <h2>10. Reproduction and competition evidence boundary</h2>
    <p><code>run.py --placebos 100</code> reruns all four ledgers and controls offline from licensed inputs. <code>verify.py</code> provides keyless saved-metric, balance and timing checks plus 16 tests. Input/artifact manifests hash raw snapshots, protocol, journal, code and results. Exact raw reconstruction requires the licensed snapshot and entitlements; output replay alone is insufficient.</p>
    <p><b>Decision:</b> retain an auditable research candidate, with no pristine-holdout or unqualified “no lookahead” cap-rule claim. Weak residual alpha, unverified buyer roles and idealized execution remain material. Freeze a verified-buyer protocol and live decision timestamps before collecting new forward observations; obtain locate/recall and margin data before deployment.</p>
    <h2>References and audit files</h2>
    <p>[1] <a href="https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Stock_Mergers_Value.pdf">Savor &amp; Lu (2009), Do Stock Mergers Create Value for Acquirers?</a><br>
    [2] <a href="https://massive.com/knowledge-base/article/is-massives-stock-data-adjusted-for-splits-or-dividends">Massive: stock adjustment convention.</a><br>
    [3] <a href="https://massive.com/docs/rest/stocks/corporate-actions/dividends">Massive: dividends API.</a> Ten disclosed FX proxy rows: <code>data/dividend_overrides.csv</code>.<br>
    [4] <a href="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html">Kenneth French Data Library: RF, FF5 and momentum.</a><br>
    Merger terms: <code>corporate_actions.csv</code>. Methods: protocol, deviations, trial ledger and README. Exact metrics: <code>output/results.json</code>.</p>''')
    style='''@page {size:Letter;margin:1in;} *{box-sizing:border-box;} body{margin:0;color:#162432;font:11pt/1.28 Georgia,serif;}
    .page{height:8.96in;position:relative;break-after:page;} .page:last-child{break-after:auto;}
    h1{font:700 21pt/1.14 Arial,sans-serif;margin:0 0 11pt;color:#112e43;} h2{font:700 12pt/1.2 Arial,sans-serif;margin:14pt 0 7pt;}
    p{margin:0 0 9pt;} .subtitle{font-family:Arial,sans-serif;color:#526b7b;margin-bottom:15pt;}
    .callout{padding:11pt 12pt;background:#edf4f7;border-left:3pt solid #2a7890;margin-bottom:12pt;}
    table{width:100%;border-collapse:collapse;font:11pt/1.15 Arial,sans-serif;margin:8pt 0 10pt;} th{text-align:left;background:#e8f0f4;color:#153e54;}
    td,th{padding:6pt 5pt;border-bottom:1px solid #d7e0e5;} td:not(:first-child){white-space:nowrap;}
    code{font:11pt/1.28 Menlo,monospace;overflow-wrap:anywhere;} .chart{width:100%;height:1.95in;object-fit:contain;margin:0;}
    .caption{color:#526b7b;margin-top:2pt;} a{color:#205d79;text-decoration:none;} .footer{position:absolute;bottom:0;width:100%;padding-top:7pt;border-top:1px solid #bccbd3;font:11pt Arial,sans-serif;color:#526b7b;display:flex;justify-content:space-between;}'''
    body=''.join(f'<section class="page">{page}<div class="footer"><span>Acquisition-filer research revision | 2026-10-03</span><span>{i+1} / 5</span></div></section>' for i,page in enumerate(pages))
    (OUT/'quant_note_revised.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>Acquisition-filer research revision</title><style>'+style+'</style></head><body>'+body+'</body></html>')
    # A readable, source-linked text companion is built from exactly the same pages.
    import re
    markdown='\n\n'.join(re.sub('<[^>]+>',' ',p).replace('&amp;','&') for p in pages)
    (OUT/'quant_note_revised.txt').write_text(re.sub(r' +',' ',markdown))
    (OUT/'pdf').mkdir(exist_ok=True)
    print('Five-page HTML note generated from results.json; PDF target: output/pdf/quant_note_revised.pdf')


if __name__=='__main__':main()
