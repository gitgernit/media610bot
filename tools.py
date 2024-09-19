import aiogram.fsm.context
import aiogram.fsm.storage.memory
import aiogram.fsm.storage.redis
import aiogram.types


def get_user_state(
    storage: aiogram.fsm.storage.redis.RedisStorage
    | aiogram.fsm.storage.memory.MemoryStorage,
    bot_id: int | str,
    user_id: int | str,
) -> aiogram.fsm.context.FSMContext:
    return aiogram.fsm.context.FSMContext(
        storage=storage,
        key=aiogram.fsm.context.StorageKey(
            bot_id=bot_id,
            chat_id=user_id,
            user_id=user_id,
        ),
    )
