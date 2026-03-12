"""
gifts.py — Хэндлеры для раздела «Подарки».

Логика:
  - Подарок покупается (тариф + срок) и сохраняется в таблице Gift.
  - После покупки генерируется одноразовая ссылка активации.
  - Активировать может любой пользователь только 1 раз.
  - Просмотр: активные / использованные подарки + кто активировал.
"""

import logging
import secrets
from aiogram import Router, F, types, Bot
from typing import Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from config.settings import Settings
from bot.middlewares.i18n import JsonI18n
from bot.keyboards.inline.user_keyboards import (
    get_gifts_menu_keyboard,
    get_gift_plan_selection_keyboard,
    get_subscription_options_keyboard,
    get_gift_detail_keyboard,
    get_gifts_list_keyboard,
    get_back_to_main_menu_markup,
)

router = Router(name="user_gifts_router")


# ────────────────────────────────────────────────────────
#  Вспомогательные функции для работы с БД подарков
# ────────────────────────────────────────────────────────

async def _get_gift_model(session: AsyncSession):
    """Ленивый импорт модели Gift — создаётся только если файл существует."""
    try:
        from db.models import Gift
        return Gift
    except ImportError:
        return None


async def _get_user_gifts(session: AsyncSession, user_id: int, is_active: bool):
    """Вернуть список подарков пользователя."""
    Gift = await _get_gift_model(session)
    if Gift is None:
        return []
    try:
        result = await session.execute(
            select(Gift).where(
                Gift.buyer_id == user_id,
                Gift.is_used == (not is_active),
            ).order_by(Gift.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logging.error("Failed to fetch gifts for user %s: %s", user_id, e)
        return []


# ────────────────────────────────────────────────────────
#  Главная вкладка «Подарки»
# ────────────────────────────────────────────────────────

async def show_gifts_menu(
        event: Union[types.Message, types.CallbackQuery],
        i18n_data: dict,
        settings: Settings):
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: Optional[JsonI18n] = i18n_data.get("i18n_instance")
    _ = lambda key, **kw: i18n.gettext(current_lang, key, **kw) if i18n else key

    text = (
        "🎁 <b>Подарки</b>\n\n"
        "Здесь вы можете купить подписку в подарок для другого пользователя.\n"
        "После покупки вы получите одноразовую ссылку, которую можно передать кому угодно.\n\n"
        "Подарок активируется только <b>один раз</b>."
    )
    markup = get_gifts_menu_keyboard(current_lang, i18n)

    target = event.message if isinstance(event, types.CallbackQuery) else event
    if not target:
        return

    if isinstance(event, types.CallbackQuery):
        try:
            await target.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await target.answer(text, reply_markup=markup, parse_mode="HTML")
        try:
            await event.answer()
        except Exception:
            pass
    else:
        await target.answer(text, reply_markup=markup, parse_mode="HTML")


# ────────────────────────────────────────────────────────
#  Callbacks меню подарков
# ────────────────────────────────────────────────────────

@router.callback_query(F.data == "gifts_action:buy")
async def gifts_buy_handler(callback: types.CallbackQuery,
                             i18n_data: dict, settings: Settings):
    """Показать выбор тарифа для подарка."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    text = (
        "🎁 <b>Подписка в подарок</b>\n\n"
        "Выберите тариф, который хотите подарить:"
    )
    markup = get_gift_plan_selection_keyboard(current_lang, i18n)
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gift_plan:"))
async def gift_plan_selected(callback: types.CallbackQuery,
                              i18n_data: dict, settings: Settings):
    """Выбран тариф подарка — показать выбор периода."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    plan = callback.data.split(":")[1]
    plan_names = {
        "standard":  "Стандартный",
        "family":    "Семейный",
        "corporate": "Корпоративный",
    }
    plan_label = plan_names.get(plan, plan)

    text = (
        f"🎁 <b>Подарок — {plan_label} тариф</b>\n\n"
        "Выберите срок подписки:"
    )
    options = settings.subscription_options or {}
    markup = get_subscription_options_keyboard(
        options, "₽", current_lang, i18n, plan=plan, is_gift=True
    )
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gift_period:"))
async def gift_period_selected(callback: types.CallbackQuery,
                                i18n_data: dict, settings: Settings,
                                session: AsyncSession, bot: Bot):
    """Выбран тариф + период — создать подарок и выдать ссылку."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("Ошибка данных.", show_alert=True)
        return

    plan = parts[1]
    try:
        months = int(parts[2])
    except ValueError:
        await callback.answer("Ошибка данных.", show_alert=True)
        return

    user_id = callback.from_user.id
    plan_names = {
        "standard":  "Стандартный",
        "family":    "Семейный",
        "corporate": "Корпоративный",
    }
    plan_label = plan_names.get(plan, plan)

    # Получаем цену
    options = settings.subscription_options or {}
    price = options.get(months) or options.get(str(months))

    # --- Здесь должна быть логика оплаты ---
    # Пока что: создаём подарок без оплаты (заглушка, интегрируйте с платёжной системой)
    # TODO: перенаправить на оплату перед созданием подарка

    Gift = await _get_gift_model(session)
    if Gift is None:
        await callback.answer(
            "Функция подарков временно недоступна. Таблица Gift не создана.",
            show_alert=True,
        )
        return

    token = secrets.token_urlsafe(16)
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception:
        bot_username = "your_bot"

    activation_link = f"https://t.me/{bot_username}?start=gift_{token}"

    try:
        gift = Gift(
            buyer_id=user_id,
            plan=plan,
            months=months,
            token=token,
            is_used=False,
            created_at=datetime.now(timezone.utc),
        )
        session.add(gift)
        await session.commit()
    except Exception as e:
        logging.error("Failed to create gift: %s", e)
        await session.rollback()
        await callback.answer("Ошибка создания подарка.", show_alert=True)
        return

    text = (
        f"✅ <b>Подарок создан!</b>\n\n"
        f"🎁 Тариф: <b>{plan_label}</b>\n"
        f"⏱ Срок: <b>{months} мес.</b>\n\n"
        f"Ссылка для активации:\n"
        f"<code>{activation_link}</code>\n\n"
        f"Передайте эту ссылку получателю. Активировать можно только <b>один раз</b>."
    )
    from bot.keyboards.inline.user_keyboards import get_back_to_main_menu_markup
    markup = get_back_to_main_menu_markup(current_lang, i18n)
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gifts_action:active")
async def gifts_active_handler(callback: types.CallbackQuery,
                                i18n_data: dict, settings: Settings,
                                session: AsyncSession):
    """Показать активные (неиспользованные) подарки."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    gifts_raw = await _get_user_gifts(session, callback.from_user.id, is_active=True)

    if not gifts_raw:
        text = "🟢 <b>Активные подарки</b>\n\nУ вас нет активных (неиспользованных) подарков."
        from bot.keyboards.inline.user_keyboards import _back
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(_back(cb="main_action:gifts"))
        markup = builder.as_markup()
        try:
            await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
        await callback.answer()
        return

    gifts = [{"id": g.gift_id, "plan": g.plan, "months": g.months} for g in gifts_raw]
    text = f"🟢 <b>Активные подарки</b> ({len(gifts)}):"
    markup = get_gifts_list_keyboard(current_lang, i18n, gifts, is_active=True)
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "gifts_action:inactive")
async def gifts_inactive_handler(callback: types.CallbackQuery,
                                  i18n_data: dict, settings: Settings,
                                  session: AsyncSession):
    """Показать использованные подарки."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    gifts_raw = await _get_user_gifts(session, callback.from_user.id, is_active=False)

    if not gifts_raw:
        text = "⚪ <b>Использованные подарки</b>\n\nНет использованных подарков."
        from bot.keyboards.inline.user_keyboards import _back
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.row(_back(cb="main_action:gifts"))
        markup = builder.as_markup()
        try:
            await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
        await callback.answer()
        return

    gifts = [{"id": g.gift_id, "plan": g.plan, "months": g.months} for g in gifts_raw]
    text = f"⚪ <b>Использованные подарки</b> ({len(gifts)}):"
    markup = get_gifts_list_keyboard(current_lang, i18n, gifts, is_active=False)
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gift_detail:view:"))
async def gift_detail_view(callback: types.CallbackQuery,
                            i18n_data: dict, settings: Settings,
                            session: AsyncSession, bot: Bot):
    """Показать детали одного подарка."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    try:
        gift_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка.", show_alert=True)
        return

    Gift = await _get_gift_model(session)
    if Gift is None:
        await callback.answer("Недоступно.", show_alert=True)
        return

    result = await session.execute(select(Gift).where(Gift.gift_id == gift_id))
    gift = result.scalar_one_or_none()
    if not gift or gift.buyer_id != callback.from_user.id:
        await callback.answer("Подарок не найден.", show_alert=True)
        return

    plan_names = {
        "standard":  "Стандартный",
        "family":    "Семейный",
        "corporate": "Корпоративный",
    }
    plan_label = plan_names.get(gift.plan, gift.plan)

    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception:
        bot_username = "your_bot"

    activation_link = f"https://t.me/{bot_username}?start=gift_{gift.token}"

    if gift.is_used:
        activated_by = f"User ID: {gift.activated_by_id}" if gift.activated_by_id else "неизвестно"
        text = (
            f"⚪ <b>Подарок использован</b>\n\n"
            f"🎁 Тариф: <b>{plan_label}</b>\n"
            f"⏱ Срок: <b>{gift.months} мес.</b>\n"
            f"✅ Активировал: {activated_by}\n"
        )
    else:
        text = (
            f"🟢 <b>Активный подарок</b>\n\n"
            f"🎁 Тариф: <b>{plan_label}</b>\n"
            f"⏱ Срок: <b>{gift.months} мес.</b>\n\n"
            f"Ссылка активации:\n"
            f"<code>{activation_link}</code>"
        )

    markup = get_gift_detail_keyboard(current_lang, i18n, gift_id, is_used=gift.is_used)
    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gift_detail:copy:"))
async def gift_copy_link(callback: types.CallbackQuery,
                          i18n_data: dict, settings: Settings,
                          session: AsyncSession, bot: Bot):
    """Отправить ссылку подарка отдельным сообщением."""
    try:
        gift_id = int(callback.data.split(":")[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка.", show_alert=True)
        return

    Gift = await _get_gift_model(session)
    if Gift is None:
        await callback.answer("Недоступно.", show_alert=True)
        return

    result = await session.execute(select(Gift).where(Gift.gift_id == gift_id))
    gift = result.scalar_one_or_none()
    if not gift or gift.buyer_id != callback.from_user.id:
        await callback.answer("Не найден.", show_alert=True)
        return

    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception:
        bot_username = "your_bot"

    link = f"https://t.me/{bot_username}?start=gift_{gift.token}"
    await callback.message.answer(
        f"🔗 Ссылка активации подарка:\n<code>{link}</code>",
        parse_mode="HTML",
    )
    await callback.answer("Ссылка отправлена!")


# ────────────────────────────────────────────────────────
#  Активация подарка по ссылке (/start gift_TOKEN)
# ────────────────────────────────────────────────────────

async def activate_gift_by_token(
        message: types.Message,
        token: str,
        i18n_data: dict,
        settings: Settings,
        session: AsyncSession,
        subscription_service,
        bot: Bot,
):
    """Вызывается из start_command_handler когда start параметр = gift_TOKEN."""
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n = i18n_data.get("i18n_instance")

    Gift = await _get_gift_model(session)
    if Gift is None:
        await message.answer("Функция подарков временно недоступна.")
        return

    result = await session.execute(select(Gift).where(Gift.token == token))
    gift = result.scalar_one_or_none()

    if not gift:
        await message.answer("❌ Подарочная ссылка недействительна.")
        return

    if gift.is_used:
        await message.answer("❌ Этот подарок уже был активирован.")
        return

    user_id = message.from_user.id
    if gift.buyer_id == user_id:
        await message.answer("❌ Нельзя активировать собственный подарок.")
        return

    # Активируем подарок — здесь интегрируйте с SubscriptionService
    gift.is_used = True
    gift.activated_by_id = user_id
    gift.activated_at = datetime.now(timezone.utc)
    await session.commit()

    plan_names = {
        "standard":  "Стандартный",
        "family":    "Семейный",
        "corporate": "Корпоративный",
    }
    plan_label = plan_names.get(gift.plan, gift.plan)

    await message.answer(
        f"🎉 <b>Подарок активирован!</b>\n\n"
        f"🎁 Тариф: <b>{plan_label}</b>\n"
        f"⏱ Срок: <b>{gift.months} мес.</b>\n\n"
        f"Ваша подписка будет активирована в ближайшее время.\n"
        f"⚠️ Автоматическая выдача подписки из подарка требует интеграции с платёжной системой.",
        parse_mode="HTML",
    )
    logging.info("Gift %s activated by user %s", gift.gift_id, user_id)
