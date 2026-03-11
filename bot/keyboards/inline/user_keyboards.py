"""
user_keyboards.py — Denver VPN стиль (Bot API 9.4+)
Кастомные эмодзи + цветные стили кнопок из ss-бота.
Полная структура меню Denver: все вкладки, все разделы.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional, List
from config.settings import Settings


# ════════════════════════════════════════════════════════
#  КОНФИГ КНОПОК — только здесь меняйте текст и иконки
#  icon = custom_emoji_id из @JsonDumpBot или @RawDataBot
#  style = "primary" | "success" | "danger" | None
# ════════════════════════════════════════════════════════
BUTTONS: dict = {
    # ── Главное меню ─────────────────────────────────────
    "buy":           {"text": "Оплата",               "style": "primary", "icon": "6030443364178992166"},
    "vpn":           {"text": "Управление подпиской",  "style": "primary", "icon": "6023896773162967617"},
    "info":          {"text": "Информация",            "style": None,      "icon": "5807800879553715710"},
    "prices":        {"text": "Цены",                  "style": None,      "icon": "6030462253445160459"},
    "referral":      {"text": "Рефералы",              "style": None,      "icon": "6021690418398239007"},
    "transactions":  {"text": "Транзакции",            "style": None,      "icon": "5944922791424825958"},
    "gifts":         {"text": "Подарки",               "style": None,      "icon": "6023826881160157558"},
    "settings":      {"text": "Настройки",             "style": None,      "icon": "6021582331251268218"},
    "back":          {"text": "Назад",                 "style": None,      "icon": "5807862477974674485"},
    "trial":         {"text": "Пробный период",        "style": "success", "icon": "6030462253445160459"},
    # ── Подписка / VPN ───────────────────────────────────
    "vpn_extend":    {"text": "Продлить подписку",     "style": "primary", "icon": "5807485774983077261"},
    "connect":       {"text": "Подключиться",          "style": "primary", "icon": "6019290828759898301"},
    "my_devices":    {"text": "Мои устройства",        "style": None,      "icon": "6026029580907715757"},
    # ── Тарифы ───────────────────────────────────────────
    "plan_standard": {"text": "Обычный тариф",         "style": None,      "icon": "6024039683904772353"},
    "plan_family":   {"text": "Семейный тариф",        "style": None,      "icon": "6021690418398239007"},
    "plan_corp":     {"text": "Корпоративный тариф",   "style": None,      "icon": "6021650913289050282"},
    # ── Оплата ───────────────────────────────────────────
    "pay_yookassa":  {"text": "ЮKassa",                "style": None,      "icon": "6030443364178992166"},
    "pay_crypto":    {"text": "CryptoBot",             "style": None,      "icon": "6019290828759898301"},
    "pay_stars":     {"text": "Звёзды Telegram",       "style": None,      "icon": "6023826881160157558"},
    "pay_freekassa": {"text": "FreeKassa",             "style": None,      "icon": "6030443364178992166"},
    "pay_platega":   {"text": "Platega (СБП/карты)",   "style": None,      "icon": "6030443364178992166"},
    "pay_severpay":  {"text": "SeverPay",              "style": None,      "icon": "6030443364178992166"},
    # ── Настройки ────────────────────────────────────────
    "bind_email":    {"text": "Привязать почту",       "style": None,      "icon": "6019263620142078168"},
    "promo_inline":  {"text": "Промокод", "style": None,      "icon": "5807681883189812861"},
    "language":      {"text": "Язык",                  "style": None,      "icon": "6021582331251268218"},
    "support":       {"text": "Поддержка",             "style": None,      "icon": "5807800879553715710"},
    "status":        {"text": "Статус серверов",       "style": None,      "icon": "6023589944994306428"},
    "terms":         {"text": "Условия сервиса",       "style": None,      "icon": "6021413766669801212"},
    # ── Подарки ──────────────────────────────────────────
    "gift_make":     {"text": "Купить подарочную подписку", "style": None, "icon": "6023826881160157558"},
    "gift_history":  {"text": "История подарков",      "style": None,      "icon": "6035297458907519073"},
    "cancel":        {"text": "Отмена",                "style": None,      "icon": "5807692706507399432"},
}


def _btn(key: str, cb: str = None, url: str = None,
         web_app_url: str = None, text_override: str = None) -> InlineKeyboardButton:
    cfg = BUTTONS.get(key, {"text": key, "style": None, "icon": None})
    text = text_override if text_override is not None else cfg["text"]
    extra = {}
    if cfg.get("style"):
        extra["style"] = cfg["style"]
    if cfg.get("icon"):
        extra["icon_custom_emoji_id"] = cfg["icon"]
    if url:
        return InlineKeyboardButton(text=text, url=url, **extra)
    if web_app_url:
        from aiogram.types import WebAppInfo
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=web_app_url), **extra)
    return InlineKeyboardButton(
        text=text,
        callback_data=cb if cb is not None else key,
        **extra
    )


def _back(cb: str = "main_action:back_to_main") -> InlineKeyboardButton:
    return _btn("back", cb=cb)


# ════════════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ — Denver структура (все вкладки)
# ════════════════════════════════════════════════════════

def get_main_menu_inline_keyboard(
        lang: str,
        i18n_instance,
        settings: Settings,
        show_trial_button: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if show_trial_button and settings.TRIAL_ENABLED:
        builder.row(_btn("trial", cb="main_action:request_trial"))

    # Оплата — главная кнопка (primary, на всю ширину)
    builder.row(_btn("buy", cb="main_action:subscribe"))

    # Информация + Промокод
    builder.row(
        _btn("info",        cb="main_action:info"),
        _btn("promo_inline", cb="main_action:prices"),
    )

    # Рефералы + Транзакции
    row_ref = []
    if settings.REFERRAL_ENABLED:
        row_ref.append(_btn("referral", cb="main_action:referral"))
    row_ref.append(_btn("transactions", cb="main_action:transactions"))
    if row_ref:
        builder.row(*row_ref)

    # Подарки + Настройки
    builder.row(
        _btn("gifts",    cb="main_action:gifts"),
        _btn("settings", cb="main_action:settings"),
    )

    # Управление подпиской — широкая кнопка (primary)
    builder.row(_btn("vpn", cb="main_action:my_subscription"))

    return builder.as_markup()


def get_language_selection_keyboard(i18n_instance,
                                    current_lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🇬🇧 English {'✅' if current_lang == 'en' else ''}",
        callback_data="set_lang_en"
    )
    builder.button(
        text=f"🇷🇺 Русский {'✅' if current_lang == 'ru' else ''}",
        callback_data="set_lang_ru"
    )
    builder.row(_back())
    builder.adjust(1)
    return builder.as_markup()


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
#  УПРАВЛЕНИЕ ПОДПИСКОЙ
# ════════════════════════════════════════════════════════

def get_my_subscription_keyboard(
        lang: str, i18n_instance, settings: Settings,
        has_active_sub: bool = False,
        connect_url: str = None,
        show_devices_button: bool = False,
        current_devices: int = 0,
        max_devices: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _ = lambda key, **kw: i18n_instance.gettext(lang, key, **kw) if i18n_instance else key

    if has_active_sub and connect_url:
        builder.row(_btn("connect", url=connect_url))

    if show_devices_button and has_active_sub:
        dev_label = max_devices if max_devices > 0 else "∞"
        dev_text = _(key="devices_button",
                     current_devices=current_devices,
                     max_devices=dev_label)
        builder.row(InlineKeyboardButton(
            text=dev_text,
            callback_data="main_action:my_devices",
            icon_custom_emoji_id=BUTTONS["my_devices"]["icon"]
        ))

    builder.row(_btn("vpn_extend", cb="main_action:subscribe"))
    builder.row(_back())
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ПОКУПКА / ОПЛАТА
# ════════════════════════════════════════════════════════

def get_subscription_options_keyboard(
        subscription_options: list, currency_symbol: str,
        lang: str, i18n_instance,
        promo_discount_pct: int = 0, traffic_mode: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    currency = currency_symbol or '₽'

    if isinstance(subscription_options, dict):
        items = list(subscription_options.items())
    else:
        items = [(o.get("months"), o.get("price", 0)) for o in subscription_options]
    for period, price in items:
        if price is None:
            continue
        if traffic_mode:
            label = f"{period} ГБ — {price} {currency}"
            cb = f"sub:select_traffic:{period}"
        else:
            label = f"{period} мес. — {price} {currency}"
            cb = f"sub:select_period:{period}"
        builder.button(text=label, callback_data=cb)

    builder.row(_back())
    builder.adjust(1)
    return builder.as_markup()


def get_payment_methods_keyboard(
        lang: str, i18n_instance, settings: Settings,
        months: int, amount: float,
        enabled_methods: list) -> InlineKeyboardMarkup:
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


def get_back_to_main_menu_markup(lang: str,
                                  i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back())
    return builder.as_markup()


def get_trial_confirmation_keyboard(lang: str,
                                     i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Активировать пробный период",
                   callback_data="trial:confirm")
    builder.row(_back())
    builder.adjust(1)
    return builder.as_markup()


def get_devices_keyboard(lang: str, i18n_instance,
                          devices: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _ = lambda key, **kw: i18n_instance.gettext(lang, key, **kw) if i18n_instance else key
    for i, device in enumerate(devices, 1):
        hwid = device.get("hwid", "")
        label = _(key="disconnect_device_button", hwid=hwid[:8], index=i)
        builder.button(text=label, callback_data=f"device:disconnect:{hwid}")
    builder.row(_back(cb="main_action:my_subscription"))
    builder.adjust(1)
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ИНФОРМАЦИЯ
# ════════════════════════════════════════════════════════

def get_info_keyboard(lang: str, i18n_instance,
                       settings: Settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if settings.SUPPORT_LINK:
        builder.button(text="📖 Инструкция",
                       url=settings.SUPPORT_LINK,
                       icon_custom_emoji_id=BUTTONS["info"]["icon"])
    if settings.TERMS_OF_SERVICE_URL:
        builder.button(text="📄 Условия", url=settings.TERMS_OF_SERVICE_URL)
    builder.row(_back())
    builder.adjust(2)
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ПОДАРКИ
# ════════════════════════════════════════════════════════

def get_gift_main_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("gift_make",    cb="main_action:gift_buy"))
    builder.row(_btn("gift_history", cb="main_action:gift_history"))
    builder.row(_back())
    return builder.as_markup()


def get_gift_months_keyboard(lang: str, i18n_instance,
                              settings: Settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    currency = currency_symbol or '₽'
    for months in [1, 3, 6, 12]:
        price = settings.subscription_options.get(months, 0)
        builder.button(text=f"{months} мес. — {price} {currency}",
                       callback_data=f"gift:buy:{months}")
    builder.row(_back(cb="main_action:gifts"))
    builder.adjust(1)
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ════════════════════════════════════════════════════════

def get_settings_keyboard(lang: str, i18n_instance,
                            settings: Settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("language", cb="main_action:language"))
    builder.row(_back())
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ЦЕНЫ
# ════════════════════════════════════════════════════════

def get_prices_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back())
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  ТРАНЗАКЦИИ
# ════════════════════════════════════════════════════════

def get_transactions_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back())
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  РЕФЕРАЛЫ
# ════════════════════════════════════════════════════════

def get_referral_keyboard(lang: str, i18n_instance,
                           settings: Settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back())
    return builder.as_markup()


# ════════════════════════════════════════════════════════
#  НЕДОСТАЮЩИЕ ФУНКЦИИ — требуются сервисами и хендлерами
# ════════════════════════════════════════════════════════

def get_subscribe_only_markup(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    """Кнопка 'Оформить подписку' — используется в panel_webhook_service."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="💳 Оформить подписку",
        callback_data="main_action:subscribe",
        style="primary",
        icon_custom_emoji_id=BUTTONS["buy"]["icon"]
    ))
    return builder.as_markup()


