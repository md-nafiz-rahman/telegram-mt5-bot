# Telegram-to-MT5 Signal Trading Bot

A Python bot that listens for trade signals in a Telegram channel and automatically executes them in MetaTrader 5, using a scaled take-profit strategy with automatic trailing stop-loss.

> ⚠️ **Disclaimer:** This project was built for personal learning and experimentation with API integration and automation. It is not financial advice, and automated trading carries significant financial risk.
>
> **This repository is for demonstration purposes only. It is not intended to be installed and run using real trading account. It was built and tested using a demo trading account.**

## How It Works

1. Listens to a specified Telegram channel using Telethon
2. Parses incoming messages for a structured signal format (direction, symbol, entry, stop loss, three take-profit levels)
3. Opens three separate trades per signal, each targeting a different take-profit level (TP1, TP2, TP3)
4. Automatically trails the stop loss forward as each target is hit moving remaining trades' stop loss to just behind the most recently closed target
5. Continuously polls MT5 for position status while the bot is running

## Requirements to Run

- MetaTrader 5 must be installed and running on the same machine as the script, since the `MetaTrader5` Python package connects to the locally running MT5 terminal it does not connect to a remote server directly.
- The machine running the script must stay powered on and connected to the internet continuously, since the bot listens for signals and monitors open trades in real time via a persistent loop. If the script stops running, incoming signals won't be caught and open trades will no longer have their stop loss trailed automatically.

## Strategy Logic

This implements a common scale-out risk management approach: rather than closing a full position at one target, splitting it across three targets locks in partial profit progressively while letting the remaining position run, with the stop loss following behind to protect gained profit.

## Tech Stack

- Python
- Telethon (Telegram API client)
- MetaTrader5 Python package

## Setup

1. Clone the repo
2. Install dependencies:
```bash
   pip install -r requirements.txt
```
3. Copy `config.example.py` to `config.py` and fill in your own Telegram API credentials and MT5 login details
4. Run the bot:
```bash
   python bot.py
```

## Signal Format Expected

SELL XAUUSD 2664.2
🤑TP1: 2663.0
🤑TP2: 2661.5
🤑TP3: 2658.0
🔴SL: 2670.0


## Limitations / Possible Improvements
- Requires the host machine to remain on and connected at all times, no cloud or VPS deployment currently
- No reconnect logic if the Telegram or MT5 connection drops
- Position monitoring uses simple polling rather than event-driven updates
- No logging to file, currently only prints to console