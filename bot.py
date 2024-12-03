from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import CallbackQueryHandler
from textblob import TextBlob
import json

# Your bot's token
BOT_TOKEN = '6892664579:AAFyjH9E1UPjUgnpOyjJMKoTGWkQ3y5ZJXY'

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
    # Neutral sentiment is not shown
    return None

# AI-based recommendation function (simple keyword-based matching)
def recommend_product(user_query):
    recommendations = []
    for product in products:
        # Match the product title with the user's query (case-insensitive)
        if user_query.lower() in product['title'].lower():
            recommendations.append(product)
    return recommendations[:3] if recommendations else None

# Function to send "Made in India" message with icon
async def send_made_in_india(update: Update):
    made_in_india_message = "🇮🇳 **Made in India** 🇮🇳"
    await update.message.reply_text(made_in_india_message, parse_mode='Markdown')

# Function to start the bot
async def start(update: Update, context: CallbackContext):
    # Welcome message
    welcome_message = (
        "🎉 **Welcome to the Smart Product Finder!** 🎉\n\n"
        "🤖 I'm here to help you find your perfect product. "
        "Simply type the product name (e.g., 'realme') and I'll assist you.\n\n"
        "🌟 Let's get started! Type a product name to search."
    )
    # Send the welcome message and Made in India text
    await update.message.reply_text(welcome_message, parse_mode='Markdown')
    await send_made_in_india(update)

# Function to handle product search
async def handle_product_search(update: Update, context: CallbackContext):
    # Show typing action to indicate the bot is processing
    await update.message.reply_chat_action("typing")

    product_name = update.message.text.lower()

    # AI-based recommendation logic
    recommended_products = recommend_product(product_name)

    if recommended_products:
        # If there are recommendations, present them to the user
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
    
    # Show typing action to indicate the bot is processing
    await query.answer()  # Answer the callback query to remove loading spinner
    await query.message.reply_chat_action("typing")

    # Find the selected product by matching title
    selected_product = next((product for product in products if product['title'] == selected_product_title), None)

    if selected_product:
        # Prepare the inline keyboard button for order
        order_button = InlineKeyboardButton("🛒 Order Now", url=selected_product['link'])
        keyboard = InlineKeyboardMarkup([[order_button]])

        # Prepare the message with product details
        product_details = (
            f"<b>{selected_product['title']}</b>\n\n"
            f"⭐ <b>Rating:</b> {selected_product['rating']} ⭐\n"
            f"💎 <b>MRP:</b> ₹{selected_product['mrp']}\n"
            f"💥 <b>Discount:</b> {selected_product['discount']}%\n\n"
            f"✨ Click below to order this awesome product! 🛍️"
        )

        # Perform sentiment analysis on the product title or description
        sentiment = analyze_sentiment(selected_product['title'])
        
        if sentiment:  # Only show sentiment if it is not None (i.e., not neutral)
            sentiment_message = f"Sentiment: {sentiment} 😄"
            await query.message.reply_text(sentiment_message)
        
        # Check if the product has an image URL
        if 'image_url' in selected_product and selected_product['image_url']:
            # Send the image if available
            await query.message.reply_photo(
                selected_product['image_url'], 
                caption="Here is the product image 🖼️", 
                reply_markup=keyboard
            )
        else:
            # If no image is available, send a fallback message
            await query.message.reply_text(
                "No image uploaded by the admin for this product.",
                reply_markup=keyboard
            )

        # Send the product details and sentiment analysis result
        await query.message.reply_text(product_details, reply_markup=keyboard, parse_mode='HTML')

        # Send the "Made in India" message with icon
        await send_made_in_india(query)
    else:
        # If the product is not found in the list
        await query.message.reply_text("⚠️ Sorry, we couldn't find the product details.")

# Function to handle any unrecognized message
async def unknown(update: Update, context: CallbackContext):
    await update.message.reply_text("❓ Sorry, I didn't understand that. Please type a product name to search.", parse_mode='Markdown')

# Main function to set up the bot
def main():
    # Set up the Application and Dispatcher
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_search))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))  # Handle unknown commands
    application.add_handler(CallbackQueryHandler(button_click))  # Handle button clicks

    # Start polling for updates
    application.run_polling()

if __name__ == '__main__':
    main()
