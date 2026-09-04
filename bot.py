import time
import re
from datetime import datetime, timezone
from telethon import TelegramClient, events
import MetaTrader5 as mt5

from config import (
    TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER,
    CHANNEL_USERNAME, MT5_LOGIN_ID, MT5_PASSWORD, MT5_SERVER,
    LOT_SIZE, DEVIATION, POLLING_INTERVAL
)


# Duplicate Message Protection

TRADED_MESSAGE_IDS = set()  # Store message IDs already traded
MAX_MESSAGE_AGE_SECONDS = 300  # Only trade messages from the last 5 minutes

# global variables to store trade tickets and their targets
trade_tickets = {}
tp_levels = {}

client = TelegramClient('session_name', TELEGRAM_API_ID, TELEGRAM_API_HASH)

def initialize_mt5():
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
        return False

    authorized = mt5.login(MT5_LOGIN_ID, password=MT5_PASSWORD, server=MT5_SERVER)
    if not authorized:
        print("Failed to connect to trade account. Check credentials and connectivity.")
        return False

    print("Connected to MT5 account:", MT5_LOGIN_ID)
    return True

def parse_signal(message_text):
    """
    Given the format:
    SIGNAL ALERT

    SELL XAUUSD 2664.2

    🤑TP1: 2663.0
    🤑TP2: 2661.5
    🤑TP3: 2658.0
    🔴SL: 2670.0
    """
    direction_pattern = r"(BUY|SELL)\s+([A-Za-z0-9]+)\s+(\d+\.\d+)"
    direction_match = re.search(direction_pattern, message_text, re.IGNORECASE)
    if not direction_match:
        return None

    direction = direction_match.group(1).upper()
    symbol = direction_match.group(2).upper()
    entry = float(direction_match.group(3))

    tp_pattern = r"TP\d+:\s*(\d+\.\d+)"
    tp_matches = re.findall(tp_pattern, message_text, re.IGNORECASE)
    if len(tp_matches) < 3:
        return None
    tp1 = float(tp_matches[0])
    tp2 = float(tp_matches[1])
    tp3 = float(tp_matches[2])

    sl_pattern = r"SL:\s*(\d+\.\d+)"
    sl_match = re.search(sl_pattern, message_text, re.IGNORECASE)
    if not sl_match:
        return None
    sl = float(sl_match.group(1))

    return {
        'direction': direction,
        'symbol': symbol,
        'entry': entry,
        'sl': sl,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3
    }

def send_order(symbol, direction, entry, sl, tp):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found, please check symbol availability.")
        return None

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select {symbol}")
            return None

    symbol_tick = mt5.symbol_info_tick(symbol)
    if symbol_tick is None:
        print(f"No tick data for symbol {symbol}, cannot place order.")
        return None

    if direction == 'BUY':
        order_type = mt5.ORDER_TYPE_BUY
        order_price = symbol_tick.ask
    else:
        order_type = mt5.ORDER_TYPE_SELL
        order_price = symbol_tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": order_price,
        "sl": sl,
        "tp": tp,
        "deviation": DEVIATION,
        "magic": 123456,
        "comment": "Telegram Signal",
        "type_filling": mt5.ORDER_FILLING_FOK
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Trade execution failed, retcode={result.retcode} for TP {tp}")
        return None
    else:
        print(f"Trade executed successfully for TP {tp}, ticket: {result.order}")
        return result.order

def modify_trade_stop(tickets, new_sl):
    for ticket in tickets:
        position = None
        all_positions = mt5.positions_get()
        if all_positions:
            for pos in all_positions:
                if pos.ticket == ticket:
                    position = pos
                    break

        if position is None:
            continue

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Stop loss updated for ticket {ticket} to {new_sl}")
        else:
            print(f"Failed to update SL for ticket {ticket}, retcode={result.retcode}")

