import asyncio
import logging
import sys

import aiogram.dispatcher.dispatcher
import aiogram.filters
import aiogram.fsm.context
import aiogram.fsm.state
import aiogram.fsm.storage.base
import aiogram.fsm.storage.redis
import aiogram.types
import aiogram.utils.keyboard
import aiosqlite
from dotenv import load_dotenv

import config
import inlines
import queries
import strings
import tools

load_dotenv()

bot = aiogram.Bot(token=config.API_TOKEN)
storage = aiogram.fsm.storage.redis.RedisStorage.from_url(
    tools.REDIS_URL.format(
        user=config.REDIS_USER,
        password=config.REDIS_PASSWORD,
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
    ),
)
dp = aiogram.dispatcher.dispatcher.Dispatcher(storage=storage)


class UserStates(aiogram.fsm.state.StatesGroup):
    sending_data = aiogram.fsm.state.State()
    waiting_for_approval = aiogram.fsm.state.State()


@dp.chat_join_request(
    aiogram.filters.StateFilter(None),
    aiogram.F.chat.id == int(config.CHANNEL_ID),
)
async def approval_request_handler(
    request: aiogram.types.ChatJoinRequest,
) -> None:
    await bot.send_message(request.from_user.id, strings.INFO_REQUEST)

    state = tools.get_user_state(storage, bot.id, request.from_user.id)
    await state.set_state(UserStates.sending_data)


@dp.message(UserStates.sending_data)
async def pupil_data_handler(
    message: aiogram.types.Message,
    state: aiogram.fsm.context.FSMContext,
) -> None:
    invite = await bot.send_message(
        config.INVITES_GROUP_ID,
        strings.INVITE.format(
            user_login=message.from_user.username,
            user_text=message.text,
        ),
        reply_markup=inlines.invite_inline.as_markup(),
    )
    await state.set_state(UserStates.waiting_for_approval)

    async with aiosqlite.connect(config.DB_FILEPATH) as db:
        await db.execute(
            queries.INSERT_INVITE,
            (invite.message_id, message.from_user.id),
        )
        await db.commit()

    await message.answer(strings.WAIT)


@dp.message(UserStates.waiting_for_approval)
async def pupil_waiting_for_approval_handler(
    message: aiogram.types.Message,
) -> None:
    await message.answer(strings.WAIT)


@dp.callback_query(
    aiogram.F.message.chat.id == int(config.INVITES_GROUP_ID),
    aiogram.F.data == 'accept_invite',
)
async def accept_invite_handler(callback: aiogram.types.CallbackQuery) -> None:
    message_id = callback.message.message_id

    await callback.message.edit_text(
        callback.message.text + '\n\n' + strings.INVITE_ACCEPTED_SUCCES,
        reply_markup=None,
    )

    async with aiosqlite.connect(config.DB_FILEPATH) as db:
        async with db.execute(
            queries.GET_INVITE_USER_ID,
            (message_id,),
        ) as cursor:
            row = await cursor.fetchone()
            [user_id] = row

        await db.execute(queries.DELETE_INVITE, (message_id,))
        await db.commit()

    state = tools.get_user_state(storage, bot.id, user_id)
    await state.set_state(None)

    await bot.approve_chat_join_request(config.CHANNEL_ID, user_id)
    await callback.answer(strings.INVITE_ACCEPTED_SUCCES)


@dp.callback_query(
    aiogram.F.message.chat.id == int(config.INVITES_GROUP_ID),
    aiogram.F.data == 'decline_invite',
)
async def decline_invite_handler(
    callback: aiogram.types.CallbackQuery,
) -> None:
    message_id = callback.message.message_id

    await callback.message.edit_text(
        callback.message.text + '\n\n' + strings.INVITE_DECLINED_SUCCESS,
        reply_markup=None,
    )

    async with aiosqlite.connect(config.DB_FILEPATH) as db:
        async with db.execute(
            queries.GET_INVITE_USER_ID,
            (message_id,),
        ) as cursor:
            row = await cursor.fetchone()
            [user_id] = row

        await db.execute(queries.DELETE_INVITE, (message_id,))
        await db.commit()

    state = tools.get_user_state(storage, bot.id, user_id)
    await state.set_state(None)

    await bot.decline_chat_join_request(config.CHANNEL_ID, user_id)
    await callback.answer(strings.INVITE_DECLINED_SUCCESS)


async def main() -> None:
    async with aiosqlite.connect(config.DB_FILEPATH) as db:
        await db.execute(queries.CREATE_INVITES_TABLE)
        await db.commit()

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
