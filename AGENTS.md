# AGENTS.md

Repository: tradetron-brain. Purpose: a single verifiable knowledge base for
building Tradetron strategies with Zerodha Kite market data.

## Hierarchy of truth

1. 00_CORRECTIONS_LEDGER.md wins over everything, including your own memory.
2. An official exchange circular or a live broker API response wins over any doc.
3. Files in 90-archive/raw-imports are historical evidence, NOT current truth.
   They contain known errors. Never quote them as fact.
4. If the ledger and a doc disagree, the ledger is right and the doc is stale.
   Report the contradiction; do not silently pick one.

## Evidence tags - mandatory on every factual claim

- [V] Verified: you fetched it this session from a primary source. Cite the URL
      or the exact API call and the date.
- [O] Official doc: stated in vendor documentation, not independently tested.
- [I] Inferred: your reasoning from [V] or [O] facts. Say which ones.
- [U] Unverified: you believe it but cannot show a source. Treat as a question.

An untagged claim is treated as [U] and will be rejected on review.

## Never assert from memory

Lot size, expiry day, strike interval, tick size, and tradingsymbol format must
come from a live instrument dump or a dated circular. Every single time.
Never fabricate a tradingsymbol. If you do not have the dump, say so and stop.

## Write permissions

- Agents write ONLY inside inbox/<your-name>/. Nowhere else. Ever.
- Never edit 00_CORRECTIONS_LEDGER.md, 01_TASK_REGISTER.md, README.md, or
  anything in a numbered folder. Propose; the operator promotes.
- One topic per file. Filename: lowercase-with-hyphens.md, no spaces, no "&".
- Every file starts with the YAML front matter block from _TEMPLATE.md.

## Hard prohibitions

- No order placement, no order modification, no GTT create/modify/delete.
- Never print, echo, or commit an api_key, api_secret, access_token,
  request_token, password, account ID, or capital figure.
- No paid subscription, no spend of any amount, without explicit approval.
- If a task seems to require any of the above, stop and ask.

## Lanes

- Gemini Spark: Zerodha Kite market data, instrument dumps, historical candles.
  Does not author Tradetron schema.
- Genspark SuperAgent: Tradetron MCP tools, keyword schema, strategy markdown.
  Does not assert market parameters; requests them from Spark's outputs.
- Claude: review, specification, contradiction hunting. Writes specs, not data.
- Operator (Rishabh): executes in Tradetron, promotes inbox files, holds all
  credentials. The only actor permitted to spend money or place trades.

## Definition of done

A file is done when: front matter complete, every claim tagged, every [V] claim
carries a source and a date, contradictions with the ledger listed explicitly,
and it ends with what you could not verify and why.