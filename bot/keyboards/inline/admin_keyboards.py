from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from typing import List
import math

from config.settings import Settings
from bot.middlewares.i18n import JsonI18n
from db.models import User


# ПРЕМИУМ ЭМОДЗИ -- меняйте только значения "id" здесь
# Как получить ID: отправьте эмодзи боту @JsonDumpBot
# и скопируйте поле custom_emoji_id
# Если id = None -- кнопка отображается без премиум эмодзи

ADMIN_EMOJI: dict = {
    # Главное меню
    "stats":        {"text": "Статистика",       "id": "6023589944994306428"},
    "users":        {"text": "Пользователи",     "id": "6021690418398239007"},
    "promo":        {"text": "Промокоды",        "id": "5807681883189812861"},
    "system":       {"text": "Управление",       "id": "6021401276904905698"},
    # Статистика
    "logs":         {"text": "Логи",             "id": "6021607757457660145"},
    "transactions": {"text": "Транзакции",       "id": "6021405408663445899"},
    # Пользователи
    "users_list":   {"text": "Все юзеры",        "id": "6021405408663445899"},
    "users_search": {"text": "Найти юзера",      "id": "6021547434641987535"},
    "bans":         {"text": "Блокировки",       "id": "5807642502634674850"},
    # Бан-менеджмент
    "ban":          {"text": "Забанить",         "id": "5807642502634674850"},
    "unban":        {"text": "Разбанить",        "id": "6026349903863619779"},
    "ban_list":     {"text": "Бан-лист",         "id": "6021319161425172520"},
    # Промокоды
    "promo_create": {"text": "Создать промо",    "id": "6026080811277621020"},
    "promo_bulk":   {"text": "Массово",          "id": "6026271988861902412"},
    "promo_manage": {"text": "Управление промо", "id": "6026080811277621020"},
    "promo_days":   {"text": "Начислить дни",    "id": "5807485774983077261"},
    # Система
    "broadcast":    {"text": "Рассылка",         "id": "6030791402558855470"},
    "ads":          {"text": "Реклама",          "id": "5807414083388971488"},
    "sync":         {"text": "Синхронизация",    "id": "5807767434643382465"},
    "queues":       {"text": "Очереди",          "id": "6026306644953012956"},
    "download_db":  {"text": "Скачать БД",       "id": "5807510999326006028"},
    # Навигация
    "back":         {"text": "Назад",            "id": "5807679830195444280"},
}


def _btn(key: str, callback_data: str = None, url: str = None,
         text_override: str = None) -> InlineKeyboardButton:
    cfg = ADMIN_EMOJI.get(key, {"text": key, "id": None})
    text = text_override if text_override is not None else cfg["text"]
    extra = {}
    if cfg.get("id"):
        extra["icon_custom_emoji_id"] = cfg["id"]
    if url:
        return InlineKeyboardButton(text=text, url=url, **extra)
    return InlineKeyboardButton(
        text=text,
        callback_data=callback_data if callback_data is not None else key,
        **extra
    )


def _back(cb: str = "admin_action:main") -> InlineKeyboardButton:
    return _btn("back", callback_data=cb)


# КЛАВИАТУРЫ

def get_admin_panel_keyboard(i18n_instance, lang: str,
                             settings: Settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_btn("stats",  callback_data="admin_section:stats_monitoring"))
    builder.row(_btn("users",  callback_data="admin_section:user_management"))
    builder.row(_btn("promo",  callback_data="admin_section:promo_marketing"))
    builder.row(_btn("system", callback_data="admin_section:system_functions"))
    return builder.as_markup()


def get_stats_monitoring_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("transactions", callback_data="admin_action:all_transactions"),
        _btn("logs",         callback_data="admin_action:view_logs_menu"),
    )
    builder.row(_back())
    return builder.as_markup()


def get_user_management_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("users_list",   callback_data="admin_action:users_list:0"),
        _btn("users_search", callback_data="admin_action:users_search_prompt"),
    )
    builder.row(_btn("bans", callback_data="admin_section:ban_management"))
    builder.row(_back())
    return builder.as_markup()


def get_ban_management_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("ban",   callback_data="admin_action:ban_user_prompt"),
        _btn("unban", callback_data="admin_action:unban_user_prompt"),
    )
    builder.row(_btn("ban_list", callback_data="admin_action:view_banned:0"))
    builder.row(_back(cb="admin_section:user_management"))
    return builder.as_markup()


