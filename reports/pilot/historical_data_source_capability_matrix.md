# Historical Data Source Capability Matrix

## Scope

This is an access-capability investigation for the 22 current `SOURCE_NEEDED`
rows in the Step 2C research dataset gate. It did not call a market-data API,
download OHLCV, alter raw data, alter ticker mappings, or begin Step 3.

"Unknown" means the public documentation reviewed does not establish coverage
for the exact Thai security and period. It is not evidence that the data does
not exist.

| Source | SET coverage | Earliest history | Daily OHLCV | Intraday | Delisted securities | API | Authentication | Paid | Historical ticker support | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| SET Historical Data / SETSMART / SMART Marketplace | Primary route; SET documents historical trading/statistics data for all securities | SET Historical Data page states 1975-04-30 for historical trading/statistics; SETSMART investor web advertises 5 years; package-specific API depth | Documented EOD trading price/statistics; exact OHLCV schema and volume fields require confirmation | SET tick data is a separate request/product | Exact predecessor/delisted delivery for these rows not publicly confirmed | SMART Marketplace/API and SETSMART/API products | Yes; account/package or request workflow | Yes; SET states 10,000 baht per one year for one-time historical request | Potentially, if the requested historical security is identified in the delivery; not verified here | Strongest candidate because it is the exchange source. |
| EODHD | BK/XBKK exchange and Thai instrument pages are visible | Thailand-specific earliest date unknown; provider-wide delisted documentation is not a substitute | Documented daily open/high/low/close/adjusted close/volume | Endpoint exists; BK retention unknown | Provider supports `delisted=1`; exact Thai predecessor coverage unknown | Yes | API token | Free plan is shallow; deeper history requires a paid plan | Renamed symbols do not automatically preserve history; exact BK symbol list needs checking | BLA.BK and IRPC.BK are candidates only; no calls were made. |
| Yahoo Finance / yfinance | Current project mapping only; no verified predecessor coverage for these gaps | Generic Yahoo help says historical data is usually not earlier than 1970; exact Thai ticker maximum unknown; project audit observed mapped coverage from 2022-07-01 | Yes, subject to symbol availability | yfinance documents intraday limits including last 60 days; no tick-history guarantee | Thai delisted/predecessor support not verified | yfinance wrapper/download endpoints | yfinance generally no token; Yahoo CSV download/licensing can require Gold | Product/licensing dependent | Weak for this experiment; do not infer a successor ticker is a historical predecessor | Existing verified mapping remains authoritative; this investigation does not regenerate it. |
| Bloomberg | SET coverage and exact depth not verified | Unknown for this scope | Historical study/EOD functionality documented | Product-dependent; exact SET coverage unknown | Product-dependent; not verified | BLPAPI | Yes | Yes | Security master/history handling exists, but exact Thai predecessor result not verified | Institutional candidate, not an established recovery route. |
| LSEG / Refinitiv | Exact SET coverage not verified | Tick History documentation says global history back to Jan 1996; SET-specific earliest date unknown | Daily and other interday intervals documented | Tick and multiple intraday intervals documented | Security identity/product-dependent; not verified for these rows | RDP / Tick History APIs | Yes | Yes | Potentially strong security-master route; exact predecessor availability unknown | Requires separate subscription/login. |
| FactSet | Exact SET coverage not verified | Unknown | Global Prices API documented; exact Thai start date unknown | Tick History product documented; exact SET coverage unknown | Not verified for these rows | FactSet APIs | Yes | Yes | Product supports security history, but Thai predecessor result not verified | Institutional candidate. |
| TradingView | SET listed in data coverage | Historical depth/security-specific start unknown | Chart data can be exported, but exact OHLCV completeness is not established | Real-time/delayed chart feed; historical intraday depth unknown | Not verified | Public API route for this use not established | Account/subscription dependent | Yes for some real-time tiers | Not verified | Useful for visual/manual investigation, not a verified bulk recovery source. |
| Alpha Vantage | SET-specific coverage not verified | Documentation claims 25+ years for global daily endpoint; Thailand/security-specific start unknown | Daily OHLCV endpoint documented | Not established for this use | Not verified | REST API | API key | Rate/depth limits and premium features | Not verified | Do not treat generic global documentation as proof of SET coverage. |
| Stooq | SET coverage not verified | Unknown | Not verified | Not verified | Not verified | Not established | Unknown | Unknown | Not verified | No authoritative SET capability evidence found. |

## Source references

- [SET Historical Data](https://www.set.or.th/th/services/connectivity-and-data/data/historical)
- [SET SMART Marketplace](https://www.set.or.th/en/services/connectivity-and-data/data/smart-marketplace)
- [SETSMART FAQ](https://media.set.or.th/set/Documents/2022/Jul/SETSMART_web_FAQs.pdf)
- [SET tick data](https://www.set.or.th/en/app/online-data/tick-data?lang=en)
- [EODHD historical data API](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes)
- [EODHD delisted securities](https://eodhd.com/financial-apis/delisted-stock-companies-data-2)
- [EODHD BK exchange](https://eodhd.com/exchange/BK)
- [yfinance history reference](https://ranaroussi.github.io/yfinance/reference/yfinance.functions.html)
- [Yahoo historical-data help](https://au.help.yahoo.com/kb/finance-for-web/download-historical-data-yahoo-finance-sln2311.html)
- [LSEG historical pricing](https://developers.lseg.com/en/article-catalog/article/building-power-query--m--to-retrieve-historical-pricing-from-lse)
- [LSEG Tick History guide](https://developers.lseg.com/content/dam/devportal/api-families/thomson-reuters-tick-history/trth-rest-api/documentation/tick_hist_user_guide_jan2021.pdf)
- [FactSet Developer](https://developer.factset.com/)
- [TradingView data coverage](https://www.tradingview.com/data-coverage/)
- [Alpha Vantage documentation](https://www.alphavantage.co/documentation/)
