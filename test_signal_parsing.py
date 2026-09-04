import sys
sys.path.insert(0, '.')
from bot import parse_signal

print("=" * 60)
print("TEST 1: Valid signal with all required fields")
print("=" * 60)

test_message_1 = """
SIGNAL ALERT

SELL XAUUSD 2664.2

🤑TP1: 2663.0
🤑TP2: 2661.5
🤑TP3: 2658.0
🔴SL: 2670.0
"""

signal = parse_signal(test_message_1)
if signal:
    print("✅ Signal parsed successfully:")
    print(f"   Direction: {signal['direction']}")
    print(f"   Symbol: {signal['symbol']}")
    print(f"   Entry: {signal['entry']}")
    print(f"   TP1: {signal['tp1']}")
    print(f"   TP2: {signal['tp2']}")
    print(f"   TP3: {signal['tp3']}")
    print(f"   SL: {signal['sl']}")
else:
    print("❌ Failed to parse signal (should have succeeded)")

print("\n" + "=" * 60)
print("TEST 2: Invalid signal - missing TP3")
print("=" * 60)

test_message_2 = """
BUY EURUSD 1.0800
TP1: 1.0850
TP2: 1.0900
SL: 1.0750
"""

signal2 = parse_signal(test_message_2)
if signal2 is None:
    print("✅ Correctly rejected incomplete signal (no TP3)")
else:
    print("❌ Should have rejected incomplete signal")

print("\n" + "=" * 60)
print("TEST 3: Invalid signal - missing SL")
print("=" * 60)

test_message_3 = """
BUY GBPUSD 1.2750
TP1: 1.2800
TP2: 1.2850
TP3: 1.2900
"""

signal3 = parse_signal(test_message_3)
if signal3 is None:
    print("✅ Correctly rejected signal (no SL)")
else:
    print("❌ Should have rejected signal without SL")

print("\n" + "=" * 60)
print("TEST 4: Valid signal - BUY instead of SELL")
print("=" * 60)

test_message_4 = """
BUY EURUSD 1.0900

TP1: 1.0950
TP2: 1.1000
TP3: 1.1050
SL: 1.0850
"""

signal4 = parse_signal(test_message_4)
if signal4 and signal4['direction'] == 'BUY':
    print("✅ Signal parsed correctly as BUY:")
    print(f"   Direction: {signal4['direction']}")
    print(f"   Symbol: {signal4['symbol']}")
    print(f"   Entry: {signal4['entry']}")
else:
    print("❌ Failed to parse BUY signal")

print("\n" + "=" * 60)
print("TEST 5: Invalid signal - no direction/symbol")
print("=" * 60)

test_message_5 = """
Some random message
TP1: 1.0850
TP2: 1.0900
TP3: 1.0950
SL: 1.0750
"""

signal5 = parse_signal(test_message_5)
if signal5 is None:
    print("✅ Correctly rejected random message")
else:
    print("❌ Should have rejected message with no BUY/SELL")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