def get_promo_marketing_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("promo_create", callback_data="admin_action:create_promo"),
        _btn("promo_bulk",   callback_data="admin_action:create_bulk_promo"),
    )
    builder.row(
        _btn("promo_manage", callback_data="admin_action:promo_management"),
        _btn("promo_days",   callback_data="admin_action:bulk_days"),
    )
    builder.row(_back())
    return builder.as_markup()


def get_system_functions_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        _btn("broadcast", callback_data="admin_action:broadcast"),
        _btn("ads",       callback_data="admin_action:ads"),
    )
    builder.row(
        _btn("sync",   callback_data="admin_action:sync_panel"),
        _btn("queues", callback_data="admin_action:queue_status"),
    )
    builder.row(_btn("download_db", callback_data="admin_action:download_db"))
    builder.row(_back())
    return builder.as_markup()


def get_ads_menu_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="admin_ads_create_button"), callback_data="admin_action:ads_create")
    builder.row(_back(cb="admin_section:system_functions"))
    builder.adjust(1, 1)
    return builder.as_markup()


def get_ads_list_keyboard(i18n_instance, lang: str, campaigns: list,
                          current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    for c in campaigns:
        builder.button(text=c.source, callback_data=f"admin_ads:card:{c.ad_campaign_id}:{current_page}")
    if total_pages > 1:
        row = []
        if current_page > 0:
            row.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_ads:page:{current_page - 1}"))
        row.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="ads_page_display"))
        if current_page < total_pages - 1:
            row.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_ads:page:{current_page + 1}"))
        if row:
            builder.row(*row)
    builder.button(text=_(key="admin_ads_create_button"), callback_data="admin_action:ads_create")
    builder.row(_back(cb="admin_section:system_functions"))
    builder.adjust(1)
    return builder.as_markup()


def get_ad_card_keyboard(i18n_instance, lang: str, campaign_id: int, back_page: int) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="admin_ads_delete_button"), callback_data=f"admin_ads:delete:{campaign_id}:{back_page}")
    builder.button(text=_(key="back_to_ads_list_button"), callback_data=f"admin_ads:page:{back_page}")
    builder.row(_back(cb="admin_section:system_functions"))
    builder.adjust(1)
    return builder.as_markup()


def get_logs_menu_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Все логи сообщений",  callback_data="admin_logs:view_all:0",  icon_custom_emoji_id="6021319161425172520"),
        InlineKeyboardButton(text="Логи пользователя",   callback_data="admin_logs:prompt_user", icon_custom_emoji_id="6021690418398239007"),
    )
    builder.row(InlineKeyboardButton(text="Экспорт в CSV", callback_data="admin_logs:export_csv", icon_custom_emoji_id="5807510999326006028"))
    builder.row(_back(cb="admin_section:stats_monitoring"))
    return builder.as_markup()


def get_logs_pagination_keyboard(current_page: int, total_pages: int,
                                 base_callback_data: str, i18n_instance, lang: str,
                                 back_to_logs_menu: bool = False) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    row_buttons = []
    if current_page > 0:
        row_buttons.append(InlineKeyboardButton(text="⬅️ " + _(key="prev_page_button"),
                                                callback_data=f"{base_callback_data}:{current_page - 1}"))
    if current_page < total_pages - 1:
        row_buttons.append(InlineKeyboardButton(text=_(key="next_page_button") + " ➡️",
                                                callback_data=f"{base_callback_data}:{current_page + 1}"))
    if row_buttons:
        builder.row(*row_buttons)
    if back_to_logs_menu:
        builder.row(InlineKeyboardButton(text=_(key="admin_logs_menu_title"), callback_data="admin_action:view_logs_menu"))
    else:
        builder.row(_back(cb="admin_section:stats_monitoring"))
    return builder.as_markup()


