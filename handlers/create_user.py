from datetime import datetime, timedelta
import pytz

from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from remnawave.models import CreateUserRequestDto
from remnawave.enums import TrafficLimitStrategy
from remnawave.exceptions import ApiError

from states import CreateUserFlow
from keyboards import (
    username_kb,
    expire_kb,
    skip_input_kb,
    traffic_kb,
    traffic_strategy_kb,
    internal_squads_kb,
    external_squad_kb,
    confirm_kb,
    main_menu_kb
)
from utils import generate_shortid, format_datetime, bytes_to_gb
from remnawave_client import get_sdk

# =========================
# Сквады
# =========================

INTERNAL_SQUADS = {
    "promo1": ("ПРОМО-1", "6ee7a7cd-cfe0-49f1-9e6d-898ad2c61cb2"),
    "promo2": ("ПРОМО-2", "28c99966-6bd1-4eed-97c1-a230f31b015b"),
}
INTERNAL_SQUADS["default"] = ("СВОИ", "ec4dc856-dc75-474f-b2cb-e0e95fc76626")

EXTERNAL_SQUADS = {
    "both": ("Both", "77357f14-dd4e-4921-95e4-708fb56eaa02"),
}
EXTERNAL_SQUADS["whitelist"] = ("Whitelist", "3ed64469-d522-4ae2-87d6-4e0a562f357c")

# =========================
# Helpers
# =========================

def summary_text(data: dict) -> str:
    expire_at = data.get("expire_at")
    traffic_bytes = data.get("traffic_limit_bytes")
    internal_count = len(data.get("active_internal_squads", []))
    external_uuid = data.get("external_squad_uuid")

    return (
        "📋 Проверь данные:\n\n"
        f"👤 Username: {data.get('username')}\n"
        f"🔗 Short UUID: {data.get('short_uuid')}\n"
        f"⏳ Expire: {format_datetime(expire_at)}\n\n"
        f"📧 Email: {data.get('email')}\n"
        f"📱 Telegram ID: {data.get('telegram_id')}\n"
        f"📌 Tag: {data.get('tag')}\n"
        f"📝 Description: {data.get('description')}\n\n"
        f"📲 HWID limit: {data.get('hwid_device_limit')}\n"
        f"📦 Traffic: {bytes_to_gb(traffic_bytes)}\n"
        f"🔄 Strategy: {data.get('traffic_limit_strategy')}\n\n"
        f"👥 Internal squads: {internal_count}\n"
        f"🌍 External squad: {external_uuid}\n"
    )