def get_autorenew_cancel_keyboard(lang: str, i18n_instance,
                                   payment_method_id: str = None) -> InlineKeyboardMarkup:
    """Кнопка отмены автопродления — используется в panel_webhook_service."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔄 Продлить подписку",
        callback_data="main_action:subscribe",
        style="primary",
        icon_custom_emoji_id=BUTTONS["vpn_extend"]["icon"]
    ))
    if payment_method_id:
        builder.row(InlineKeyboardButton(
            text="❌ Отменить автопродление",
            callback_data=f"autopay:cancel:{payment_method_id}",
            icon_custom_emoji_id=BUTTONS["cancel"]["icon"]
        ))
    builder.row(_back())
    return builder.as_markup()


def get_payment_url_keyboard(lang: str, i18n_instance,
                              payment_url: str,
                              button_text: str = "💳 Оплатить") -> InlineKeyboardMarkup:
    """Кнопка с URL оплаты — FreeKassa, CryptoBot, Platega, SeverPay."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=button_text,
        url=payment_url,
        icon_custom_emoji_id=BUTTONS["buy"]["icon"]
    ))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_payment_method_keyboard(lang: str, i18n_instance,
                                 months: int,
                                 enabled_methods: list,
                                 settings: Settings = None) -> InlineKeyboardMarkup:
    """Выбор метода оплаты для конкретного периода."""
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
            cfg = BUTTONS.get(key, {})
            extra = {}
            if cfg.get("style"):
                extra["style"] = cfg["style"]
            if cfg.get("icon"):
                extra["icon_custom_emoji_id"] = cfg["icon"]
            builder.row(InlineKeyboardButton(
                text=cfg.get("text", method),
                callback_data=cb,
                **extra
            ))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_yk_autopay_choice_keyboard(lang: str,
                                    i18n_instance) -> InlineKeyboardMarkup:
    """Выбор: оплатить с автопродлением или без — YooKassa."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="💳 Оплатить (без автопродления)",
        callback_data="yk:pay:once",
        icon_custom_emoji_id=BUTTONS["buy"]["icon"]
    ))
    builder.row(InlineKeyboardButton(
        text="🔄 Оплатить с автопродлением",
        callback_data="yk:pay:auto",
        icon_custom_emoji_id=BUTTONS["vpn_extend"]["icon"]
    ))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_yk_saved_cards_keyboard(lang: str, i18n_instance,
                                 saved_methods: list,
                                 months: int) -> InlineKeyboardMarkup:
    """Список сохранённых карт YooKassa для автооплаты."""
    builder = InlineKeyboardBuilder()
    for pm in saved_methods:
        pm_id = pm.get("id", "")
        title = pm.get("title") or pm.get("card", {}).get("last4", pm_id[:8])
        builder.row(InlineKeyboardButton(
            text=f"💳 {title}",
            callback_data=f"yk:saved:{pm_id}:{months}"
        ))
    builder.row(InlineKeyboardButton(
        text="➕ Новая карта",
        callback_data=f"yk:new_card:{months}",
        icon_custom_emoji_id=BUTTONS["buy"]["icon"]
    ))
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_payment_methods_list_keyboard(lang: str, i18n_instance,
                                       payment_methods: list) -> InlineKeyboardMarkup:
    """Список сохранённых методов оплаты пользователя."""
    builder = InlineKeyboardBuilder()
    for pm in payment_methods:
        pm_id = pm.get("id", "")
        title = pm.get("title", pm_id[:8])
        builder.row(InlineKeyboardButton(
            text=f"💳 {title}",
            callback_data=f"pm:detail:{pm_id}"
        ))
    builder.row(_back())
    return builder.as_markup()


def get_payment_method_details_keyboard(lang: str, i18n_instance,
                                         pm_id: str) -> InlineKeyboardMarkup:
    """Детали сохранённого метода оплаты."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🗑 Удалить карту",
        callback_data=f"pm:delete_confirm:{pm_id}",
        icon_custom_emoji_id=BUTTONS["cancel"]["icon"]
    ))
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


