import os
import json
import warnings
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import CallbackQueryHandler
from textblob import TextBlob
from flask import Flask, request

# Suppress TextBlob SyntaxWarning
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Initialize Flask app
app = Flask(__name__)

# Your bot's token
BOT_TOKEN = os.getenv('6892664579:AAFyjH9E1UPjUgnpOyjJMKoTGWkQ3y5ZJXY')  # Set bot token as an environment variable

# Load product data from 'post.json'
with open('post.json', 'r') as f:
    products = json.load(f)

# Function to perform sentiment analysis on text
def analyze_sentiment(text):
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity

    if sentiment_score > 0:
        return "Positive"
    elif sentiment_score < 0:
        return "Negative"
    return None

# AI-based recommendation function (simple keyword-based matching)
def recommend_product(user_query):
    recommendations = []
    for product in products:
        if user_query.lower() in product['title'].lower():
            recommendations.append(product)
    return recommendations[:3] if recommendations else None

# Function to send "Made in India" message with icon
async def send_made_in_india(update: Update):
    made_in_india_message = "🇮🇳 **Made in India** 🇮🇳"
    await update.message.reply_text(made_in_india_message, parse_mode='Markdown')

# Function to handle product search
async def handle_product_search(update: Update, context: CallbackContext):
    await update.message.reply_chat_action("typing")
    product_name = update.message.text.lower()

    # AI-based recommendation logic
    recommended_products = recommend_product(product_name)

    if recommended_products:
        keyboard = []
        for product in recommended_products:
            keyboard.append([InlineKeyboardButton(product['title'], callback_data=product['title'])])

        await update.message.reply_text(
            '✌️ **Did you mean one of these products?**\nSelect a product to view more details!',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        await send_made_in_india(update)
    else:
        await update.message.reply_text('⚠️ **No matching products found**. Please try a different name.', parse_mode='Markdown')

# Function to show the selected product details when the user clicks on a suggestion
async def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    selected_product_title = query.data
    
    await query.answer()  # Answer the callback query to remove loading spinner
    await query.message.reply_chat_action("typing")

    # Find the selected product by matching title
    selected_product = next((product for product in products if product['title'] == selected_product_title), None)

    if selected_product:
        order_button = InlineKeyboardButton("🛒 Order Now", url=selected_product['link'])
        keyboard = InlineKeyboardMarkup([[order_button]])

        product_details = (
            f"<b>{selected_product['title']}</b>\n\n"
            f"⭐ <b>Rating:</b> {selected_product['rating']} ⭐\n"
            f"💎 <b>MRP:</b> ₹{selected_product['mrp']}\n"
            f"💥 <b>Discount:</b> {selected_product['discount']}%\n\n"
            f"✨ Click below to order this awesome product! 🛍️"
        )

        sentiment = analyze_sentiment(selected_product['title'])
        
        if sentiment:
            sentiment_message = f"Sentiment: {sentiment} 😄"
            await query.message.reply_text(sentiment_message)

        if 'image_url' in selected_product and selected_product['image_url']:
            await query.message.reply_photo(
                selected_product['image_url'], 
                caption="Here is the product image 🖼️", 
                reply_markup=keyboard
            )
        else:
            await query.message.reply_text(
                "No image uploaded by the admin for this product.",
                reply_markup=keyboard
            )

        await query.message.reply_text(product_details, reply_markup=keyboard, parse_mode='HTML')
        await send_made_in_india(query)
    else:
        await query.message.reply_text("⚠️ Sorry, we couldn't find the product details.")

# Function to handle any unrecognized message
async def unknown(update: Update, context: CallbackContext):
    await update.message.reply_text("❓ Sorry, I didn't understand that. Please type a product name to search.", parse_mode='Markdown')

# Flask route to handle the webhook
@app.route('/' + os.getenv('BOT_TOKEN'), methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = Update.de_json(json.loads(json_str), application.bot)
    application.process_update(update)
    return 'OK'

# Main function to set up the bot
def main():
    global application
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_search))
    application.add_handler(CallbackQueryHandler(button_click))  # Handle button clicks

    # Start Flask app
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
