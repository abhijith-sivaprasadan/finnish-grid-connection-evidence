# Verified source-complete long winter and Swedish border market analysis

## 27-day independent winter original-source PyPSA optimizations

Original-source-and-solver run: https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39419524961
Result and original source artifact: 12263162884.
Winter Jan18–Feb14 exclusive CSV source SHA-256: 946b47fb46a21171e0119891384800bf16060a4845e317d22a60df5abb69de4c.
Late winter Feb15–Mar14 exclusive CSV source SHA-256: d0189d056820c79b97ce4b27ab73e8e0503ad83d9875f38c8b7329a4bcc2eef1.

Two source-verified 27-day continuous windows (2,592 original 15-min 124+74 paired data each) yielded **48 genuinely optimized project solutions plus 6 references** with PyPSA/HiGHS. The source-missing February 14 prevents joining them as one 54-day battery operation.
Battery duration 0,2,4,8 hours; ±0/50 MW hindsight load flexibility; 1,000/1,500/2,000 MW fictional national balancing stress caps. Each experiment has 64,800 MWh nominal 100 MW project energy. Shortfall is artificial model stress slack, NOT actual customer unserved energy, outage or confirmed import availability.

## Actual Swedish border market data and model

Original-data and solver: https://github.com/abhijith-sivaprasadan/finnish-grid-connection-evidence/actions/runs/39420079414
Original dataset CSV and verified counterfactual artifact: 12262258789.
15 September–15 October 2025 exclusive: 2,880 complete quarter-hour source observations for each genuine Fingrid dataset:
- 31 https://data.fingrid.fi/en/datasets/31 FI-SE1 signed commercial transmission, positive Finnish export, negative Finnish import; SHA256 0ac06b6c4f4e6fb66a74368506ca9330472f02f0bbff85df2815530dcb3cf1c6
- 32 https://data.fingrid.fi/en/datasets/32 FI-SE3 signed commercial transmission; SHA256 06596a60b1d4054aadc9957728d5f672a4342a4c5dea2e4bdabad179528722ec
- 38 https://data.fingrid.fi/en/datasets/38 available intraday SE1 to FI market capacity AFTER day-ahead (MW); SHA256 db1a347f4c99fd4e9f33814bb68dd95afd7e47aa9b83527ee67ddd5ed76c6b82
- 39 https://data.fingrid.fi/en/datasets/39 available intraday SE3 to FI market capacity AFTER day-ahead (MW); SHA256 06fd05c4d7e825fb6547dbeba26d58aafefcf0aeb5e32664fa3ea9854e653bb7

Observed FI-SE1, FI-SE3 commercial flow means −525.599 MW and −204.562 MW (negative means import into FI). Two-border leftover intraday SE->FI capacity: median 553.6 MW, range 0 to 3,528.9 MW; 67.153% of intervals at least 100 MW.

A DISTINCT 100 MW project-only conditional intraday-market-access sensitivity solved 8 optimal PyPSA cases, 0/2/4/8 h hypothetical 100 MW battery, hindsight flexible load ±0/50 MW. Mathematical penalty relaxation ranges from 22,052.15 MWh (firm, no battery) to 10,868.4018 MWh (hindsight flexible + 8h). Not actual unserved power.

**Do not confuse concepts.** Signed commercial flows are not measured physical power flows. Remaining INTRADAY commercial capacity is not total interconnector physical capacity, cannot represent automatically deliverable dispatch or a connection right, and does not represent Estonia, Norway or the entire Finnish transmission system. Do not numerically equate this separate project-only counterfactual penalty with the earlier national residual one-bus model.

Without physical topology, point-level operator grid rights, actual bids/price/dispatch, reserves and valid 2030 projections, neither study can conclude a real 100 MW project is connectable. No annual 2025 source series or full-year storage solve is claimed. The source-ingestion workflow is manual-only following authenticated validation.
