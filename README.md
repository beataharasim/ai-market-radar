# AI Market Radar

**AI-powered (or fully rule-based) daily cross-market intelligence report** covering:

- **Global equities**: US, Europe, Asia, Emerging Markets  
- **Government bonds**: US Treasuries (short / intermediate / long), international govvies, TIPS  
- **Credit**: Investment-grade & high-yield corporate, EM hard-currency bonds  
- **Crypto & DeFi**: BTC/ETH, protocol TVL, stablecoins, DEX volumes  

Inspired by [duanyytop/ai-market-radar](https://github.com/duanyytop/ai-market-radar).  
Uses only **public / free data sources**. LLM analysis is optional.

---

## Features

| Section | Content |
|---------|---------|
| **Key Insight** | Single most important cross-market signal |
| **Global Risk Sentiment** | Equities + credit + crypto risk appetite |
| **Rates & Government Bonds** | Duration / yield moves (esp. long-end Treasuries) |
| **Credit Conditions** | IG vs High Yield performance |
| **Crypto & DeFi** | BTC/ETH, protocol TVL, stablecoin supply, DEX volume |
| **Regional Equities** | US, Europe, Asia, EM major indexes |
| **Divergences & Capital Flows** | Where markets disagree and money appears to move |
| **Risk Matrix + Action Plan** | Ranked risks + conservative / moderate / aggressive notes |

---

## Data Sources (all free)

| Source | Data |
|--------|------|
| [CoinGecko](https://www.coingecko.com) | BTC/ETH prices, global market cap & volume |
| [DeFiLlama](https://defillama.com) | Protocol TVL, stablecoin supply, DEX volumes |
| [Yahoo Finance](https://finance.yahoo.com) (via `yfinance`) | Global equity indexes + bond ETFs (gov & credit) |

### Covered instruments (examples)

**Equities**  
- US: Dow Jones, S&P 500, NASDAQ Composite, Russell 2000  
- Europe: Euro Stoxx 50, DAX, FTSE 100, CAC 40, IBEX 35, SMI  
- Asia: Nikkei 225, Hang Seng, HSCEI, SSE Composite, SZSE, ChiNext, KOSPI, ASX 200, Sensex  
- EM: iShares / Vanguard MSCI EM ETFs, Bovespa  

**Government bonds**  
- US curve: TLT (20+y), IEF (7-10y), SHY (1-3y), GOVT, BND  
- International: BWX, IGOV  
- Inflation-linked: TIP  

**Credit**  
- Investment Grade: LQD, VCIT, VCSH  
- High Yield: HYG, JNK  
- EM bonds: EMB  
- Aggregate: AGG  

No paid API keys required for the rule-based report.

---

## Quick Start

```bash
# 1. Clone / copy this folder
cd ai-market-radar

# 2. Create virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run (rule-based – works immediately)
python src/main.py
```

Reports are written to `reports/report-YYYY-MM-DD.md` and `reports/latest.md`.

---

## Optional: LLM-enhanced report

1. Copy the example env file:

```bash
cp .env.example .env
```

2. Edit `.env` and add your key:

```env
LLM_PROVIDER=openai          # or anthropic
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini        # or any compatible model
LLM_BASE_URL=https://api.openai.com/v1   # change for OpenRouter / Groq / DeepSeek / Kimi etc.
```

3. Run with the flag:

```bash
python src/main.py --llm
# Chinese version
python src/main.py --llm --locale zh
```

If the LLM call fails, the script automatically falls back to the rule-based report.

---

## Daily automation (already configured)

A GitHub Actions workflow runs **every day at 06:00 UTC** and commits a fresh report to `reports/`.

You can also trigger it manually: **Actions → Daily Market Report → Run workflow**.

View the latest report:
- https://github.com/beataharasim/ai-market-radar/blob/main/reports/latest.md

---

## Project Structure

```
ai-market-radar/
├── src/
│   ├── main.py            # CLI entry point
│   ├── data_sources.py    # CoinGecko / DeFiLlama / yfinance collectors
│   └── report.py          # Rule-based + LLM report generators
├── reports/               # Generated Markdown files
├── .github/workflows/daily.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Disclaimer

This tool generates automated analysis for **informational and educational purposes only**.  
It is **not** financial, investment, or trading advice. Markets involve substantial risk of loss. Always do your own research.

---

## License

MIT
