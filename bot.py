import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from admin_filter import AdminFilterMiddleware
from loguru import logger

from config import BOT_TOKEN
from states import CreateUserFlow
from handlers import (
    cmd_start,
    start_create,
    username_generate,
    username_manual,
    username_text,
    expire_buttons,
    expire_manual,
    expire_manual_text,
    expire_next,
    skip_handler,
    email_text,
    telegram_text,
    hwid_text,
    tag_text,
    description_text,
    traffic_buttons,
    traffic_manual,
    traffic_manual_text,
    traffic_next,
    strategy_handler,
    internal_squad_handler,
    internal_next,
    external_handler,
    confirm_create,
    cancel_flow
)

logger.add("logs/bot.log", level="INFO", rotation="10 MB", retention="1 month", compression="gz")

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрируем middleware
    dp.message.middleware(AdminFilterMiddleware())
    dp.callback_query.middleware(AdminFilterMiddleware())

    # /start
    dp.message.register(cmd_start, F.text == "/start")

    # start flow
    dp.callback_query.register(start_create, F.data == "start_create")

    # cancel
    dp.callback_query.register(lambda call, state: cancel_flow(state, call), F.data == "cancel")

    # username
    dp.callback_query.register(username_generate, CreateUserFlow.username, F.data == "username_generate")
    dp.callback_query.register(username_manual, CreateUserFlow.username, F.data == "username_manual")
    dp.message.register(username_text, CreateUserFlow.username)

    # expire
    dp.callback_query.register(expire_buttons, CreateUserFlow.expire_select, F.data.in_({"exp_1", "exp_3", "exp_6", "exp_12", "exp_reset"}))
    dp.callback_query.register(expire_manual, CreateUserFlow.expire_select, F.data == "exp_manual")
    dp.message.register(expire_manual_text, CreateUserFlow.expire_manual_days)
    dp.callback_query.register(expire_next, CreateUserFlow.expire_select, F.data == "exp_next")

    # skip handler
    dp.callback_query.register(skip_handler, F.data == "skip")

    # email / telegram / hwid / tag / description
    dp.message.register(email_text, CreateUserFlow.email)
    dp.message.register(telegram_text, CreateUserFlow.telegram_id)
    dp.message.register(hwid_text, CreateUserFlow.hwid_limit)
    dp.message.register(tag_text, CreateUserFlow.tag)
    dp.message.register(description_text, CreateUserFlow.description)

    # traffic
    dp.callback_query.register(traffic_buttons, CreateUserFlow.traffic_select, F.data.startswith("tr_") | (F.data == "tr_reset"))
    dp.callback_query.register(traffic_manual, CreateUserFlow.traffic_select, F.data == "tr_manual")
    dp.message.register(traffic_manual_text, CreateUserFlow.traffic_manual_gb)
    dp.callback_query.register(traffic_next, CreateUserFlow.traffic_select, F.data == "tr_next")

    # strategy
    dp.callback_query.register(strategy_handler, CreateUserFlow.traffic_strategy, F.data.startswith("str_"))

    # internal squads
    dp.callback_query.register(
        internal_squad_handler,
        CreateUserFlow.internal_squads,
        (F.data.startswith("int_") & (F.data != "int_next")) | (F.data == "int_reset")
    )
    dp.callback_query.register(
        internal_next,
        CreateUserFlow.internal_squads,
        F.data == "int_next"
    )

    # external squad
    dp.callback_query.register(external_handler, CreateUserFlow.external_squad, F.data.startswith("ext_") | (F.data == "ext_skip"))

    # confirm
    dp.callback_query.register(confirm_create, CreateUserFlow.confirm, F.data == "confirm_create")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logger.info("Bot is launched...")
        asyncio.run(main())
    except Exception as e:
        logger.error(f"The bot fell with a mistake: {e}")
    finally:
        logger.warning("Bot off")
        asyncio.session.close()