async def safe_edit_text(message, text: str, reply_markup: InlineKeyboardMarkup = None, **kwargs):
    """Безопасный edit_text — игнорирует ошибку 'message is not modified'."""
    try:
        await message.edit_text(text=text, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise


async def cancel_flow(state: FSMContext, call: CallbackQuery):
    await state.clear()
    await safe_edit_text(call.message, "❌ Отменено.", reply_markup=main_menu_kb())
    await call.answer()


# =========================
# Start Create
# =========================

async def start_create(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(CreateUserFlow.username)
    await safe_edit_text(call.message, "Выбери username:", reply_markup=username_kb())
    await call.answer()


# =========================
# Username
# =========================

async def username_generate(call: CallbackQuery, state: FSMContext):
    username = generate_shortid()
    short_uuid = generate_shortid()

    await state.update_data(username=username, short_uuid=short_uuid)
    await state.set_state(CreateUserFlow.expire_select)
    await state.update_data(expire_months=0, expire_days=0)

    await safe_edit_text(
        call.message,
        f"✅ Username выбран: `{username}`\n\nТеперь выбери срок подписки:",
        reply_markup=expire_kb(),
        parse_mode="Markdown"
    )
    await call.answer()


async def username_manual(call: CallbackQuery, state: FSMContext):
    await safe_edit_text(call.message, "✍️ Введи username вручную (3-36 символов, буквы/цифры/_):",
                         reply_markup=skip_input_kb())
    await call.answer()


async def username_text(message: Message, state: FSMContext):
    username = message.text.strip()
    if len(username) < 3 or len(username) > 36:
        await message.answer("❌ Username должен быть от 3 до 36 символов.")
        return

    short_uuid = generate_shortid()
    await state.update_data(username=username, short_uuid=short_uuid)
    await state.set_state(CreateUserFlow.expire_select)
    await state.update_data(expire_months=0, expire_days=0)

    await message.answer(
        f"✅ Username установлен: `{username}`\n\nВыбери срок подписки:",
        reply_markup=expire_kb(),
        parse_mode="Markdown"
    )


# =========================
# Expire Select
# =========================

async def expire_buttons(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    months = data.get("expire_months", 0)
    days = data.get("expire_days", 0)

    if call.data == "exp_reset":
        months, days = 0, 0
    elif call.data == "exp_1": months, days = 1, 0
    elif call.data == "exp_3": months, days = 3, 0
    elif call.data == "exp_6": months, days = 6, 0
    elif call.data == "exp_12": months, days = 12, 0

    await state.update_data(expire_months=months, expire_days=days)
    selected_str = f"{months} месяцев" if months else (f"{days} дней" if days else "НЕ ВЫБРАНО")

    await safe_edit_text(
        call.message,
        f"⏳ Выбран срок: *{selected_str}*\n\nВыбирай сколько угодно, потом нажми ➡️ Продолжить.",
        reply_markup=expire_kb(),
        parse_mode="Markdown"
    )
    await call.answer()


async def expire_manual(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateUserFlow.expire_manual_days)
    await safe_edit_text(call.message, "✍️ Введи срок в днях (например 45):", reply_markup=skip_input_kb())
    await call.answer()


async def expire_manual_text(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days <= 0 or days > 3650:
            raise Exception()
    except:
        await message.answer("❌ Введи число дней (1 - 3650).")
        return

    await state.update_data(expire_days=days, expire_months=0)
    await state.set_state(CreateUserFlow.expire_select)
    await message.answer(f"✅ Срок установлен: {days} дней\n\nТеперь нажми ➡️ Продолжить или измени выбор:",
                         reply_markup=expire_kb())


async def expire_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    months, days = data.get("expire_months", 0), data.get("expire_days", 0)

    if months <= 0 and days <= 0:
        await call.answer("❌ Сначала выбери срок!", show_alert=True)
        return

    expire_at = datetime.now(tz=pytz.UTC) + timedelta(days=30*months + days)
    await state.update_data(expire_at=expire_at)
    await state.set_state(CreateUserFlow.email)
    await safe_edit_text(call.message, "📧 Введи Email (или пропусти):", reply_markup=skip_input_kb())
    await call.answer()


# =========================
# Skip Handler
# =========================

async def skip_handler(call: CallbackQuery, state: FSMContext):
    current = await state.get_state()

    if current == CreateUserFlow.email.state:
        await state.update_data(email=None)
        await state.set_state(CreateUserFlow.telegram_id)
        await safe_edit_text(call.message, "📱 Введи Telegram ID (или пропусти):", reply_markup=skip_input_kb())

    elif current == CreateUserFlow.telegram_id.state:
        await state.update_data(telegram_id=None)
        await state.set_state(CreateUserFlow.hwid_limit)
        await safe_edit_text(call.message, "📲 Введи HWID лимит (по умолчанию 2) или пропусти:", reply_markup=skip_input_kb())

    elif current == CreateUserFlow.hwid_limit.state:
        await state.update_data(hwid_device_limit=2)
        await state.set_state(CreateUserFlow.tag)
        await safe_edit_text(call.message, "📌 Введи TAG (или пропусти):", reply_markup=skip_input_kb())

    elif current == CreateUserFlow.tag.state:
        await state.update_data(tag=None)
        await state.set_state(CreateUserFlow.description)
        await safe_edit_text(call.message, "📝 Введи описание (или пропусти):", reply_markup=skip_input_kb())

    elif current == CreateUserFlow.description.state:
        await state.update_data(description=None)
        await state.set_state(CreateUserFlow.traffic_select)
        await state.update_data(traffic_limit_bytes=None)
        await safe_edit_text(call.message, "📦 Выбери лимит трафика:", reply_markup=traffic_kb())

    elif current == CreateUserFlow.expire_manual_days.state:
        await state.set_state(CreateUserFlow.expire_select)
        await safe_edit_text(call.message, "⏳ Выбери срок подписки:", reply_markup=expire_kb())

    elif current == CreateUserFlow.traffic_manual_gb.state:
        await state.set_state(CreateUserFlow.traffic_select)
        await safe_edit_text(call.message, "📦 Выбери лимит трафика:", reply_markup=traffic_kb())

    await call.answer()


# =========================
# Email / Telegram / HWID / Tag / Desc
# =========================

async def email_text(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await state.set_state(CreateUserFlow.telegram_id)
    await message.answer("📱 Введи Telegram ID (или пропусти):", reply_markup=skip_input_kb())


async def telegram_text(message: Message, state: FSMContext):
    try:
        tg_id = int(message.text.strip())
    except:
        await message.answer("❌ Telegram ID должен быть числом.")
        return

    await state.update_data(telegram_id=tg_id)
    await state.set_state(CreateUserFlow.hwid_limit)
    await message.answer("📲 Введи HWID лимит (по умолчанию 2) или пропусти:", reply_markup=skip_input_kb())


async def hwid_text(message: Message, state: FSMContext):
    try:
        hwid = int(message.text.strip())
        if hwid < 0 or hwid > 100:
            raise Exception()
    except:
        await message.answer("❌ HWID должен быть числом (0-100).")
        return

    await state.update_data(hwid_device_limit=hwid)
    await state.set_state(CreateUserFlow.tag)
    await message.answer("📌 Введи TAG (или пропусти):", reply_markup=skip_input_kb())


async def tag_text(message: Message, state: FSMContext):
    await state.update_data(tag=message.text.strip())
    await state.set_state(CreateUserFlow.description)
    await message.answer("📝 Введи описание (или пропусти):", reply_markup=skip_input_kb())


async def description_text(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(CreateUserFlow.traffic_select)
    await state.update_data(traffic_limit_bytes=None)
    await message.answer("📦 Выбери лимит трафика:", reply_markup=traffic_kb())


# =========================
# Traffic Select
# =========================

async def traffic_buttons(call: CallbackQuery, state: FSMContext):
    data = call.data

    if data == "tr_reset":
        await state.update_data(traffic_limit_bytes=None)

    elif data == "tr_unlim":
        await state.update_data(traffic_limit_bytes=0)

    elif data.startswith("tr_") and data.split("_")[1].isdigit():
        gb = int(data.split("_")[1])
        await state.update_data(traffic_limit_bytes=gb * 1024**3)

    elif data == "tr_next":
        current_data = await state.get_data()
        traffic = current_data.get("traffic_limit_bytes")
        if traffic is None:
            await call.answer("❌ Сначала выбери трафик!", show_alert=True)
            return
        await state.set_state(CreateUserFlow.traffic_strategy)
        await safe_edit_text(call.message, "🔄 Выбери стратегию сброса трафика (или пропусти):",
                             reply_markup=traffic_strategy_kb())
        await call.answer()
        return
    else:
        await call.answer()
        return

    current_data = await state.get_data()
    traffic_str = bytes_to_gb(current_data.get("traffic_limit_bytes"))
    await safe_edit_text(call.message, f"📦 Трафик выбран: *{traffic_str}*\n\nМожно менять сколько угодно:",
                         reply_markup=traffic_kb(), parse_mode="Markdown")
    await call.answer()


async def traffic_manual(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateUserFlow.traffic_manual_gb)
    await safe_edit_text(call.message,
                         "✍️ Введи лимит трафика в GB (например 37)\nЕсли хочешь безлимит — нажми ♾ Безлимит.",
                         reply_markup=skip_input_kb())
    await call.answer()


async def traffic_manual_text(message: Message, state: FSMContext):
    try:
        gb = int(message.text.strip())
        if gb < 1 or gb > 100000:
            raise Exception()
    except:
        await message.answer("❌ Введи число GB (1 - 100000).")
        return

    await state.update_data(traffic_limit_bytes=gb * 1024**3)
    await state.set_state(CreateUserFlow.traffic_select)
    await message.answer(f"✅ Трафик установлен: {gb} GB\n\nТеперь нажми ➡️ Продолжить или измени выбор:",
                         reply_markup=traffic_kb())


async def traffic_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    traffic = data.get("traffic_limit_bytes")
    if traffic is None:
        await call.answer("❌ Сначала выбери трафик!", show_alert=True)
        return
    await state.set_state(CreateUserFlow.traffic_strategy)
    await safe_edit_text(call.message, "🔄 Выбери стратегию сброса трафика (или пропусти):",
                         reply_markup=traffic_strategy_kb())
    await call.answer()


# =========================
# Strategy
# =========================

async def strategy_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "str_skip":
        strategy = TrafficLimitStrategy.MONTH
    else:
        strategy_name = call.data.split("_", 1)[1]
        if not hasattr(TrafficLimitStrategy, strategy_name):
            await call.answer("❌ Некорректная стратегия!", show_alert=True)
            return
        strategy = getattr(TrafficLimitStrategy, strategy_name)

    await state.update_data(traffic_limit_strategy=strategy)
    await state.set_state(CreateUserFlow.internal_squads)
    await state.update_data(selected_internal=[])

    text = "👥 Выбери внутренние сквады (можно несколько):"
    kb = internal_squads_kb(INTERNAL_SQUADS, set())
    await safe_edit_text(call.message, text=text, reply_markup=kb)
    await call.answer()


# =========================
# Internal squads
# =========================

async def internal_squad_handler(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("selected_internal", []))

    if call.data == "int_reset":
        selected = set()
    elif call.data.startswith("int_"):
        key = call.data.split("_", 1)[1]
        if key in selected:
            selected.remove(key)
        else:
            selected.add(key)

    await state.update_data(selected_internal=list(selected))
    kb = internal_squads_kb(INTERNAL_SQUADS, selected)
    await safe_edit_text(call.message, "👥 Выбери внутренние сквады (можно несколько):", reply_markup=kb)
    await call.answer()


async def internal_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_internal", [])
    uuids = [INTERNAL_SQUADS[key][1] for key in selected if key in INTERNAL_SQUADS]
    await state.update_data(active_internal_squads=uuids)

    await state.set_state(CreateUserFlow.external_squad)
    await safe_edit_text(call.message, "🌍 Выбери внешний сквад (или пропусти):", reply_markup=external_squad_kb(EXTERNAL_SQUADS))
    await call.answer()


# =========================
# External squad
# =========================

async def external_handler(call: CallbackQuery, state: FSMContext):
    if call.data == "ext_skip":
        await state.update_data(external_squad_uuid=None)
    else:
        key = call.data.split("_", 1)[1]
        await state.update_data(external_squad_uuid=EXTERNAL_SQUADS[key][1])

    data = await state.get_data()
    await state.set_state(CreateUserFlow.confirm)
    await safe_edit_text(call.message, summary_text(data), reply_markup=confirm_kb())
    await call.answer()


# =========================
# Confirm create
# =========================

async def confirm_create(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        sdk = get_sdk()
        create_request = CreateUserRequestDto(
            username=data["username"],
            expire_at=data["expire_at"],
            email=data.get("email"),
            telegram_id=data.get("telegram_id"),
            hwid_device_limit=data.get("hwid_device_limit", 2),
            tag=data.get("tag"),
            description=data.get("description"),
            traffic_limit_bytes=data.get("traffic_limit_bytes"),
            traffic_limit_strategy=data.get("traffic_limit_strategy", TrafficLimitStrategy.MONTH),
            active_internal_squads=data.get("active_internal_squads", []),
            external_squad_uuid=data.get("external_squad_uuid"),
            short_uuid=data.get("short_uuid") or generate_shortid()
        )
        user = await sdk.users.create_user(body=create_request)
        await state.clear()

        await safe_edit_text(
            call.message,
            f"✅ Пользователь создан!\n\n"
            f"👤 Username: {user.username}\n"
            f"🆔 UUID: {user.uuid}\n"
            f"🔗 Subscription:\n{user.subscription_url}\n\n"
            f"⏳ Expire: {user.expire_at}",
            reply_markup=main_menu_kb()
        )
        await call.answer()

    except ApiError as e:
        await state.clear()
        await safe_edit_text(
            call.message,
            f"❌ API Error:\n\nCode: {e.error.code}\nMessage: {e.error.message}",
            reply_markup=main_menu_kb()
        )
        await call.answer()
    except Exception as e:
        await state.clear()
        await safe_edit_text(
            call.message,
            f"❌ Ошибка:\n\n{str(e)}",
            reply_markup=main_menu_kb()
        )
        await call.answer()
