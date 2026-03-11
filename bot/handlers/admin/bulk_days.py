"""
Admin: Массовое начисление дней подписки
"""
import logging
import asyncio
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from bot.states.admin_states import AdminStates
from bot.keyboards.inline.admin_keyboards import get_back_to_admin_panel_keyboard, get_admin_panel_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from bot.middlewares.i18n import JsonI18n
from db.dal import user_dal, subscription_dal
from bot.services.subscription_service import SubscriptionService

router = Router(name="bulk_days_router")


async def show_bulk_days_menu(callback: types.CallbackQuery,
                              state: FSMContext,
                              i18n_data: dict,
                              settings: Settings,
                              session: AsyncSession):
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: Optional[JsonI18n] = i18n_data.get("i18n_instance")
    if not i18n or not callback.message:
        await callback.answer("Error.", show_alert=True)
        return

    # Count users
    try:
        all_ids = await user_dal.get_all_active_user_ids_for_broadcast(session)
        active_ids = await user_dal.get_user_ids_with_active_subscription(session)
        all_count = len(all_ids)
        active_count = len(active_ids)
    except Exception:
        all_count = active_count = 0

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"✅ Только активные подписчики ({active_count})",
        callback_data="bulk_days_target:active",
        icon_custom_emoji_id="6021793768196282527"
    ))
    builder.row(InlineKeyboardButton(
        text=f"👥 Всем пользователям ({all_count})",
        callback_data="bulk_days_target:all",
        icon_custom_emoji_id="6021690418398239007"
    ))
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="admin_section:promo_marketing",
        icon_custom_emoji_id="5807679830195444280"
    ))

    try:
        await callback.message.edit_text(
            f"📅 <b>Массовое начисление дней</b>\n\n"
            f"Всего пользователей: <b>{all_count}</b>\n"
            f"С активной подпиской: <b>{active_count}</b>\n\n"
            f"Кому начислить дни?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            f"📅 <b>Массовое начисление дней</b>\n\nКому начислить дни?",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("bulk_days_target:"))
async def bulk_days_target_handler(callback: types.CallbackQuery,
                                   state: FSMContext,
                                   settings: Settings,
                                   i18n_data: dict):
    target = callback.data.split(":")[1]  # "all" or "active"
    await state.update_data(bulk_target=target)
    await state.set_state(AdminStates.waiting_for_bulk_days_count)

    label = "всем пользователям" if target == "all" else "только активным подписчикам"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="admin_action:bulk_days",
        icon_custom_emoji_id="5807679830195444280"
    ))

    try:
        await callback.message.edit_text(
            f"📅 <b>Начисление дней — {label}</b>\n\nВведите количество дней для начисления:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            f"📅 <b>Начисление дней — {label}</b>\n\nВведите количество дней:",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    await callback.answer()


@router.message(AdminStates.waiting_for_bulk_days_count, F.text)
async def bulk_days_count_handler(message: types.Message,
                                  state: FSMContext,
                                  settings: Settings,
                                  i18n_data: dict):
    try:
        days = int(message.text.strip())
        if days <= 0 or days > 3650:
            await message.answer("❌ Введите число от 1 до 3650 дней.")
            return
    except ValueError:
        await message.answer("❌ Введите целое число.")
        return

    data = await state.get_data()
    target = data.get("bulk_target", "active")
    label = "всем пользователям" if target == "all" else "только активным подписчикам"

    await state.update_data(bulk_days=days)
    await state.set_state(AdminStates.waiting_for_bulk_days_confirm)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"Подтвердить — начислить {days} дней",
        callback_data="bulk_days_confirm:yes",
        icon_custom_emoji_id="6026349903863619779"
    ))
    builder.row(InlineKeyboardButton(
        text="Отмена",
        callback_data="admin_action:bulk_days",
        icon_custom_emoji_id="5807692706507399432"
    ))

    await message.answer(
        f"⚠️ <b>Подтверждение</b>\n\n"
        f"Начислить <b>{days} дней</b> {label}.\n\n"
        f"Это действие нельзя отменить. Продолжить?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "bulk_days_confirm:yes", StateFilter(AdminStates.waiting_for_bulk_days_confirm))
async def bulk_days_confirm_handler(callback: types.CallbackQuery,
                                    state: FSMContext,
                                    settings: Settings,
                                    i18n_data: dict,
                                    session: AsyncSession,
                                    subscription_service: SubscriptionService):
    data = await state.get_data()
    target = data.get("bulk_target", "active")
    days = data.get("bulk_days", 0)
    await state.clear()
    await callback.answer()

    if not days:
        await callback.message.answer("❌ Ошибка: количество дней не задано.")
        return

    try:
        await callback.message.edit_text(f"⏳ Начисляю {days} дней...", parse_mode="HTML")
    except Exception:
        pass

    try:
        if target == "active":
            user_ids = await user_dal.get_user_ids_with_active_subscription(session)
        else:
            user_ids = await user_dal.get_all_active_user_ids_for_broadcast(session)
    except Exception as e:
        logging.error(f"bulk_days: failed to get user_ids: {e}")
        await callback.message.answer("❌ Ошибка получения списка пользователей.")
        return

    ok = fail = 0
    for uid in user_ids:
        try:
            await subscription_service.extend_active_subscription_days(
                session, uid, days, "admin_bulk_extension"
            )
            ok += 1
        except Exception:
            fail += 1

    try:
        await session.commit()
    except Exception as e:
        logging.error(f"bulk_days commit error: {e}")

    # Send notifications
    notified = notif_fail = 0
    for uid in user_ids:
        try:
            await callback.message.bot.send_message(
                uid, f"🎉 Вам начислено <b>{days} дней</b> подписки!", parse_mode="HTML"
            )
            notified += 1
        except Exception:
            notif_fail += 1
        await asyncio.sleep(0.05)

    label = "активным подписчикам" if target == "active" else "всем пользователям"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Назад",
        callback_data="admin_section:promo_marketing",
        icon_custom_emoji_id="5807679830195444280"
    ))

    try:
        await callback.message.edit_text(
            f"✅ <b>Готово!</b>\n\n"
            f"Начислено {days} дней {label}.\n"
            f"Обновлено: <b>{ok}</b> | Ошибок: <b>{fail}</b>\n"
            f"Уведомлено: <b>{notified}</b> | Не доставлено: <b>{notif_fail}</b>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            f"✅ Готово! Начислено {days} дней. Обновлено: {ok}, ошибок: {fail}.",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
