
import logging
from telegram import (
    Bot,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)

# -- Bot and its token
token = 'TOKEN'
bot = Bot(token)

# -- States and CBD --

FIRST, SECOND, THIRD = range(3)
ORDER, OFFER, SEND, CANCEL = range(4)

# Put yours
admin_id = 'some id'

# -- Inline Keyboards --

start_keyboard = [
    [
        InlineKeyboardButton("Сделать заказ", callback_data=str(ORDER)),
        InlineKeyboardButton("Предложить контент", callback_data=str(OFFER)),
    ]
]

send_button = [
    [
        InlineKeyboardButton("Отправить так", callback_data=str(SEND)),
    ],
    [
        InlineKeyboardButton("Отменить", callback_data=str(CANCEL)),
    ]
]

cancel_button = [
    [
        InlineKeyboardButton("Отменить", callback_data=str(CANCEL)),
    ]
]

# -- Main functions --

def start(update: Update, context: CallbackContext) -> None:
    reply_markup = InlineKeyboardMarkup(start_keyboard)
    data = context.chat_data
    msg = update.message.reply_text('Что бы Вы хотели сделать?', reply_markup=reply_markup)
    data.update({'m_id': msg.message_id})
    return FIRST

def order(update: Update, context: CallbackContext) -> None:
    data = context.chat_data
    data.update({'type': 'order'})
    reply_markup = InlineKeyboardMarkup(cancel_button)
    query = update.callback_query
    query.answer()
    query.edit_message_text('Опишите Ваш заказ (текст или медиа)', reply_markup=reply_markup)
    return SECOND

def collect_order(update: Update, context: CallbackContext) -> None:
    reply_markup = InlineKeyboardMarkup(send_button)
    data = context.chat_data
    if data.get('order') == None:
        data.update({'order': [update.message]})
    else:
        data.get('order').append(update.message)
    if data.get('m_id') != None:
        bot.delete_message(update.message.from_user.id, data.get('m_id'))
    msg = update.message.reply_text('Можете добавить что-то ещё', reply_markup=reply_markup)
    data.update({'m_id': msg.message_id})
    return THIRD

def offer(update: Update, context: CallbackContext) -> None:
    data = context.chat_data
    data.update({'type': 'offer'})
    query = update.callback_query
    query.answer()
    query.edit_message_text('Отправьте мне материалы, которые бы Вы хотели предложить')
    return SECOND

def send_order(update: Update, context: CallbackContext) -> None:
    data = context.chat_data
    sending(data.get('order'), data.get('type'))
    data.pop('order')
    query = update.callback_query
    query.answer()
    reply_markup = InlineKeyboardMarkup(start_keyboard)
    if data.get('type') == 'order':
        msg = query.edit_message_text('Заказ принят. Можете заказать ещё', reply_markup=reply_markup)
        data.update({'m_id': msg.message_id})
    elif data.get('type') == 'offer':
        msg = query.edit_message_text('Предложение принято. Можете сделать что-то ещё', reply_markup=reply_markup)
        data.update({'m_id': msg.message_id})
    return FIRST

def warn(update: Update, context: CallbackContext) -> None:
    reply_markup = InlineKeyboardMarkup(start_keyboard)
    data = context.chat_data
    bot.delete_message(update.message.from_user.id, data.get('m_id'))
    data.pop('m_id')
    update.message.reply_text('Воспользуйтесь кнопками под моим ответом, чтобы начать работу со мной')
    update.message.reply_text('Что бы Вы хотели сделать?', reply_markup=reply_markup)

def cancel(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    query.edit_message_text('Вы отменили действие. Чтобы начать снова, вызовите меня командой /start')
    return ConversationHandler.END

# -- Sending order to admin (clumsily) --

def sending(messages, type):
    if type == 'order':
        bot.send_message(admin_id, f'{messages[0].from_user.id}\n{messages[0].from_user.username}\nЗаказ:')
    elif type == 'offer':
        bot.send_message(admin_id, f'{messages[0].from_user.id}\n{messages[0].from_user.username}\nПредложка:')
    for m in messages:
        if m.text != None:
            bot.send_message(admin_id, m.text)
        elif m.photo != []:
            if m.caption != None:
                bot.send_photo(admin_id, m.photo[0].file_id, caption=m.caption)
            else:
                bot.send_photo(admin_id, m.photo[0].file_id)
        elif m.video != None:
            if m.caption != None:
                bot.send_video(admin_id, m.video.file_id, caption=m.caption)
            else:
                bot.send_video(admin_id, m.video.file_id)
        elif m.animation != None:
            if m.caption != None:
                bot.send_animation(admin_id, m.animation.file_id, caption=m.caption)
            else:
                bot.send_animation(admin_id, m.animation.file_id)
        elif m.document != None:
            if m.caption != None:
                bot.send_document(admin_id, m.document.file_id, caption=m.caption)
            else:
                bot.send_document(admin_id, m.document.file_id)
        elif m.video_note != None:
            bot.send_video_note(admin_id, m.video_note.file_id)
        elif m.voice != None:
            if m.caption != None:
                bot.send_voice(admin_id, m.voice.file_id, caption=m.caption)
            else:
                bot.send_voice(admin_id, m.voice.file_id)
        elif m.audio != None:
            if m.caption != None:
                bot.send_audio(admin_id, m.audio.file_id, caption=m.caption)
            else:
                bot.send_audio(admin_id, m.audio.file_id)

# -- Launching --

def main() -> None:
    token = 'TOKEN'
    updater = Updater(token)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            FIRST: [
                CallbackQueryHandler(order, pattern='^' + str(ORDER) + '$'),
                CallbackQueryHandler(offer, pattern='^' + str(OFFER) + '$'),
                MessageHandler(Filters.update, warn),
                ],
            SECOND: [
                MessageHandler(Filters.update & ~Filters.command, collect_order),
                CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$'),
                ],
            THIRD: [
                MessageHandler(Filters.update & ~Filters.command, collect_order),
                CallbackQueryHandler(send_order, pattern='^' + str(SEND) + '$'),
                CallbackQueryHandler(cancel, pattern='^' + str(CANCEL) + '$'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling(allowed_updates=Update.ALL_TYPES)

    updater.idle()

#    # -- Webhook properties --
#
#    WEBHOOK_HOST = "IP" (put it here)
#    WEBHOOK_LISTEN = "0.0.0.0"
#    WEBHOOK_PORT = 8443
#
#    WEBHOOK_SSL_CERT = "/home/mrgovart/cert.pem"
#    WEBHOOK_SSL_PRIV = "/home/mrgovart/pkey.key"
#
#    WEBHOOK_URL_BASE = "https://{}:{}".format(WEBHOOK_HOST, WEBHOOK_PORT)
#    WEBHOOK_URL_PATH = "/{}/".format(token)
#
#    # -- Starting webhook --
#
#    updater.start_webhook(listen=WEBHOOK_LISTEN,
#                          port=WEBHOOK_PORT,
#                          url_path=token,
#                          key=WEBHOOK_SSL_PRIV,
#                          cert=WEBHOOK_SSL_CERT,
#                          webhook_url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

if __name__ == '__main__':
    main()

