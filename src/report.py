"""
Report generation: rule-based Markdown + optional LLM enhancement.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from openai import OpenAI

from data_sources import ReportData

logger = logging.getLogger(__name__)


def _fmt_num(n: float, decimals: int = 2) -> str:
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.{decimals}f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.{decimals}f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.{decimals}f}K"
    return f"{n:.{decimals}f}"


def _fmt_pct(p: float) -> str:
    sign = "+" if p >= 0 else ""
    return f"{sign}{p:.2f}%"


def format_rule_based(data: ReportData) -> str:
    """Pure rule-based Markdown report (no LLM required)."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    lines: list[str] = []

    lines.append(f"# Market Intelligence Report — {date_str}")
    lines.append("")
    lines.append(f"**Generated at:** {now.isoformat()}")
    lines.append("")
    lines.append("> Rule-based analysis (no LLM). Add an LLM key for richer cross-market narrative.")
    lines.append("")

    lines.append("## Market Overview")
    lines.append("")
    lines.append("| Asset | Price | 24h Change |")
    lines.append("|-------|------:|-----------:|")
    lines.append(
        f"| BTC | ${_fmt_num(data.market.btc_price)} | {_fmt_pct(data.market.btc_change_24h)} |"
    )
    lines.append(
        f"| ETH | ${_fmt_num(data.market.eth_price)} | {_fmt_pct(data.market.eth_change_24h)} |"
    )
    lines.append("")
    lines.append(
        f"**Total Crypto Market Cap:** ${_fmt_num(data.market.total_market_cap)} "
        f"({_fmt_pct(data.market.market_cap_change_24h)})"
    )
    lines.append(f"**24h Volume:** ${_fmt_num(data.market.total_volume_24h)}")
    lines.append("")

    lines.append("## Protocol TVL Rankings")
    lines.append("")
    if data.top_tvl_gainers:
        lines.append("### Top Gainers (1d)")
        lines.append("")
        lines.append("| Protocol | TVL | 1d | 7d | Category |")
        lines.append("|----------|----:|---:|---:|----------|")
        for p in data.top_tvl_gainers:
            lines.append(
                f"| {p.name} | ${_fmt_num(p.tvl)} | {_fmt_pct(p.tvl_change_1d)} | "
                f"{_fmt_pct(p.tvl_change_7d)} | {p.category} |"
            )
        lines.append("")
    if data.top_tvl_losers:
        lines.append("### Top Losers (1d)")
        lines.append("")
        lines.append("| Protocol | TVL | 1d | 7d | Category |")
        lines.append("|----------|----:|---:|---:|----------|")
        for p in data.top_tvl_losers:
            lines.append(
                f"| {p.name} | ${_fmt_num(p.tvl)} | {_fmt_pct(p.tvl_change_1d)} | "
                f"{_fmt_pct(p.tvl_change_7d)} | {p.category} |"
            )
        lines.append("")

    lines.append("## Stablecoin Supply")
    lines.append("")
    if data.stablecoins:
        lines.append("| Stablecoin | Supply | 1d Change | 7d Change |")
        lines.append("|------------|-------:|----------:|----------:|")
        for s in data.stablecoins:
            lines.append(
                f"| {s.symbol} ({s.name}) | ${_fmt_num(s.total_supply)} | "
                f"{_fmt_pct(s.supply_change_1d)} | {_fmt_pct(s.supply_change_7d)} |"
            )
        lines.append("")
    else:
        lines.append("_No stablecoin data available._")
        lines.append("")

    lines.append("## DEX Volume (24h)")
    lines.append("")
    if data.dex_volumes:
        lines.append("| DEX | 24h Volume | Change |")
        lines.append("|-----|-----------:|-------:|")
        for d in data.dex_volumes:
            lines.append(
                f"| {d.name} | ${_fmt_num(d.volume_24h)} | {_fmt_pct(d.volume_change_1d)} |"
            )
        lines.append("")
    else:
        lines.append("_No DEX data available._")
        lines.append("")

    def _market_section(title: str, indices: list) -> None:
        if not indices:
            return
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Index / Instrument | Price | Change |")
        lines.append("|--------------------|------:|-------:|")
        for i in indices:
            lines.append(f"| {i.name} | {_fmt_num(i.price)} | {_fmt_pct(i.change_pct)} |")
        lines.append("")

    _market_section("US Equity", data.us_indices)
    _market_section("Europe Equity", data.europe_indices)
    _market_section("Asia Equity", data.asia_indices)
    _market_section("Emerging Markets Equity", data.em_indices)
    _market_section("Government Bonds", data.gov_bonds)
    _market_section("Credit / Corporate Bonds", data.credit_bonds)

    lines.append("## Market Signals")
    lines.append("")
    if data.signals:
        for s in data.signals:
            lines.append(
                f"- **[{s['severity'].upper()}] [{s['signal'].upper()}]** {s['message']}"
            )
    else:
        lines.append("_No strong signals detected today._")
    lines.append("")

    lines.append("## Quick Positioning Notes")
    lines.append("")
    bullish = sum(1 for s in data.signals if s["signal"] == "bullish")
    bearish = sum(1 for s in data.signals if s["signal"] == "bearish")
    if bullish > bearish + 1:
        lines.append("- **Bias:** Risk-on. Consider selective exposure in high-conviction themes.")
    elif bearish > bullish + 1:
        lines.append("- **Bias:** Risk-off. Prefer cash / defensive positioning.")
    else:
        lines.append("- **Bias:** Mixed / neutral. Wait for clearer cross-market confirmation.")
    lines.append("")
    lines.append("---")
    lines.append("*This is an automated, rule-based report for informational purposes only. Not financial advice.*")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are a senior cross-market analyst writing a daily intelligence report for global multi-asset investors.