def monitor_trades(direction, tp_levels, trade_tickets):
    tp1_closed = False
    tp2_closed = False
    tp1 = tp_levels['tp1']
    tp2 = tp_levels['tp2']
    tp3 = tp_levels['tp3']

    ticket_tp1 = trade_tickets['tp1']
    ticket_tp2 = trade_tickets['tp2']
    ticket_tp3 = trade_tickets['tp3']

    while True:
        open_positions = mt5.positions_get()
        open_tickets = [p.ticket for p in open_positions] if open_positions else []

        if not tp1_closed:
            if ticket_tp1 not in open_tickets:
                tp1_closed = True
                print("TP1 order closed, adjusting SL of TP2 and TP3 orders...")
                new_sl = tp1 - ((tp1 * 0.0001) if 'XAU' in tp_levels['symbol'] else 0.1)
                modify_trade_stop([ticket_tp2, ticket_tp3], new_sl)

        if tp1_closed and not tp2_closed:
            if ticket_tp2 not in open_tickets:
                tp2_closed = True
                print("TP2 order closed, adjusting SL of TP3 order...")
                new_sl = tp2 - ((tp2 * 0.0001) if 'XAU' in tp_levels['symbol'] else 0.1)
                modify_trade_stop([ticket_tp3], new_sl)

        if ticket_tp3 not in open_tickets:
            print("TP3 order closed or no more trades open. Stopping monitor.")
            break

        time.sleep(POLLING_INTERVAL)

@client.on(events.NewMessage(chats=CHANNEL_USERNAME))
async def handler(event):
    message = event.message.message
    message_id = event.message.id
    message_date = event.message.date

    # Prevent duplicate trades
    if message_id in TRADED_MESSAGE_IDS:
        print(f"⚠️ Message ID {message_id} already traded (duplicate). Ignoring.")
        return

    # Safety check, ignore messages that are too old
    current_time = datetime.now(timezone.utc)
    message_age = (current_time - message_date).total_seconds()

    if message_age > MAX_MESSAGE_AGE_SECONDS:
        print(f"⚠️ Message is {message_age} seconds old (max: {MAX_MESSAGE_AGE_SECONDS}s). Ignoring old signal.")
        return

    signal = parse_signal(message)
    if signal:
        print(f"✅ Signal received: {signal}")
        print(f"   Message ID: {message_id}, Age: {message_age}s")

        # Mark message as traded before execution to prevent re-entry
        TRADED_MESSAGE_IDS.add(message_id)

        tp_levels.clear()
        tp_levels['symbol'] = signal['symbol']
        tp_levels['tp1'] = signal['tp1']
        tp_levels['tp2'] = signal['tp2']
        tp_levels['tp3'] = signal['tp3']

        trade_tickets.clear()

        tp1_ticket = send_order(signal['symbol'], signal['direction'], signal['entry'], signal['sl'], signal['tp1'])
        if tp1_ticket is None:
            print("❌ Failed to execute TP1 order. Aborting trade sequence.")
            TRADED_MESSAGE_IDS.discard(message_id)
            return
        trade_tickets['tp1'] = tp1_ticket

        tp2_ticket = send_order(signal['symbol'], signal['direction'], signal['entry'], signal['sl'], signal['tp2'])
        if tp2_ticket is None:
            print("❌ Failed to execute TP2 order. Aborting trade sequence.")
            TRADED_MESSAGE_IDS.discard(message_id)
            return
        trade_tickets['tp2'] = tp2_ticket

        tp3_ticket = send_order(signal['symbol'], signal['direction'], signal['entry'], signal['sl'], signal['tp3'])
        if tp3_ticket is None:
            print("❌ Failed to execute TP3 order. Aborting trade sequence.")
            TRADED_MESSAGE_IDS.discard(message_id)
            return
        trade_tickets['tp3'] = tp3_ticket

        print(f"✅ All 3 orders executed. Starting monitoring...")
        monitor_trades(signal['direction'], tp_levels, trade_tickets)
    else:
        print(f"⚠️ Message doesn't contain valid signal format.")

if __name__ == "__main__":
    if not initialize_mt5():
        exit("MT5 initialization failed.")

    with client:
        print("✅ Listening for signals...")
        print(f"   Max message age: {MAX_MESSAGE_AGE_SECONDS} seconds")
        print("   Duplicate protection: ENABLED")
        client.run_until_disconnected()
