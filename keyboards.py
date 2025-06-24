from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
import texts

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(texts.JOKE_BUTTON_TEXT)], 
        [KeyboardButton(texts.DICE_BUTTON_TEXT)],
        [KeyboardButton(texts.TRUTH_OR_DARE_BUTTON_TEXT)] 
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_truth_or_dare_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(texts.TRUTH_BUTTON_TEXT, callback_data='truth_or_dare_truth'),
            InlineKeyboardButton(texts.DARE_BUTTON_TEXT, callback_data='truth_or_dare_dare')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)