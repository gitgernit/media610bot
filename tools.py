import aiogram.fsm.context
import aiogram.fsm.storage.memory
import aiogram.fsm.storage.redis
import aiogram.types

REDIS_URL = 'redis://{user}:{password}@{host}:{port}/{db}'


def get_user_state(
    storage: aiogram.fsm.storage.redis.RedisStorage
    | aiogram.fsm.storage.redis.RedisStorage,
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