Coverage: US / Europe / Asia / Emerging equities, government bonds, credit (IG & HY), and crypto/DeFi.

Your core value is connecting the dots across these markets.

Analysis Framework:
1. Risk Appetite Chain: US equities set the global tone → Europe & Asia follow → EM and crypto amplify (higher beta).
2. Rates & Duration: Government bond price moves (especially long-end Treasuries) signal rate expectations; rising yields often pressure duration-sensitive assets.
3. Credit conditions: Investment-grade vs high-yield performance indicates risk appetite and recession probability.
4. Capital Rotation: Stablecoin supply, DeFi TVL, equity leadership by region, bond vs equity relative strength.
5. Divergence Alerts: Markets moving in opposite directions are the highest-alpha signals.
6. Macro Linkages: USD strength, rate path, China policy, global liquidity.

Rules:
- Base every claim strictly on the provided data. Do not invent numbers.
- Lead with the single most important cross-market insight.
- Be concise and actionable.
- Use Markdown with clear headings and tables where helpful.
- End with a short disclaimer that this is AI-generated analysis, not financial advice.
"""


def build_data_context(data: ReportData) -> str:
    lines = ["## Raw Market Data", ""]
    lines.append("### Crypto Prices & Market Cap")
    lines.append(
        f"- BTC: ${data.market.btc_price:,.2f} ({data.market.btc_change_24h:+.2f}% 24h)"
    )
    lines.append(
        f"- ETH: ${data.market.eth_price:,.2f} ({data.market.eth_change_24h:+.2f}% 24h)"
    )
    lines.append(
        f"- Total Market Cap: ${data.market.total_market_cap / 1e9:.1f}B "
        f"({data.market.market_cap_change_24h:+.2f}% 24h)"
    )
    lines.append(f"- Total 24h Volume: ${data.market.total_volume_24h / 1e9:.1f}B")
    lines.append("")

    if data.top_tvl_gainers:
        lines.append("### Protocol TVL — Top Gainers")
        for p in data.top_tvl_gainers[:6]:
            lines.append(
                f"- {p.name} ({p.category}): ${p.tvl / 1e9:.2f}B TVL, "
                f"{p.tvl_change_1d:+.2f}% 1d, {p.tvl_change_7d:+.2f}% 7d"
            )
        lines.append("")

    if data.top_tvl_losers:
        lines.append("### Protocol TVL — Top Losers")
        for p in data.top_tvl_losers[:6]:
            lines.append(
                f"- {p.name} ({p.category}): ${p.tvl / 1e9:.2f}B TVL, "
                f"{p.tvl_change_1d:+.2f}% 1d, {p.tvl_change_7d:+.2f}% 7d"
            )
        lines.append("")

    if data.stablecoins:
        lines.append("### Stablecoin Supply")
        for s in data.stablecoins:
            lines.append(
                f"- {s.symbol}: ${s.total_supply / 1e9:.2f}B, "
                f"{s.supply_change_1d:+.3f}% 1d, {s.supply_change_7d:+.3f}% 7d"
            )
        lines.append("")

    if data.dex_volumes:
        lines.append("### DEX 24h Volume (top)")
        for d in data.dex_volumes[:8]:
            lines.append(
                f"- {d.name}: ${d.volume_24h / 1e6:.1f}M ({d.volume_change_1d:+.1f}%)"
            )
        lines.append("")

    def _add_bucket(title: str, indices: list) -> None:
        if not indices:
            return
        lines.append(f"### {title}")
        for i in indices:
            lines.append(f"- {i.name}: {i.price:,.2f} ({i.change_pct:+.2f}%)")
        lines.append("")

    _add_bucket("US Equity", data.us_indices)
    _add_bucket("Europe Equity", data.europe_indices)
    _add_bucket("Asia Equity", data.asia_indices)
    _add_bucket("Emerging Markets Equity", data.em_indices)
    _add_bucket("Government Bonds", data.gov_bonds)
    _add_bucket("Credit / Corporate Bonds", data.credit_bonds)

    if data.signals:
        lines.append("### Pre-derived Signals")
        for s in data.signals:
            lines.append(f"- [{s['severity']}] [{s['signal']}] {s['message']}")
        lines.append("")

    return "\n".join(lines)


def generate_llm_report(data: ReportData, locale: str = "en") -> Optional[str]:
    """Call an OpenAI-compatible or Anthropic-compatible endpoint."""
    api_key = os.getenv("LLM_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    provider = (os.getenv("LLM_PROVIDER") or "openai").lower()
    model = os.getenv("LLM_MODEL") or "gpt-4o-mini"
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("ANTHROPIC_BASE_URL")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lang = "Chinese (简体中文)" if locale.startswith("zh") else "English"

    user_prompt = f"""Here is today's ({date_str}) multi-asset market data (equities, government bonds, credit, crypto/DeFi):