def get_banned_users_keyboard(banned_users: List[User], current_page: int,
                              total_banned: int, i18n_instance: JsonI18n,
                              lang: str, settings: Settings) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    page_size = settings.LOGS_PAGE_SIZE
    for user_row in banned_users:
        parts = []
        if user_row.first_name:
            parts.append(user_row.first_name)
        if user_row.username:
            parts.append(f"(@{user_row.username})")
        if not parts:
            parts.append(f"ID: {user_row.user_id}")
        button_text = _(key="admin_banned_user_button_text",
                        user_display=" ".join(parts).strip(),
                        user_id=user_row.user_id)
        builder.row(InlineKeyboardButton(text=button_text,
                                         callback_data=f"admin_user_card:{user_row.user_id}:{current_page}"))
    if total_banned > page_size:
        total_pages = math.ceil(total_banned / page_size)
        pagination_buttons = []
        if current_page > 0:
            pagination_buttons.append(InlineKeyboardButton(text=_(key="prev_page_button"),
                                                           callback_data=f"admin_action:view_banned:{current_page - 1}"))
        pagination_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}",
                                                       callback_data="stub_page_display"))
        if current_page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(text=_(key="next_page_button"),
                                                           callback_data=f"admin_action:view_banned:{current_page + 1}"))
        if pagination_buttons:
            builder.row(*pagination_buttons)
    builder.row(_back(cb="admin_section:ban_management"))
    return builder.as_markup()


def get_users_list_keyboard(users: List[User], current_page: int,
                            total_users: int, i18n_instance, lang: str,
                            page_size: int = 15) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    for user in users:
        parts = []
        if user.username:
            parts.append(f"@{user.username}")
        parts.append(f"ID: {user.user_id}")
        if user.first_name:
            parts.append(f"- {user.first_name}")
        builder.row(InlineKeyboardButton(text=" ".join(parts),
                                         callback_data=f"admin_user_card_from_list:{user.user_id}:{current_page}"))
    if total_users > page_size:
        total_pages = math.ceil(total_users / page_size)
        pagination_buttons = []
        if current_page > 0:
            pagination_buttons.append(InlineKeyboardButton(text=_(key="prev_page_button"),
                                                           callback_data=f"admin_action:users_list:{current_page - 1}"))
        pagination_buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}",
                                                       callback_data="stub_page_display"))
        if current_page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(text=_(key="next_page_button"),
                                                           callback_data=f"admin_action:users_list:{current_page + 1}"))
        if pagination_buttons:
            builder.row(*pagination_buttons)
    builder.row(_back(cb="admin_section:user_management"))
    return builder.as_markup()


def get_user_card_keyboard(user_id: int, is_banned: bool,
                           i18n_instance, lang: str,
                           banned_list_page: int = 0) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    if is_banned:
        builder.button(text=_(key="user_card_unban_button"),
                       callback_data=f"admin_unban_confirm:{user_id}:{banned_list_page}")
    else:
        builder.button(text=_(key="user_card_ban_button"),
                       callback_data=f"admin_ban_confirm:{user_id}:{banned_list_page}")
    builder.button(text=_(key="user_card_open_profile_button"), url=f"tg://user?id={user_id}")
    builder.button(text=_(key="user_card_back_to_banned_list_button"),
                   callback_data=f"admin_action:view_banned:{banned_list_page}")
    builder.row(_back(cb="admin_section:user_management"))
    builder.adjust(1)
    return builder.as_markup()


def get_confirmation_keyboard(yes_callback_data: str, no_callback_data: str,
                              i18n_instance, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="yes_button"), callback_data=yes_callback_data)
    builder.button(text=_(key="no_button"),  callback_data=no_callback_data)
    return builder.as_markup()


def get_broadcast_confirmation_keyboard(lang: str, i18n_instance,
                                        target: str = "all") -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    def mark(label, is_sel): return ("* " + label) if is_sel else label
    builder.button(text=mark(_(key="broadcast_target_all_button"),      target == "all"),      callback_data="broadcast_target:all")
    builder.button(text=mark(_(key="broadcast_target_active_button"),   target == "active"),   callback_data="broadcast_target:active")
    builder.button(text=mark(_(key="broadcast_target_inactive_button"), target == "inactive"), callback_data="broadcast_target:inactive")
    builder.adjust(3)
    builder.button(text=_(key="confirm_broadcast_send_button"), callback_data="broadcast_final_action:send")
    builder.button(text=_(key="cancel_broadcast_button"),       callback_data="broadcast_final_action:cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_back_to_admin_panel_keyboard(lang: str, i18n_instance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back())
    return builder.as_markup()


def get_sync_result_keyboard(i18n_instance, lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_back(cb="admin_section:system_functions"))
    return builder.as_markup()
