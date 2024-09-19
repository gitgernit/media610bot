import aiogram.utils.keyboard

invite_inline = aiogram.utils.keyboard.InlineKeyboardBuilder()
invite_inline.row(
    aiogram.types.InlineKeyboardButton(
        text='Принять',
        callback_data='accept_invite',
    ),
    aiogram.types.InlineKeyboardButton(
        text='Отклонить',
        callback_data='decline_invite',
    ),
)