{build_data_context(data)}

Write a cross-market intelligence report in **{lang}**. Structure it exactly as:

1. **Key Insight** — The single most important cross-market signal today (1-2 sentences)
2. **Global Risk Sentiment** — Equities (US → Europe → Asia → EM) + credit + crypto. Risk-on or risk-off? Aligned or diverging?
3. **Rates & Government Bonds** — What duration / yield moves are signalling (especially long-end Treasuries and international govvies)
4. **Credit Conditions** — IG vs High Yield performance and what it implies for risk appetite / recession risk
5. **Crypto & DeFi** — BTC/ETH, TVL trends, stablecoin supply. How does crypto relate to equities and rates today?
6. **Regional Equity Snapshot** — US, Europe, Asia, EM highlights
7. **Cross-Market Divergences** — Any markets moving in opposite directions? Why and what it implies
8. **Capital Flow Map** — Where money appears to be moving (bonds vs equities, IG vs HY, stablecoins, DeFi TVL, regional leadership)
9. **Risk Matrix** — Top 3 risks ranked by probability × impact
10. **Action Plan** — Concrete notes for: conservative / moderate / aggressive profiles

Title: "# Market Intelligence Report — {date_str}"

End with a short disclaimer.
"""

    try:
        if provider == "anthropic":
            client = OpenAI(api_key=api_key, base_url=base_url or "https://api.anthropic.com/v1")
        else:
            client = OpenAI(api_key=api_key, base_url=base_url)

        resp = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = resp.choices[0].message.content
        return content.strip() if content else None
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return None


def generate_report(data: ReportData, prefer_llm: bool = True, locale: str = "en") -> str:
    if prefer_llm:
        llm_text = generate_llm_report(data, locale=locale)
        if llm_text:
            return llm_text
        logger.warning("Falling back to rule-based report")
    return format_rule_based(data)
