import asyncio
import logging
import sys
import os

import aiogram.fsm.storage.memory
import aiogram.filters
import aiogram.dispatcher.dispatcher
import aiogram.types
import aiogram.utils.keyboard
import aiogram.fsm.state
import aiogram.fsm.context
import aiogram.fsm.storage.base
import aiosqlite

from dotenv import load_dotenv

import queries
import strings

load_dotenv()

API_TOKEN = '8022812254:AAEvakxcpNGmTLFa624ndUnC7D86O7osfxw'

bot = aiogram.Bot(token=API_TOKEN)
storage = aiogram.fsm.storage.memory.MemoryStorage()
dp = aiogram.dispatcher.dispatcher.Dispatcher(storage=storage)

CHANNEL_ID = os.getenv('CHANNEL_ID')
INVITES_GROUP_ID = os.getenv('INVITES_GROUP_ID')
DB_FILEPATH = os.getenv('DB_FILEPATH')


class UserStates(aiogram.fsm.state.StatesGroup):
    sending_data = aiogram.fsm.state.State()
    waiting_for_approval = aiogram.fsm.state.State()


@dp.chat_join_request(aiogram.filters.StateFilter(None),
                      aiogram.F.chat.id == int(CHANNEL_ID))
async def approval_request_handler(request: aiogram.types.ChatJoinRequest):
    await bot.send_message(request.from_user.id, strings.INFO_REQUEST)

    state = aiogram.fsm.context.FSMContext(
        storage=dp.storage,
        key=aiogram.fsm.context.StorageKey(
            bot_id=bot.id,
            chat_id=request.from_user.id,
            user_id=request.from_user.id,
        )
    )
    await state.set_state(UserStates.sending_data)


@dp.message(UserStates.sending_data)
async def pupil_data_handler(message: aiogram.types.Message,
                             state: aiogram.fsm.context.FSMContext):
    builder = aiogram.utils.keyboard.InlineKeyboardBuilder()
    builder.row(
        aiogram.types.InlineKeyboardButton(
            text="Принять", callback_data='accept_invite'
        ),
        aiogram.types.InlineKeyboardButton(
            text="Отклонить", callback_data='decline_invite'
        ),
    )
    invite = await bot.send_message(INVITES_GROUP_ID,
                                       strings.INVITE.format(
                                           user_login=message.from_user.username,
                                           user_text=message.text,
                                       ),
                                       reply_markup=builder.as_markup())
    await state.set_state(UserStates.waiting_for_approval)

    async with aiosqlite.connect(DB_FILEPATH) as db:
        await db.execute(queries.INSERT_INVITE,
                         (invite.message_id, message.from_user.id))
        await db.commit()

    await message.answer(strings.WAIT)


@dp.message(UserStates.waiting_for_approval)
async def pupil_waiting_for_approval_handler(message: aiogram.types.Message):
    await message.answer(strings.WAIT)


@dp.callback_query(aiogram.F.message.chat.id == int(INVITES_GROUP_ID),
                   aiogram.F.data == 'accept_invite')
async def accept_invite_handler(callback: aiogram.types.CallbackQuery):
    message_id = callback.message.message_id

    await callback.message.edit_text(callback.message.text + '\n\n✅Запрос принят✅',
                                     reply_markup=None)

    async with aiosqlite.connect(DB_FILEPATH) as db:
        async with db.execute(queries.GET_INVITE_USER_ID,
                              (message_id,)) as cursor:
            row = await cursor.fetchone()
            [user_id] = row

        await db.execute(queries.DELETE_INVITE, (message_id,))
        await db.commit()

    state = aiogram.fsm.context.FSMContext(
        storage=dp.storage,
        key=aiogram.fsm.context.StorageKey(
            bot_id=bot.id,
            chat_id=user_id,
            user_id=user_id,
        )
    )
    await state.set_state(None)
    await bot.approve_chat_join_request(CHANNEL_ID, user_id)
    await callback.answer('Пользователь принят!')


@dp.callback_query(aiogram.F.message.chat.id == int(INVITES_GROUP_ID),
                   aiogram.F.data == 'decline_invite')
async def accept_invite_handler(callback: aiogram.types.CallbackQuery):
    message_id = callback.message.message_id

    await callback.message.edit_text(callback.message.text + '\n\n❌Запрос отклонен❌',
                                     reply_markup=None)

    async with aiosqlite.connect(DB_FILEPATH) as db:
        async with db.execute(queries.GET_INVITE_USER_ID,
                              (message_id,)) as cursor:
            row = await cursor.fetchone()
            [user_id] = row

        await db.execute(queries.DELETE_INVITE, (message_id,))
        await db.commit()

    state = aiogram.fsm.context.FSMContext(
        storage=dp.storage,
        key=aiogram.fsm.context.StorageKey(
            bot_id=bot.id,
            chat_id=user_id,
            user_id=user_id,
        )
    )
    await state.set_state(None)
    await bot.decline_chat_join_request(CHANNEL_ID, user_id)
    await callback.answer('Пользователь не принят!')


async def main():
    async with aiosqlite.connect(DB_FILEPATH) as db:
        await db.execute(queries.CREATE_INVITES_TABLE)
        await db.commit()

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
