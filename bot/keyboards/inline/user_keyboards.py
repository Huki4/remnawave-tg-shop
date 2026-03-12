"""
user_keyboards.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Для изменения кнопок и эмодзи — редактируй bot_config.py
  (файл в корне проекта рядом с main.py)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import Settings
from bot_config import PREMIUM_EMOJI, BUTTON_LABELS, INFO_LINKS


# Собираем BUTTONS из bot_config (для обратной совместимости со всем кодом)
BUTTONS: dict = {
    key: {"text": BUTTON_LABELS.get(key, key), "emoji_id": PREMIUM_EMOJI.get(key, "")}
    for key in set(list(BUTTON_LABELS.keys()) + list(PREMIUM_EMOJI.keys()))
}


# ════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (не трогай)
# ════════════════════════════════════════════════════════

def _btn(key: str, cb: str = None, url: str = None,
         text_override: str = None) -> InlineKeyboardButton:
    cfg = BUTTONS.get(key, {"text": key, "emoji_id": ""})
    text = text_override if text_override is not None else cfg["text"]
    extra = {}
    if cfg.get("emoji_id"):
        extra["icon_custom_emoji_id"] = cfg["emoji_id"]
    if url:
        return InlineKeyboardButton(text=text, url=url, **extra)
    return InlineKeyboardButton(text=text,
                                callback_data=cb if cb is not None else key,
                                **extra)


def _back(cb: str = "main_action:back_to_main") -> InlineKeyboardButton:
    return _btn("back", cb=cb)


# ════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ════════════════════════════════════════════════════════

def get_main_menu_inline_keyboard(
        lang: str, i18n_instance, settings: Settings,
        show_trial_button: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if show_trial_button and settings.TRIAL_ENABLED:
        builder.row(_btn("trial", cb="main_action:request_trial"))
    builder.row(_btn("buy",      cb="main_action:subscribe"))
    builder.row(
        _btn("referral", cb="main_action:referral"),
        _btn("gifts",    cb="main_action:gifts"),
    )
    builder.row(
        _btn("info",     cb="main_action:info"),
        _btn("settings", cb="main_action:settings"),
    )
    builder.row(_btn("vpn", cb="main_action:my_subscription"))
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ОПЛАТА
# ════════════════════════════════════════════════════════

def get_plan_selection_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("plan_standard", cb="plan:standard"))
    builder.row(_btn("plan_family",   cb="plan:family"))
    builder.row(_btn("plan_corp",     cb="plan:corporate"))
    builder.row(_btn("plan_gift",     cb="plan:gift"))
    builder.row(_back())
    return builder.as_markup()


def get_gift_plan_selection_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("plan_standard", cb="gift_plan:standard"))
    builder.row(_btn("plan_family",   cb="gift_plan:family"))
    builder.row(_btn("plan_corp",     cb="gift_plan:corporate"))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_subscription_options_keyboard(
        subscription_options, currency_symbol: str,
        lang: str, i18n_instance,
        promo_discount_pct: int = 0,
        traffic_mode: bool = False,
        plan: str = None,
        is_gift: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    currency = currency_symbol or "₽"
    if isinstance(subscription_options, dict):
        items = list(subscription_options.items())
    else:
        items = [(o.get("months"), o.get("price", 0)) for o in subscription_options]
    for months, price in sorted(items, key=lambda x: x[0] if x[0] else 0):
        if months is None:
            continue
        label = f"{months} ГБ" if traffic_mode else f"{months} мес."
        if price is not None:
            label += f" — {price} {currency} (-{promo_discount_pct}%)" if promo_discount_pct else f" — {price} {currency}"
        cb = f"gift_period:{plan}:{months}" if is_gift else (
            f"sub:{plan}:{months}" if plan else f"sub:standard:{months}"
        )
        builder.row(InlineKeyboardButton(text=label, callback_data=cb))
    builder.row(_back(cb="plan:gift" if is_gift else "main_action:subscribe"))
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ИНФОРМАЦИЯ
# ════════════════════════════════════════════════════════

def get_info_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Ярус 1: Канал (акцент) + FAQ
    cfg_ch = BUTTONS["info_channel"]
    extra_ch = {"icon_custom_emoji_id": cfg_ch["emoji_id"]} if cfg_ch["emoji_id"] else {}
    cfg_faq = BUTTONS["info_faq"]
    extra_faq = {"icon_custom_emoji_id": cfg_faq["emoji_id"]} if cfg_faq["emoji_id"] else {}
    builder.row(
        InlineKeyboardButton(text=cfg_ch["text"],  url=INFO_LINKS["channel"], **extra_ch),
        InlineKeyboardButton(text=cfg_faq["text"], url=INFO_LINKS["faq"],     **extra_faq),
    )
    # Ярус 2: Соглашение + Политика
    cfg_terms = BUTTONS["info_terms"]
    extra_terms = {"icon_custom_emoji_id": cfg_terms["emoji_id"]} if cfg_terms["emoji_id"] else {}
    cfg_priv = BUTTONS["info_privacy"]
    extra_priv = {"icon_custom_emoji_id": cfg_priv["emoji_id"]} if cfg_priv["emoji_id"] else {}
    builder.row(
        InlineKeyboardButton(text=cfg_terms["text"], url=INFO_LINKS["terms"],   **extra_terms),
        InlineKeyboardButton(text=cfg_priv["text"],  url=INFO_LINKS["privacy"], **extra_priv),
    )
    # Ярус 3: Техподдержка — большая акцентная кнопка
    cfg_sup = BUTTONS["info_support"]
    extra_sup = {"icon_custom_emoji_id": cfg_sup["emoji_id"]} if cfg_sup["emoji_id"] else {}
    builder.row(InlineKeyboardButton(text=cfg_sup["text"], url=INFO_LINKS["support"], **extra_sup))
    builder.row(_back())
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  РЕФЕРАЛЫ
# ════════════════════════════════════════════════════════

def get_referral_keyboard(lang: str, i18n_instance,
                           referral_link: str) -> InlineKeyboardMarkup:
    import urllib.parse
    builder = InlineKeyboardBuilder()
    share_text = f"Присоединяйся: {referral_link}"
    cfg = BUTTONS["ref_share"]
    extra = {"icon_custom_emoji_id": cfg["emoji_id"]} if cfg["emoji_id"] else {}
    builder.row(InlineKeyboardButton(
        text=cfg["text"],
        url=f"https://t.me/share/url?url={urllib.parse.quote(referral_link)}&text={urllib.parse.quote(share_text)}",
        **extra,
    ))
    builder.row(_btn("ref_qr", cb="referral_action:generate_qr"))
    builder.row(_back())
    return builder.as_markup()


def get_referral_link_keyboard(lang: str, i18n_instance,
                                referral_link: str) -> InlineKeyboardMarkup:
    return get_referral_keyboard(lang, i18n_instance, referral_link)


# ════════════════════════════════════════════════════════
#  ПОДАРКИ
# ════════════════════════════════════════════════════════

def get_gifts_menu_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("gift_buy",      cb="gifts_action:buy"))
    builder.row(_btn("gift_active",   cb="gifts_action:active"))
    builder.row(_btn("gift_inactive", cb="gifts_action:inactive"))
    builder.row(_back())
    return builder.as_markup()


def get_gift_detail_keyboard(lang: str, i18n_instance,
                               gift_id: int, is_used: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_used:
        builder.row(InlineKeyboardButton(text="📋 Скопировать ссылку",
                                         callback_data=f"gift_detail:copy:{gift_id}"))
        builder.row(InlineKeyboardButton(text="👁 Кто активировал",
                                         callback_data=f"gift_detail:who:{gift_id}"))
    builder.row(_back(cb="gifts_action:active" if not is_used else "gifts_action:inactive"))
    return builder.as_markup()


def get_gifts_list_keyboard(lang: str, i18n_instance,
                              gifts: list, is_active: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for gift in gifts:
        gid = gift.get("id", 0)
        plan = gift.get("plan", "")
        months = gift.get("months", 0)
        builder.row(InlineKeyboardButton(
            text=f"🎁 {plan} · {months} мес.",
            callback_data=f"gift_detail:view:{gid}",
        ))
    builder.row(_back(cb="main_action:gifts"))
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ════════════════════════════════════════════════════════

def get_settings_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("language", cb="main_action:language"))
    builder.row(_back())
    return builder.as_markup()


def get_language_selection_keyboard(i18n_instance,
                                     current_lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"🇬🇧 English {'✅' if current_lang == 'en' else ''}",
                   callback_data="set_lang_en")
    builder.button(text=f"🇷🇺 Русский {'✅' if current_lang == 'ru' else ''}",
                   callback_data="set_lang_ru")
    builder.row(_back(cb="main_action:settings"))
    builder.adjust(1)
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  УПРАВЛЕНИЕ ПОДПИСКОЙ
# ════════════════════════════════════════════════════════

def get_my_subscription_keyboard(
        lang: str, i18n_instance, settings: Settings,
        has_active_sub: bool = False,
        connect_url: str = None,
        show_devices_button: bool = False,
        current_devices: int = 0,
        max_devices: int = 0,
        subscription_link: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_active_sub and connect_url:
        builder.row(_btn("connect", url=connect_url))
    if show_devices_button and has_active_sub:
        dev_label = str(max_devices) if max_devices and max_devices > 0 else "∞"
        label = f"{BUTTONS['my_devices']['text']} ({current_devices}/{dev_label})"
        builder.row(_btn("my_devices", cb="main_action:my_devices", text_override=label))
    if has_active_sub and subscription_link:
        builder.row(_btn("sub_qr", cb="sub_qr:generate"))
    builder.row(_btn("vpn_extend", cb="main_action:subscribe"))
    builder.row(_back())
    return builder.as_markup()


def get_subscription_qr_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  МЕТОДЫ ОПЛАТЫ
# ════════════════════════════════════════════════════════

def get_payment_methods_keyboard(
        lang: str, i18n_instance, settings: Settings,
        months: int, amount: float,
        enabled_methods: list,
        plan: str = "standard") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    method_map = {
        "yookassa":  ("pay_yookassa",  f"pay:yookassa:{plan}:{months}"),
        "cryptopay": ("pay_crypto",    f"pay:cryptopay:{plan}:{months}"),
        "stars":     ("pay_stars",     f"pay:stars:{plan}:{months}"),
        "freekassa": ("pay_freekassa", f"pay:freekassa:{plan}:{months}"),
        "platega":   ("pay_platega",   f"pay:platega:{plan}:{months}"),
        "severpay":  ("pay_severpay",  f"pay:severpay:{plan}:{months}"),
    }
    for method in enabled_methods:
        if method in method_map:
            key, cb = method_map[method]
            builder.row(_btn(key, cb=cb))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  КАНАЛ
# ════════════════════════════════════════════════════════

def get_channel_subscription_keyboard(lang: str, i18n_instance,
                                       channel_link: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _ = lambda key, **kw: i18n_instance.gettext(lang, key, **kw) if i18n_instance else key
    if channel_link:
        builder.button(text=_(key="channel_subscription_join_button"), url=channel_link)
    builder.button(text=_(key="channel_subscription_verify_button"),
                   callback_data="channel_subscription:verify")
    builder.adjust(1)
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  УНИВЕРСАЛЬНЫЕ
# ════════════════════════════════════════════════════════

def get_back_to_main_menu_markup(lang: str, i18n_instance,
                                  callback_data: str = "main_action:back_to_main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back(cb=callback_data))
    return builder.as_markup()


def get_connect_and_main_keyboard(
        lang: str, i18n_instance, settings: Settings,
        config_link: str = None,
        connect_button_url: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    target = connect_button_url or config_link
    if target:
        builder.row(_btn("connect", url=target))
    builder.row(_back())
    return builder.as_markup()


def get_trial_confirmation_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Активировать пробный период", callback_data="trial:confirm")
    builder.row(_back())
    builder.adjust(1)
    return builder.as_markup()


def get_autorenew_confirm_keyboard(enable: bool, sub_id: int,
                                    lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text = "✅ Да, включить" if enable else "✅ Да, отключить"
    builder.row(InlineKeyboardButton(text=text,
                                     callback_data=f"autorenew:confirm:{sub_id}:{1 if enable else 0}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена",
                                     callback_data="main_action:my_subscription"))
    return builder.as_markup()


def get_autorenew_cancel_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="autorenew:cancel"))
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


def get_subscribe_only_markup(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("buy", cb="main_action:subscribe"))
    return builder.as_markup()


def get_payment_url_keyboard(lang: str, i18n_instance, payment_url: str,
                              button_text: str = "Оплатить") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=button_text, url=payment_url))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_payment_method_keyboard(lang: str, i18n_instance, months: int,
                                  enabled_methods: list, settings=None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    method_map = {
        "yookassa":  ("pay_yookassa",  f"pay:yookassa:{months}"),
        "cryptopay": ("pay_crypto",    f"pay:cryptopay:{months}"),
        "stars":     ("pay_stars",     f"pay:stars:{months}"),
        "freekassa": ("pay_freekassa", f"pay:freekassa:{months}"),
        "platega":   ("pay_platega",   f"pay:platega:{months}"),
        "severpay":  ("pay_severpay",  f"pay:severpay:{months}"),
    }
    for method in enabled_methods:
        if method in method_map:
            key, cb = method_map[method]
            builder.row(_btn(key, cb=cb))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_yk_autopay_choice_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Оплатить (без автопродления)",
                                     callback_data="yk:pay:once"))
    builder.row(InlineKeyboardButton(text="Оплатить с автопродлением",
                                     callback_data="yk:pay:auto"))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_yk_saved_cards_keyboard(lang: str, i18n_instance,
                                  saved_methods: list, months: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pm in saved_methods:
        pm_id = pm.get("id", "")
        title = pm.get("title") or pm.get("card", {}).get("last4", pm_id[:8])
        builder.row(InlineKeyboardButton(text=f"Карта {title}",
                                         callback_data=f"yk:saved:{pm_id}:{months}"))
    builder.row(InlineKeyboardButton(text="Новая карта",
                                     callback_data=f"yk:new_card:{months}"))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_payment_methods_list_keyboard(lang: str, i18n_instance,
                                       payment_methods: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pm in payment_methods:
        pm_id = pm.get("id", "")
        title = pm.get("title", pm_id[:8])
        builder.row(InlineKeyboardButton(text=f"Карта {title}",
                                         callback_data=f"pm:detail:{pm_id}"))
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


def get_payment_method_details_keyboard(lang: str, i18n_instance,
                                         pm_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🗑 Удалить карту",
                                     callback_data=f"pm:delete_confirm:{pm_id}"))
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


def get_payment_method_delete_confirm_keyboard(lang: str, i18n_instance,
                                                pm_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Да, удалить",
                                     callback_data=f"pm:delete:{pm_id}"))
    builder.row(InlineKeyboardButton(text="❌ Отмена",
                                     callback_data=f"pm:detail:{pm_id}"))
    return builder.as_markup()


def get_bind_url_keyboard(lang: str, i18n_instance,
                           bind_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 Привязать карту", url=bind_url))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_back_to_payment_method_details_keyboard(pm_id: str, lang: str,
                                                  i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back(cb=f"pm:detail:{pm_id}"))
    return builder.as_markup()


def get_payment_methods_manage_keyboard(lang: str, i18n_instance,
                                         has_card: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_card:
        builder.row(InlineKeyboardButton(text="💳 Мои карты", callback_data="pm:list"))
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


def get_back_to_payment_methods_keyboard(lang: str,
                                          i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_user_banned_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    cfg = BUTTONS["info_support"]
    extra = {"icon_custom_emoji_id": cfg["emoji_id"]} if cfg["emoji_id"] else {}
    builder.row(InlineKeyboardButton(
        text=cfg["text"],
        url=INFO_LINKS.get("support", "https://t.me/yoursupport"),
        **extra,
    ))
    return builder.as_markup()
