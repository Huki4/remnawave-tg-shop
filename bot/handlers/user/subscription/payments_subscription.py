import logging
import math
from typing import Optional

from aiogram import F, Router, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline.user_keyboards import get_payment_method_keyboard
from bot.middlewares.i18n import JsonI18n
from config.settings import Settings

router = Router(name="user_subscription_payments_selection_router")


async def resolve_fiat_offer_price_for_user(
    session: AsyncSession,
    settings: Settings,
    user_id: int,
    months: float,
    sale_mode: str,
    promo_code_service=None,
) -> Optional[float]:
    """Resolve offer price server-side to prevent callback payload tampering."""
    price_source = (
        getattr(settings, "traffic_packages", {}) or {}
        if sale_mode == "traffic"
        else (settings.subscription_options or {})
    )
    base_price = price_source.get(months)
    if base_price is None:
        return None

    resolved_price = float(base_price)
    if promo_code_service:
        active_discount_info = await promo_code_service.get_user_active_discount(session, user_id)
        if active_discount_info:
            discount_pct, _ = active_discount_info
            resolved_price, _ = promo_code_service.calculate_discounted_price(
                resolved_price,
                discount_pct,
            )
    return resolved_price


@router.callback_query(F.data.startswith("subscribe_period:"))
async def select_subscription_period_callback_handler(
    callback: types.CallbackQuery,
    settings: Settings,
    i18n_data: dict,
    session: AsyncSession,
    promo_code_service=None,  # Injected from dispatcher
):
    current_lang = i18n_data.get("current_language", settings.DEFAULT_LANGUAGE)
    i18n: Optional[JsonI18n] = i18n_data.get("i18n_instance")
    get_text = lambda key, **kwargs: i18n.gettext(current_lang, key, **kwargs) if i18n else key

    if not i18n or not callback.message:
        try:
            await callback.answer(get_text("error_occurred_try_again"), show_alert=True)
        except Exception as exc:
            logging.debug("Suppressed exception in bot/handlers/user/subscription/payments_subscription.py: %s", exc)
        return

    # Parse: subscribe_period:{months} or subscribe_period:{months}:{plan}
    parts = callback.data.split(":")
    try:
        months = float(parts[1])
    except (ValueError, IndexError):
        logging.error(f"Invalid subscription period in callback_data: {callback.data}")
        try:
            await callback.answer(get_text("error_try_again"), show_alert=True)
        except Exception as exc:
            logging.debug("Suppressed exception in bot/handlers/user/subscription/payments_subscription.py: %s", exc)
        return

    # Extract optional plan
    selected_plan = parts[2] if len(parts) > 2 else None
    PLAN_DEVICE_LIMITS = {
        "standard": 2,
        "family": 10,
        "corporate": 50,
    }
    plan_device_limit = PLAN_DEVICE_LIMITS.get(selected_plan) if selected_plan else None

    # Store plan device limit in callback message bot_data via FSMContext workaround
    # We pass it via a global dict keyed by user_id (cleared on use)
    if not hasattr(settings, "_plan_device_limits"):
        settings._plan_device_limits = {}
    if plan_device_limit is not None:
        settings._plan_device_limits[callback.from_user.id] = plan_device_limit
    else:
        settings._plan_device_limits.pop(callback.from_user.id, None)

    price_source = settings.subscription_options
    stars_price_source = settings.stars_subscription_options if hasattr(settings, "stars_subscription_options") else {}

    price_rub = price_source.get(months)
    stars_price = stars_price_source.get(months) if stars_price_source else None
    currency_symbol_val = "RUB"

    # Check for active discount and apply if exists
    discount_text = ""
    if promo_code_service and (price_rub is not None or stars_price is not None):
        active_discount_info = await promo_code_service.get_user_active_discount(
            session, callback.from_user.id
        )

        if active_discount_info:
            discount_pct, promo_code = active_discount_info
            if price_rub is not None:
                original_price_rub = price_rub
                price_rub, discount_amt = promo_code_service.calculate_discounted_price(
                    price_rub, discount_pct
                )
                discount_text = get_text(
                    "active_discount_notice",
                    code=promo_code,
                    discount_pct=discount_pct,
                    original_price=original_price_rub,
                    discounted_price=price_rub,
                    discount_amount=discount_amt,
                    currency_symbol=currency_symbol_val,
                )
            if stars_price is not None:
                import math
                original_stars_price = stars_price
                discounted_stars_price, _ = promo_code_service.calculate_discounted_price(
                    float(stars_price), discount_pct
                )
                discounted_stars_price = math.ceil(discounted_stars_price)
                stars_price = discounted_stars_price
                if not discount_text:
                    discount_amt = original_stars_price - discounted_stars_price
                    discount_text = get_text(
                        "active_discount_notice",
                        code=promo_code,
                        discount_pct=discount_pct,
                        original_price=original_stars_price,
                        discounted_price=discounted_stars_price,
                        discount_amount=discount_amt,
                        currency_symbol="⭐",
                    )

    if price_rub is None:
        logging.error(
            f"Price not found for option {months} using subscription_options."
        )
        try:
            await callback.answer(get_text("error_try_again"), show_alert=True)
        except Exception as exc:
            logging.debug("Suppressed exception in bot/handlers/user/subscription/payments_subscription.py: %s", exc)
        return

    plan_labels = {
        "standard": "🔵 Стандартный (2 устройства)",
        "family": "👨‍👩‍👧‍👦 Семейный (10 устройств)",
        "corporate": "🏢 Корпоративный (50 устройств)",
    }
    plan_label = plan_labels.get(selected_plan, "") if selected_plan else ""
    plan_note = f"\n\n📋 <b>Тариф: {plan_label}</b>" if plan_label else ""

    text_content = get_text("choose_payment_method") + plan_note
    if discount_text:
        text_content = f"{discount_text}\n\n{text_content}"

    reply_markup = get_payment_method_keyboard(
        months,
        price_rub,
        stars_price,
        currency_symbol_val,
        current_lang,
        i18n,
        settings,
        sale_mode="subscription",
    )

    try:
        await callback.message.edit_text(text_content, reply_markup=reply_markup, parse_mode="HTML")
    except Exception as e_edit:
        logging.warning(
            f"Edit message for payment method selection failed: {e_edit}. Sending new one."
        )
        await callback.message.answer(text_content, reply_markup=reply_markup, parse_mode="HTML")
    try:
        await callback.answer()
    except Exception as exc:
        logging.debug("Suppressed exception in bot/handlers/user/subscription/payments_subscription.py: %s", exc)
