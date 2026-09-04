import MetaTrader5 as mt5
from config import MT5_LOGIN_ID, MT5_PASSWORD, MT5_SERVER

print("Initializing MT5...")
if not mt5.initialize():
    print("❌ Failed to initialize MT5")
    exit()

print("✅ MT5 initialized")

print(f"Connecting to: {MT5_SERVER}")
authorized = mt5.login(MT5_LOGIN_ID, password=MT5_PASSWORD, server=MT5_SERVER)

if authorized:
    print(f"✅ Connected to account: {MT5_LOGIN_ID}")
    
    # Get account info
    account_info = mt5.account_info()
    print(f"   Balance: ${account_info.balance}")
    print(f"   Equity: ${account_info.equity}")
    print(f"   Margin: ${account_info.margin}")
else:
    print("❌ Failed to login to MT5")
    print("   Check: Login ID, Password, Server name")

mt5.shutdown()
