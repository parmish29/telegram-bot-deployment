from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import re
from urllib.parse import unquote

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets API Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name('Credentials.json', SCOPE)
client = gspread.authorize(CREDS)

# Google Sheet IDs
goods_sheet_id = '18f8m74G93nW-yugulYKYdrIWPBAPV-rP671DH7LRyYE'  # Replace with your actual Google Sheet ID for the goods sheet
movies_sheet_id = '1KG5bQxC0Y7n8SFuyEBSnJwGTrbSu7TzEkQdE8YbGiqk'  # Replace with your actual Google Sheet ID for the movies sheet

# Load movie sheet for retrieving movie links
try:
    movies_sheet = client.open_by_key(movies_sheet_id).sheet1
    goods_sheet = client.open_by_key(goods_sheet_id).sheet1  # Make sure to add goods_sheet
    logger.info("Sheets accessed successfully")
except gspread.SpreadsheetNotFound:
    logger.error("Spreadsheet not found. Please check the Sheet IDs and permissions.")

# Helper function to clean and decode text for matching
def clean_text(text):
    text = unquote(str(text))  # Decode URL-encoded characters like %20
    return re.sub(r'[^A-Za-z0-9\s]+', '', text).strip().lower()

# Function to find movie link based on user query
def find_movie_link(query):
    try:
        movie_data = movies_sheet.get_all_records()
    except Exception as e:
        logger.error(f"Error reading movie data: {e}")
        return None

    query_cleaned = clean_text(query)
    for movie in movie_data:
        if 'File Name' in movie and 'URL' in movie:
            cleaned_name = clean_text(movie['File Name'])
            if query_cleaned in cleaned_name:
                return movie['URL']  # Return the first matching movie link
    return None

# Function to verify if a transaction ID is valid with added logging for debugging
def is_transaction_id_valid(transaction_id):
    try:
        # Get all transaction IDs in the "Paid Transaction" table (column E)
        paid_transaction_ids = goods_sheet.col_values(5)  # Column E has "Transaction ID"
        
        # Debugging: Log the values retrieved from the sheet
        logger.info(f"Retrieved transaction IDs: {paid_transaction_ids}")
        
        # Check if the provided transaction ID is in the list
        return transaction_id in paid_transaction_ids
    except Exception as e:
        logger.error(f"Error accessing Google Sheet for transaction IDs: {e}")
        return False
# Function to log verified transaction in "Latest Verified Sessions" and remove it from "Paid Transaction"
def log_verified_session(transaction_id, user_id):
    try:
        # Dynamically find the next available row in the "Latest Verified Sessions" table
        latest_sessions = goods_sheet.get_all_values()  # Fetch all rows to determine the next available row
        row_num = len(latest_sessions) + 1  # Determine next empty row after existing data

        # Update the next available row with the transaction ID, "Verified" status, and user ID
        goods_sheet.update(f'A{row_num}:C{row_num}', [[transaction_id, "Verified", user_id]])

        # Find and remove the transaction ID from the "Paid Transaction" table
        paid_transactions = goods_sheet.get_all_values()  # Fetch all rows for both tables
        for i, row in enumerate(paid_transactions, start=1):
            if row[4] == transaction_id:  # Assuming transaction ID is in column E
                goods_sheet.delete_rows(i)  # Delete the row containing the verified transaction ID
                break

        return True
    except Exception as e:
        logger.error(f"Error logging verified session: {e}")
        return False


# /start command to initiate bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! Please enter the movie or show name you are searching for.")

# Handle movie search based on user input
async def handle_movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.message.text.strip()
    movie_link = find_movie_link(query)
    if movie_link:
        await update.message.reply_text(
            "This movie link is available! Please pay 20 rupees on UPI ID (9991957029@ybl) "
            "and reply with /verify_movie <Transaction ID>."
        )
        # Store the movie link in context for use after verification
        context.user_data["pending_movie_link"] = movie_link
    else:
        await update.message.reply_text("Sorry, no matches found. Try a different title or check spelling.")

# Verify the transaction ID
async def verify_movie_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a transaction ID with the /verify_movie command.")
        return

    transaction_id = context.args[0].strip()
    user_id = update.message.from_user.id
    if is_transaction_id_valid(transaction_id):
        # Log the verified transaction in "Latest Verified Sessions"
        if log_verified_session(transaction_id, user_id):
            movie_link = context.user_data.get("pending_movie_link")
            if movie_link:
                await update.message.reply_text(f"Transaction verified! Here is your link: {movie_link}")
                context.user_data["pending_movie_link"] = None  # Clear link after use
            else:
                await update.message.reply_text("No pending movie link found. Try searching for a movie again.")
        else:
            await update.message.reply_text("Failed to log your session. Please try again later.")
    else:
        await update.message.reply_text("Transaction verification failed. Please check your ID and try again.")

# Main function to initialize and run the bot
def main():
    bot_token = "8126846654:AAFCiat4c1xKpxzlZq5m5eEKDeW-q7dkb-I"  # Replace with your bot token
    app = Application.builder().token(bot_token).build()

    # Add handlers for commands and messages
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("verify_movie", verify_movie_transaction))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_movie_search))
    app.add_handler(MessageHandler(filters.Regex(r'(?i)\bhi\b'), start))  # Start when user says "hi"

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