def get_payment_method_delete_confirm_keyboard(lang: str, i18n_instance,
                                                pm_id: str) -> InlineKeyboardMarkup:
    """Подтверждение удаления сохранённого метода оплаты."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="✅ Да, удалить",
        callback_data=f"pm:delete:{pm_id}",
        style="danger",
        icon_custom_emoji_id=BUTTONS["cancel"]["icon"]
    ))
    builder.row(_back(cb=f"pm:detail:{pm_id}"))
    return builder.as_markup()


def get_bind_url_keyboard(lang: str, i18n_instance,
                           bind_url: str) -> InlineKeyboardMarkup:
    """Кнопка привязки карты для автоплатежей."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔗 Привязать карту",
        url=bind_url,
        icon_custom_emoji_id=BUTTONS["buy"]["icon"]
    ))
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
        builder.row(InlineKeyboardButton(
            text="💳 Мои карты",
            callback_data="pm:list",
            icon_custom_emoji_id=BUTTONS["buy"]["icon"]
        ))
    builder.row(_back(cb="main_action:my_subscription"))
    return builder.as_markup()


def get_back_to_payment_methods_keyboard(lang: str,
                                          i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back(cb="main_action:subscribe"))
    return builder.as_markup()


def get_referral_link_keyboard(lang: str, i18n_instance,
                                referral_link: str) -> InlineKeyboardMarkup:
    """Кнопка поделиться реферальной ссылкой."""
    builder = InlineKeyboardBuilder()
    share_text = f"Присоединяйся к Denver VPN: {referral_link}"
    builder.row(InlineKeyboardButton(
        text="📤 Поделиться ссылкой",
        url=f"https://t.me/share/url?url={referral_link}&text={share_text}",
        icon_custom_emoji_id=BUTTONS["referral"]["icon"]
    ))
    builder.row(_back())
    return builder.as_markup()


