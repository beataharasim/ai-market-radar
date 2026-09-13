#!/usr/bin/env python3
"""
AI Market Radar – daily cross-market intelligence report.

Usage:
  python src/main.py                  # rule-based (no key needed)
  python src/main.py --llm            # try LLM if keys are set
  python src/main.py --locale zh      # Chinese output when using LLM
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Allow running from project root or from src/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_sources import collect_all
from report import generate_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ai-market-radar")


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Market Radar daily report")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Attempt LLM-enhanced report (requires LLM_API_KEY)",
    )
    parser.add_argument(
        "--locale",
        default="en",
        choices=["en", "zh"],
        help="Language for LLM report (en or zh)",
    )
    parser.add_argument(
        "--out-dir",
        default="reports",
        help="Directory to write Markdown reports",
    )
    args = parser.parse_args()

    # Load .env from project root
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")

    cg_key = os.getenv("COINGECKO_API_KEY") or None
    logger.info("Collecting market data from public sources...")
    data = collect_all(coingecko_key=cg_key)

    logger.info("Generating report (llm=%s, locale=%s)...", args.llm, args.locale)
    markdown = generate_report(data, prefer_llm=args.llm, locale=args.locale)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = root / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    suffix = f"-{args.locale}" if args.locale != "en" else ""
    out_file = out_dir / f"report-{date_str}{suffix}.md"
    out_file.write_text(markdown, encoding="utf-8")

    # Also write a latest copy for convenience
    latest = out_dir / f"latest{suffix}.md"
    latest.write_text(markdown, encoding="utf-8")

    logger.info("Wrote %s", out_file)
    logger.info("Wrote %s", latest)
    print("\n" + "=" * 60)
    print(markdown[:3000] + ("\n...\n" if len(markdown) > 3000 else ""))
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
