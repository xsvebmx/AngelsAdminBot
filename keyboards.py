from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Создать пользователя", callback_data="start_create")
    kb.adjust(1)
    return kb.as_markup()


def username_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Сгенерировать", callback_data="username_generate")
    kb.button(text="✍️ Ввести вручную", callback_data="username_manual")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2, 1)
    return kb.as_markup()


def expire_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="+1 месяц", callback_data="exp_1")
    kb.button(text="+3 месяца", callback_data="exp_3")
    kb.button(text="+6 месяцев", callback_data="exp_6")
    kb.button(text="+12 месяцев", callback_data="exp_12")

    kb.button(text="✍️ Ввести дни вручную", callback_data="exp_manual")

    kb.button(text="❌ Сбросить выбор", callback_data="exp_reset")
    kb.button(text="➡️ Продолжить", callback_data="exp_next")
    kb.button(text="❌ Отмена", callback_data="cancel")

    kb.adjust(2, 2, 1, 2, 1)
    return kb.as_markup()


def skip_input_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭ Пропустить", callback_data="skip")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()


def traffic_kb():
    kb = InlineKeyboardBuilder()

    kb.button(text="50 GB", callback_data="tr_50")
    kb.button(text="100 GB", callback_data="tr_100")
    kb.button(text="200 GB", callback_data="tr_200")
    kb.button(text="500 GB", callback_data="tr_500")

    kb.button(text="♾ Безлимит", callback_data="tr_unlim")
    kb.button(text="✍️ Ввести GB вручную", callback_data="tr_manual")

    kb.button(text="❌ Сбросить", callback_data="tr_reset")
    kb.button(text="➡️ Продолжить", callback_data="tr_next")
    kb.button(text="❌ Отмена", callback_data="cancel")

    kb.adjust(2, 2, 2, 3)
    return kb.as_markup()


def traffic_strategy_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="NO_RESET", callback_data="str_NO_RESET")
    kb.button(text="MONTHLY (default)", callback_data="str_MONTHLY")
    kb.button(text="WEEKLY", callback_data="str_WEEKLY")
    kb.button(text="DAILY", callback_data="str_DAILY")
    kb.button(text="⏭ Пропустить (MONTHLY)", callback_data="str_skip")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2, 2, 1, 1)
    return kb.as_markup()


def internal_squads_kb(internal_squads: dict, selected: set) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # Основные сквады
    for key, (name, _) in internal_squads.items():
        mark = "✅" if key in selected else "⬜"
        kb.button(text=f"{mark} {name}", callback_data=f"int_{key}")

    # Разбиваем сквады по одному в ряд
    kb.adjust(1)

    # Нижний ряд с действиями — используем уже созданные кнопки, а не новый InlineKeyboardBuilder
    reset_btn = InlineKeyboardButton(text="❌ Сбросить", callback_data="int_reset")
    next_btn = InlineKeyboardButton(text="➡️ Продолжить", callback_data="int_next")
    cancel_btn = InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    kb.row(reset_btn, next_btn, cancel_btn)

    return kb.as_markup()


def external_squad_kb(external_squads: dict):
    kb = InlineKeyboardBuilder()

    for key, (name, _) in external_squads.items():
        kb.button(text=name, callback_data=f"ext_{key}")

    kb.button(text="⏭ Пропустить (пусто)", callback_data="ext_skip")
    kb.button(text="❌ Отмена", callback_data="cancel")

    kb.adjust(1)
    return kb.as_markup()


def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Создать", callback_data="confirm_create")
    kb.button(text="❌ Отмена", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()
