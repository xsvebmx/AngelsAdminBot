from aiogram.fsm.state import StatesGroup, State


class CreateUserFlow(StatesGroup):
    username = State()

    expire_select = State()
    expire_manual_days = State()

    email = State()
    telegram_id = State()
    hwid_limit = State()
    tag = State()
    description = State()

    traffic_select = State()
    traffic_manual_gb = State()

    traffic_strategy = State()

    internal_squads = State()
    external_squad = State()

    confirm = State()
