import logging
import re
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler, ConversationHandler
)

import config
import texts
import keyboards
import db
import gemini_utils

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CHOOSING_ACTION = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Ну привет, {user.mention_html()}. {texts.START_MESSAGE}", # Немного в стиле Шмы
        reply_markup=keyboards.get_main_keyboard(),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(texts.HELP_MESSAGE, reply_markup=keyboards.get_main_keyboard())

async def tell_joke_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    joke = await gemini_utils.get_gemini_joke()
    await update.message.reply_text(joke)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text_original = update.message.text # Сохраняем оригинальный текст для Gemini
    text_lower = text_original.lower().strip()

    if text_lower == "шма, отключись":
        if db.mute_user(user_id):
            await update.message.reply_text(texts.USER_MUTED_MSG)
        else:
            await update.message.reply_text(texts.ALREADY_MUTED_MSG)
        return
    elif text_lower == "шма, включись":
        if db.unmute_user(user_id):
            await update.message.reply_text(texts.USER_UNMUTED_MSG)
        else:
            await update.message.reply_text(texts.ALREADY_UNMUTED_MSG)
        return

    if text_lower == "шма, расскажи анекдот":
        await tell_joke_action(update, context)
        return

    if db.is_user_muted(user_id):
        return
    
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    gemini_response = await gemini_utils.get_gemini_response(text_original) # Передаем оригинальный текст
    if gemini_response:
        await update.message.reply_text(gemini_response)


async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await context.bot.send_dice(chat_id=chat_id)


async def truth_or_dare_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message and update.message.text == texts.TRUTH_OR_DARE_BUTTON_TEXT:
        await update.message.reply_text(
            texts.TRUTH_OR_DARE_PROMPT,
            reply_markup=keyboards.get_truth_or_dare_inline_keyboard()
        )
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            text=texts.TRUTH_OR_DARE_PROMPT,
            reply_markup=keyboards.get_truth_or_dare_inline_keyboard()
        )
    return CHOOSING_ACTION


async def truth_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Ща я тебе такую правду выкачу, обоср*шься... Ищу самый мерзкий вопрос...")
    
    await context.bot.send_chat_action(chat_id=query.message.chat_id, action="typing")
    question = await gemini_utils.get_truth_question()

    if question:
        # Теперь Шма задает только вопрос
        response_text = f"❓ **Ну что, готов(а) к правде, ничтожество?**\n\n{question}\n\nОтвечай давай, не тяни кота за яйца." 
        await query.edit_message_text(text=response_text, parse_mode='Markdown') # Markdown для выделения
    else:
        await query.edit_message_text(text=texts.ERROR_TRUTH_MSG) 
    
    return ConversationHandler.END

async def dare_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Так, сейчас я тебе такое задание придумаю, будешь долго отмываться... Ха-ха.") 

    await context.bot.send_chat_action(chat_id=query.message.chat_id, action="typing")
    dare_task = await gemini_utils.get_dare_task()
    
    response_text = f"🔥 **Ну что, слабак, готов(а) к действию?**\n\n{dare_task}\n\nВыполняй, или я тебя прокляну!"
    await query.edit_message_text(text=response_text, parse_mode='Markdown')
    
    return ConversationHandler.END

async def cancel_truth_or_dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    cancel_message = "Пф, слабак. Слился, как обычно. Ничего другого и не ожидала." 
    if query:
        await query.answer()
        await query.edit_message_text(text=cancel_message)
    elif update.message:
        await update.message.reply_text(cancel_message, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.GEMINI_API_KEY:
        logger.error("Не найден TELEGRAM_BOT_TOKEN или GEMINI_API_KEY в .env файле.")
        return

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.Regex(f"^{re.escape(texts.JOKE_BUTTON_TEXT)}$"), tell_joke_action))
    application.add_handler(MessageHandler(filters.Regex(f"^{re.escape(texts.DICE_BUTTON_TEXT)}$"), roll_dice))

    tod_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f"^{re.escape(texts.TRUTH_OR_DARE_BUTTON_TEXT)}$"), truth_or_dare_start)],
        states={
            CHOOSING_ACTION: [
                CallbackQueryHandler(truth_chosen, pattern="^truth_or_dare_truth$"),
                CallbackQueryHandler(dare_chosen, pattern="^truth_or_dare_dare$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_truth_or_dare)],
    )
    application.add_handler(tod_conv_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот Шма (злая версия) запускается...")
    application.run_polling()

if __name__ == "__main__":
    db.init_db()
    main()