def get_autorenew_confirm_keyboard(lang: str, i18n_instance, payment_method_id: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Включить автопродление", callback_data=f"autopay:confirm:{payment_method_id or ''}"))
    builder.row(InlineKeyboardButton(text="Отмена", callback_data="main_action:my_subscription"))
    return builder.as_markup()


def get_subscribe_only_markup(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Оформить подписку", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_payment_url_keyboard(lang: str, i18n_instance, payment_url: str, button_text: str = "Оплатить") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=button_text, url=payment_url))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_payment_method_keyboard(lang: str, i18n_instance, months: int, enabled_methods: list, settings=None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    method_map = {"yookassa": ("ЮKassa", f"pay:yookassa:{months}"), "cryptopay": ("CryptoBot", f"pay:cryptopay:{months}"), "stars": ("Звезды", f"pay:stars:{months}"), "freekassa": ("FreeKassa", f"pay:freekassa:{months}"), "platega": ("Platega", f"pay:platega:{months}"), "severpay": ("SeverPay", f"pay:severpay:{months}")}
    for method in enabled_methods:
        if method in method_map:
            text, cb = method_map[method]
            builder.row(InlineKeyboardButton(text=text, callback_data=cb))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_yk_autopay_choice_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Оплатить (без автопродления)", callback_data="yk:pay:once"))
    builder.row(InlineKeyboardButton(text="Оплатить с автопродлением", callback_data="yk:pay:auto"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_yk_saved_cards_keyboard(lang: str, i18n_instance, saved_methods: list, months: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pm in saved_methods:
        pm_id = pm.get("id", "")
        title = pm.get("title") or pm.get("card", {}).get("last4", pm_id[:8])
        builder.row(InlineKeyboardButton(text=f"Карта {title}", callback_data=f"yk:saved:{pm_id}:{months}"))
    builder.row(InlineKeyboardButton(text="Новая карта", callback_data=f"yk:new_card:{months}"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_payment_methods_list_keyboard(lang: str, i18n_instance, payment_methods: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for pm in payment_methods:
        pm_id = pm.get("id", "")
        title = pm.get("title", pm_id[:8])
        builder.row(InlineKeyboardButton(text=f"Карта {title}", callback_data=f"pm:detail:{pm_id}"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:my_subscription"))
    return builder.as_markup()


def get_payment_method_details_keyboard(lang: str, i18n_instance, pm_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Удалить карту", callback_data=f"pm:delete_confirm:{pm_id}"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:my_subscription"))
    return builder.as_markup()


def get_payment_method_delete_confirm_keyboard(lang: str, i18n_instance, pm_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Да, удалить", callback_data=f"pm:delete:{pm_id}"))
    builder.row(InlineKeyboardButton(text="Отмена", callback_data=f"pm:detail:{pm_id}"))
    return builder.as_markup()


def get_bind_url_keyboard(lang: str, i18n_instance, bind_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Привязать карту", url=bind_url))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_back_to_payment_method_details_keyboard(pm_id: str, lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Назад", callback_data=f"pm:detail:{pm_id}"))
    return builder.as_markup()


def get_payment_methods_manage_keyboard(lang: str, i18n_instance, has_card: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_card:
        builder.row(InlineKeyboardButton(text="Мои карты", callback_data="pm:list"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:my_subscription"))
    return builder.as_markup()


def get_back_to_payment_methods_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Назад", callback_data="main_action:subscribe"))
    return builder.as_markup()


def get_user_banned_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Поддержка", callback_data="main_action:support"))
    return builder.as_markup()
