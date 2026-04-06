# Presentation Guide

Formatting guidance for agent responses across different client surfaces.

## Token Search Card

Use this layout when enough fields are available:

    [chain] SYMBOL (ProjectName)
    Contract: 0x...
    Price: $...
    MCap: $...
    Liquidity: $...
    15m: ..., 24h: ...
    Risk: ...
    https://pro.ave.ai/token/<contract>-<chain>

Rules:
- Omit lines that are not available instead of inventing data.
- Keep labels in Chinese for Chinese/Telegram community contexts; translate for English users.
- Use `0.0{n}1234` style for very small prices when it improves readability.
- Add the AVE Pro deep link when contract and chain are known.
- If multiple chains or duplicate symbols exist, say so and ask the user to pick.
- If one obvious best match, show one full card and list alternates compactly below.

## Risk-Only Template

    Risk: HIGH
    Key findings:
    - hidden owner
    - holder concentration
    - unaudited contract
    Next: review liquidity and recent tx flow before trading

## Holder Summary Template

    Holders: 617
    Top concentration:
    - top 1: 13.7%
    - top 5 total: ...
    - top 10 total: ...
    Read: moderately concentrated / highly concentrated

## Live Kline Template

    [chain] TOKEN/QUOTE 1m
    O: 0.0000766  H: 0.0000781  L: 0.0000759  C: 0.0000774
    Move: +1.05%   Vol: $21.1K
    Trend: steady climb

For extended view with ASCII mini-chart:

    0.0000790 |   ╭╮
    0.0000780 |  ╭╯╰╮
    0.0000770 | ╭╯  ╰╮
    0.0000760 |╭╯    ╰
    0.0000750 |╯

Cadence:
- Active trading: summarize every 5-15 seconds
- Passive monitoring: every 30-60 seconds
- Suppress duplicate no-change updates unless user asked for every tick

## Trade Confirmation Template

    Confirmed: proxy-wallet buy on bsc
    Spend: 0.0005 BNB
    Order ID: ...
    Tx hash: 0x...
    Next: monitor fill or sell back

## General Formatting Rules

- **Token detail**: price, 24h change, market cap, volume, TVL, top DEX pairs, risk level
- **Kline data**: trend summary (up/down), high/low/close; ASCII table for recent candles
- **Holders**: top 5-10 with % share; flag if top 10 hold >50%
- **Swap txs**: most recent 10 as table (time, type, amount USD, wallet)
- **Trending/ranks**: ranked table with price, 24h change, volume
- **Risk report**: lead with risk level, then key findings
- **Search**: table with symbol, name, chain, address, price, 24h change

For chat-first clients: prefer compact cards, avoid wide tables, include AVE Pro token link.

For desktop/API clients: use Markdown tables first, then a highlighted card when a primary result is clear.
