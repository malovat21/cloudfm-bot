import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
    CallbackQueryHandler
)


# Настройки с вашими данными
TOKEN = "8013532862:AAGG6ywOEfm7s6XgFJPBevxjIjmW_cZ8wZE"
ADMIN_IDS = [711876728, 789800147]
ADMIN_USERNAME = "@malovat21"


# Создаем кастомный обработчик логов с поддержкой UTF-8
class Utf8FileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        super().__init__(filename, mode, encoding, delay)


# Настройка логгирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Обработчик для файла с UTF-8
file_handler = Utf8FileHandler("bot.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Обработчик для консоли
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Состояния пользователя
USER_STATES = {}
USER_CARTS = {}
USER_CURRENT_PRODUCT = {}
USER_CURRENT_FLAVORS = {}

# Словари с вкусами
DISPOSABLE_FLAVORS = {
    "HQD NEO X 25000 тяг": [
        "Киви маракуйя гуава",
        "Малина лимон арбуз"
    ],
    "HQD Glaze 12000 тяг": [
        "Виноград Малина",
        "Черная смородина",
        "Черника"
    ],
    "ELF BAR NIC KING 30000 тяг": [
        "Арбуз Вишня",
        "Виноград Клюква", 
        "Черника Малина лёд"
    ],
    "Lost Mary OS 25000 тяг": [
        "Ананас Апельсин",
        "Вишня Малина Лайм",
        "Кислый виноград лёд"
    ],
    "Plonq Ultra 12000 тяг": [
        "Виноград",
        "Голубика Малина",
        "Клубника Манго",
        "Смородина"
    ],
    "Plonq Roqy L 20000 тяг": [
        "Вишня Черника Клюква",
        "Кислое Киви Маракуйя",
        "Сакура Виноград"
    ],
    "PUFFMI TANK 20000 тяг": [
        "Blueberry ice - Черничный лёд",
        "Pomegranate Lime - Гранат Лайм"
    ],
    "Instabar WT 15000 тяг": [
        "Сакура Виноград",
        "Ананас Кокос",
        "Арбузный Коктейль",
        "Вишня Персик Лимон"
    ],
    "WAKA Blast 38000 тяг": [
        "Лимон Лайм + Ментол микс"
    ]
}

LIQUID_FLAVORS = {
    "HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml": [
        "Gum Wolf (Арбузная жвачка)",
        "Sour Beast (Киви, клубника и перечная мята)"
    ],
    "PODONKI ARCADE Salt 2% 30 ml": [
        "Виноград Ежевика",
        "Вишневый энергетик", 
        "Лимонад Голубика",
        "Манго Маракуйя",
        "Цитрусовый Микс"
    ],
    "CATSWILL Salt 2% 30 ml": [
        "Вишня Персик Мята",
        "Имбирный Лимоден с Малиной",
        "Кислый Малиновый Скитлс",
        "Лимонад Ежевика Сироп",
        "Мамба Кислое Яблоко Киви",
        "Скитлс из Винограда Изабеллы"
    ],
    "MAXWELLS Salt 2% 30 ml": [
        "Алтай",
        "Ягодный Мармелад", 
        "Зеленый чай с ягодами"
    ],
    "Rell Green Salt 2% 30 ml": [
        "Grapefruit (Грейпфрут)",
        "Nord Ice Nectarine (Северный Нектарин)",
        "Papaya Banana (Папайя с Бананом)",
        "Passion Citrus (Цитрус Маракуйя)",
        "Pineapple Lemon (Ананас Лимон)",
        "Tropical Smoothie (Тропический Смузи)"
    ],
    "Rell Ultima Salt 2% 30 ml": [
        "Jasmine Raspberry (Жасмин Малина)",
        "Kiwi Guava (Киви Гуава)",
        "Peach Grape (Персик Виноград)",
        "Peach Tea (Персиковый чай)"
    ]
}

# ---- Обновленные клавиатуры ----

def main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["🛒 Каталог", "🛍️ Корзина"],
        ["🚚 Доставка", "❓ Помощь"],
        ["📞 Контакты"]
    ], resize_keyboard=True)


def catalog_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["💧 Жидкости", "🚬 Одноразки"],
        ["🌿 Жевательный табак", "🔧 Под-системы"],
        ["⚙️ Комплектующие для под-систем"],
        ["🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для жидкостей
def liquids_brands_keyboard():
    return ReplyKeyboardMarkup([
        ["HUSKY", "PODONKI", "CATSWILL"],
        ["MAXWELLS", "Rell"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров HUSKY
def husky_products_keyboard():
    return ReplyKeyboardMarkup([
        ["HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml"],
        ["⬅️ Назад к жидкостям", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров PODONKI
def podonki_products_keyboard():
    return ReplyKeyboardMarkup([
        ["PODONKI ARCADE Salt 2% 30 ml"],
        ["⬅️ Назад к жидкостям", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров CATSWILL
def catswill_products_keyboard():
    return ReplyKeyboardMarkup([
        ["CATSWILL Salt 2% 30 ml"],
        ["⬅️ Назад к жидкостям", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров MAXWELLS
def maxwells_products_keyboard():
    return ReplyKeyboardMarkup([
        ["MAXWELLS Salt 2% 30 ml"],
        ["⬅️ Назад к жидкостям", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров Rell
def rell_products_keyboard():
    return ReplyKeyboardMarkup([
        ["Rell Green Salt 2% 30 ml", "Rell Ultima Salt 2% 30 ml"],
        ["⬅️ Назад к жидкостям", "🏠 Главное меню"]
    ], resize_keyboard=True)


# ОБНОВЛЕНО: Клавиатура для одноразок с новыми брендами
def disposable_brands_keyboard():
    return ReplyKeyboardMarkup([
        ["HQD", "ELF BAR", "LOST MARY"],
        ["PLONQ", "WAKA", "PUFFMI"],
        ["INSTABAR"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров HQD
def hqd_products_keyboard():
    return ReplyKeyboardMarkup([
        ["HQD NEO X 25000 тяг", "HQD Glaze 12000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров ELF BAR
def elfbar_products_keyboard():
    return ReplyKeyboardMarkup([
        ["ELF BAR NIC KING 30000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров LOST MARY
def lostmary_products_keyboard():
    return ReplyKeyboardMarkup([
        ["Lost Mary OS 25000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров PLONQ
def plonq_products_keyboard():
    return ReplyKeyboardMarkup([
        ["Plonq Ultra 12000 тяг", "Plonq Roqy L 20000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров WAKA
def waka_products_keyboard():
    return ReplyKeyboardMarkup([
        ["WAKA Blast 38000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров PUFFMI
def puffmi_products_keyboard():
    return ReplyKeyboardMarkup([
        ["PUFFMI TANK 20000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для товаров INSTABAR
def instabar_products_keyboard():
    return ReplyKeyboardMarkup([
        ["Instabar WT 15000 тяг"],
        ["⬅️ Назад к одноразкам", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Инлайн клавиатура для добавления в корзину
def add_to_cart_keyboard(product_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton("🛒 Перейти в корзину", callback_data="go_to_cart")]
    ])


# Клавиатура для снюса
def snus_brands_keyboard():
    return ReplyKeyboardMarkup([
        ["FAFF", "ICEBERG", "LYFT"],
        ["ARQA", "BLAX", "CORVUS"],
        ["KASTA"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для под-систем
def pod_systems_keyboard():
    return ReplyKeyboardMarkup([
        ["Geek Vape", "Vaporesso"],
        ["Smoant", "Voopoo"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для комплектующих
def pod_accessories_keyboard():
    return ReplyKeyboardMarkup([
        ["Испарители", "Картриджы"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


# Клавиатура для картриджей
def cartridges_keyboard():
    return ReplyKeyboardMarkup([
        ["PLONQ 3ml 0.4 Ом", "Vaporesso XROS 3ML 0.4 Ом"],
        ["⬅️ Назад к комплектующим", "🏠 Главное меню"]
    ], resize_keyboard=True)


def back_to_catalog_keyboard():
    return ReplyKeyboardMarkup([
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


def cart_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ Отправить заказ", "✏️ Редактировать заказ"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)


# ---- Функции рассылки для администраторов ----

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Использование: /broadcast <сообщение>")
        return
    
    message = " ".join(context.args)
    await send_broadcast(context, message)
    await update.message.reply_text("✅ Рассылка запущена!")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return
    
    active_users = len(USER_CARTS)
    active_carts = sum(1 for cart in USER_CARTS.values() if cart)
    
    stats_text = f"📊 *Статистика бота:*\n\n"
    stats_text += f"👥 Пользователей: {active_users}\n"
    stats_text += f"🛒 Активных корзин: {active_carts}\n"
    stats_text += f"📝 Состояний пользователей: {len(USER_STATES)}\n"
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return
    
    help_text = (
        "🛠️ *Команды администратора:*\n\n"
        "/broadcast <текст> - Рассылка сообщения всем пользователям\n"
        "/stats - Статистика бота\n"
        "/stop - Остановить бота\n"
        "/admin_help - Справка по командам админа\n\n"
        f"👑 Администраторы: {', '.join(str(admin_id) for admin_id in ADMIN_IDS)}"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def send_broadcast(context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    success_count = 0
    fail_count = 0
    
    broadcast_text = f"📢 *РАССЫЛКА ОТ АДМИНИСТРАТОРА*\n\n{message}\n\n_Это автоматическое сообщение, пожалуйста, не отвечайте на него._"
    
    if not USER_CARTS:
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text="❌ Нет пользователей для рассылки",
                parse_mode="Markdown"
            )
        return
    
    for user_id in USER_CARTS.keys():
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                parse_mode="Markdown"
            )
            success_count += 1
            # Небольшая задержка чтобы не превысить лимиты Telegram
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Ошибка отправки рассылки пользователю {user_id}: {e}")
            fail_count += 1
    
    # Отправляем отчет админам
    report_text = (
        f"📊 *Отчет о рассылке:*\n\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удалось отправить: {fail_count}\n"
        f"👥 Всего пользователей: {len(USER_CARTS)}\n"
        f"📝 Сообщение: {message[:100]}..."
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=report_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки отчета админу {admin_id}: {e}")

# ---- Основные функции магазина ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "main_menu"
    if user.id not in USER_CARTS:
        USER_CARTS[user.id] = []

    await update.message.reply_text(
        f"👋 Добро пожаловать в *CloudFM*, {user.first_name}!\n\n"
        "Мы предлагаем лучшие товары для вейпинга с быстрой доставкой!\n"
        "Выберите действие в меню ниже:",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    logger.info(f"User {user.id} started the bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *Справка по магазину CloudFM*\n\n"
        "Вот что вы можете сделать:\n"
        "- 🛒 *Каталог* - просмотреть товары\n"
        "- 🛍️ *Корзина* - посмотреть ваши заказы\n"
        "- 🚚 *Доставка* - узнать условия доставки\n"
        "- 📞 *Контакты* - связаться с нами\n"
        "- /start - Вернуться в главное меню",
        parse_mode="Markdown"
    )


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "catalog_menu"

    await update.message.reply_text(
        "🛒 *Выберите категориу товаров:*\n\n"
        "• 💧 Жидкости для электронных сигарет\n"
        "• 🚬 Одноразовые электронные сигареты\n"
        "• 🌿 Жевательный табак\n"
        "• 🔧 Под-системы (POD-системы)\n"
        "• ⚙️ Комплектующие для под-систем\n",
        reply_markup=catalog_menu_keyboard(),
        parse_mode="Markdown"
    )


async def show_liquids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "liquids_brands"

    await update.message.reply_text(
        "💧 *Выберите бренд жидкости:*",
        reply_markup=liquids_brands_keyboard(),
        parse_mode="Markdown"
    )


# Функция для отображения одноразок
async def show_disposable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "disposable_brands"

    await update.message.reply_text(
        "🚬 *Одноразовые электронные сигареты:*\n\n"
        "Выберите бренд:",
        reply_markup=disposable_brands_keyboard(),
        parse_mode="Markdown"
    )


# Функция для показа товаров HUSKY
async def show_husky_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "husky_products"

    await update.message.reply_text(
        "💧 *Товары HUSKY:*\n\n"
        "• HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml - 400 ₽\n\n"
        "Выберите продукт:",
        reply_markup=husky_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров PODONKI
async def show_podonki_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "podonki_products"

    await update.message.reply_text(
        "💧 *Товары PODONKI:*\n\n"
        "• PODONKI ARCADE Salt 2% 30 ml - 400 ₽\n\n"
        "Выберите продукт:",
        reply_markup=podonki_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров CATSWILL
async def show_catswill_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "catswill_products"

    await update.message.reply_text(
        "💧 *Товары CATSWILL:*\n\n"
        "• CATSWILL Salt 2% 30 ml - 450 ₽\n\n"
        "Выберите продукт:",
        reply_markup=catswill_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров MAXWELLS
async def show_maxwells_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "maxwells_products"

    await update.message.reply_text(
        "💧 *Товары MAXWELLS:*\n\n"
        "• MAXWELLS Salt 2% 30 ml - 400 ₽\n\n"
        "Выберите продукт:",
        reply_markup=maxwells_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров Rell
async def show_rell_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "rell_products"

    await update.message.reply_text(
        "💧 *Товары Rell:*\n\n"
        "• Rell Green Salt 2% 30 ml - 450 ₽\n"
        "• Rell Ultima Salt 2% 30 ml - 600 ₽\n\n"
        "Выберите продукт:",
        reply_markup=rell_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров HQD
async def show_hqd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "hqd_products"

    await update.message.reply_text(
        "🚬 *Товары HQD:*\n\n"
        "• HQD NEO X 25000 тяг - 1600 ₽\n"
        "• HQD Glaze 12000 тяг - 1350 ₽\n\n"
        "Выберите продукт:",
        reply_markup=hqd_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров ELF BAR
async def show_elfbar_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "elfbar_products"

    await update.message.reply_text(
        "🚬 *Товары ELF BAR:*\n\n"
        "• ELF BAR NIC KING 30000 тяг - 1450 ₽\n\n"
        "Выберите продукт:",
        reply_markup=elfbar_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров LOST MARY
async def show_lostmary_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "lostmary_products"

    await update.message.reply_text(
        "🚬 *Товары LOST MARY:*\n\n"
        "• Lost Mary OS 25000 тяг - 1400 ₽\n\n"
        "Выберите продукт:",
        reply_markup=lostmary_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров PLONQ
async def show_plonq_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "plonq_products"

    await update.message.reply_text(
        "🚬 *Товары PLONQ:*\n\n"
        "• Plonq Ultra 12000 тяг - 1850 ₽\n"
        "• Plonq Roqy L 20000 тяг - 1700 ₽\n\n"
        "Выберите продукт:",
        reply_markup=plonq_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров WAKA
async def show_waka_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "waka_products"

    await update.message.reply_text(
        "🚬 *Товары WAKA:*\n\n"
        "• WAKA Blast 38000 тяг - 1600 ₽\n\n"
        "Выберите продукт:",
        reply_markup=waka_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товаров PUFFMI
async def show_puffmi_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "puffmi_products"

    await update.message.reply_text(
        "🚬 *Товары PUFFMI:*\n\n"
        "• PUFFMI TANK 20000 тяг - 1650 ₽\n\n"
        "Выберите продукт:",
        reply_markup=puffmi_products_keyboard(),
        parse_mode="Markdown"
    )

# Функция для показа товары INSTABAR
async def show_instabar_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "instabar_products"

    await update.message.reply_text(
        "🚬 *Товары INSTABAR:*\n\n"
        "• Instabar WT 15000 тяг - 800 ₽\n\n"
        "Выберите продукт:",
        reply_markup=instabar_products_keyboard(),
        parse_mode="Markdown"
    )

async def show_snus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "snus_brands"

    await update.message.reply_text(
        "🌿 *Жевательный табак:*\n\n"
        "Выберите бренд:",
        reply_markup=snus_brands_keyboard(),
        parse_mode="Markdown"
    )


async def show_pod_systems(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "pod_systems"

    await update.message.reply_text(
        "🔧 *Под-системы:*\n\n"
        "Выберите бренд:",
        reply_markup=pod_systems_keyboard(),
        parse_mode="Markdown"
    )


async def show_pod_accessories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "pod_accessories"

    await update.message.reply_text(
        "⚙️ *Комплектующие для под-систем:*\n\n"
        "Выберите тип:",
        reply_markup=pod_accessories_keyboard(),
        parse_mode="Markdown"
    )


# Функция для показа картриджей
async def show_cartridges(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "cartridges"

    await update.message.reply_text(
        "🔧 *Картриджы для под-систем:*\n\n"
        "• PLONQ 3ml 0.4 Ом - 400 ₽\n"
        "• Vaporesso XROS 3ML 0.4 Ом - 250 ₽\n\n"
        "Выберите продукт:",
        reply_markup=cartridges_keyboard(),
        parse_mode="Markdown"
    )


async def back_to_liquids(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_liquids(update, context)


async def back_to_disposable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_disposable(update, context)


async def back_to_accessories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_pod_accessories(update, context)


async def back_to_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await show_catalog(update, context)


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "main_menu"

    await update.message.reply_text(
        "🏠 Возвращаемся в главное меню",
        reply_markup=main_menu_keyboard()
    )


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    cart = USER_CARTS.get(user.id, [])
    USER_STATES[user.id] = "cart"

    cart_text = "🛍️ *Ваша корзина*\n\n"
    if not cart:
        cart_text += "Ваша корзина пуста"
    else:
        total = 0
        for i, item in enumerate(cart, 1):
            cart_text += f"{i}. {item['name']} - {item['quantity']} шт. ({item['price']} ₽)\n"
            total += item['price'] * item['quantity']
        cart_text += f"\nИтого: *{total} ₽*\n"

    await update.message.reply_text(
        cart_text,
        reply_markup=cart_keyboard(),
        parse_mode="Markdown"
    )


async def delivery_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info = (
        "🚚 *Условия доставки CloudFM*\n\n"
        "• *Самовывоз:* Адрес уточняется при заказе у оператора @CloudFMMSC (Пн-Вс 10:00-22:00)\n"
        "• *Доставка по городу:* Цену доставки уточняйте у оператора @CloudFMMSC (Пн-Вс 10:00-22:00)\n"
        "• *Экспресс-доставка:* При заказе от 3000 ₽, цена доставки 500 ₽ (в течение 2 часов)\n\n"
        "Все заказы оформляются анонимно!"
    )
    await update.message.reply_text(info, parse_mode="Markdown")


async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact_info = (
        "📞 *Контакты магазина CloudFM*\n\n"
        "• Телеграм: @CloudFMMSC\n"
        "Часы работы: 24/7\n\n"
        "По вопросам оптовых закупов: @CloudFMMSC"
    )
    await update.message.reply_text(contact_info, parse_mode="Markdown")


async def send_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    cart = USER_CARTS.get(user.id, [])

    if not cart:
        await update.message.reply_text(
            "❌ Ваша корзина пуста! Добавьте товары перед оформлением заказа.",
            reply_markup=main_menu_keyboard()
        )
        return

    order_text = f"🛒 *Новый заказ!*\n\n"
    order_text += f"👤 Пользователь: [{user.first_name}](tg://user?id={user.id})\n"
    order_text += f"🆔 ID: `{user.id}`\n\n"
    order_text += "📝 *Состав заказа:*\n"

    total = 0
    for item in cart:
        item_total = item['price'] * item['quantity']
        order_text += f"- {item['name']} - {item['quantity']} шт. = {item_total} ₽\n"
        total += item_total

    order_text += f"\n💵 *Итого: {total} ₽*"

    success = False
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=order_text,
                parse_mode="Markdown"
            )
            success = True
            logger.info(f"Order sent to admin {admin_id} for user {user.id}")
        except Exception as e:
            logger.error(f"Error sending order to admin {admin_id}: {e}")

    if success:
        await update.message.reply_text(
            "✅ Ваш заказ оформлен! Скоро с вами свяжется оператор для уточнения деталей.",
            reply_markup=main_menu_keyboard()
        )
        USER_CARTS[user.id] = []
    else:
        await update.message.reply_text(
            "⚠️ Произошла ошибка при отправке заказа. Пожалуйста, свяжитесь с нами через меню Контакты."
        )


async def edit_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    cart = USER_CARTS.get(user.id, [])
    USER_STATES[user.id] = "editing_cart"

    if not cart:
        await update.message.reply_text(
            "❌ Ваша корзина пуста!",
            reply_markup=main_menu_keyboard()
        )
        return

    cart_text = "✏️ *Редактирование корзина*\n\n"
    cart_text += "Отправьте номер товара для удаления:\n\n"

    total = 0
    for i, item in enumerate(cart, 1):
        item_total = item['price'] * item['quantity']
        cart_text += f"{i}. {item['name']} - {item['quantity']} шт. = {item_total} ₽\n"
        total += item_total

    cart_text += f"\n💵 Итого: *{total} ₽*"

    await update.message.reply_text(
        cart_text,
        reply_markup=cart_keyboard(),
        parse_mode="Markdown"
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id in ADMIN_IDS:
        await update.message.reply_text("🛑 Бот остановлен...")
        logger.warning(f"Bot stopped by admin {user.id}")
        await context.application.stop()
    else:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        logger.warning(f"Unauthorized stop attempt by {user.id}")


# Функция для обработки выбора вкуса
async def handle_flavor_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str, product_name: str, price: int):
    user = update.effective_user
    user_id = user.id
    
    # Словарь с URL изображений для каждого продукта
    product_images = {
        "husky_malaysian": "https://iimg.su/i/QxOz3w",
        "podonki_arcade": "https://iimg.su/i/Bkw383",
        "catswill": "https://iimg.su/i/J8MdO8",
        "maxwells": "https://iimg.su/i/3ElcUl",
        "rell_green": "https://iimg.su/i/0KnwNB",
        "rell_ultima": "https://iimg.su/i/tZq4Bl",
        "hqd_neo_x": "https://iimg.su/i/nPspGQ",
        "hqd_glaze": "https://iimg.su/i/4KJr2t",
        "elfbar_nic_king": "https://iimg.su/i/Q8bqko",
        "lost_mary_os": "https://iimg.su/i/IMFhAh",
        "plonq_ultra": "https://iimg.su/i/sUggA0",
        "plonq_roqy_l": "https://iimg.su/i/tMBFds",
        "waka_blast": "https://iimg.su/i/DjZBoz",
        "puffmi_tank": "https://iimg.su/i/t1ibma",
        "instabar_wt": "https://iimg.su/i/53MBuB",
        "plonq_cartridge": "https://iimg.su/i/L8HJGr",
        "vaporesso_cartridge": "https://iimg.su/i/BGCTN4"
    }
    
    # Проверяем, есть ли вкусы у этого продукта
    if product_name in DISPOSABLE_FLAVORS:
        flavors = DISPOSABLE_FLAVORS[product_name]
        USER_CURRENT_PRODUCT[user_id] = product_id
        USER_CURRENT_FLAVORS[user_id] = flavors
        
        # Формируем сообщение со списком вкусов и ценой
        message_text = f"🎯 *{product_name}* - *{price} ₽*\n\n"
        message_text += "Выберите вкус:\n\n"
        for i, flavor in enumerate(flavors, 1):
            message_text += f"{i}. {flavor}\n"
        
        message_text += f"\n💵 Цена: *{price} ₽*"
        
        USER_STATES[user_id] = f"waiting_flavor_{product_id}"
        
        # Отправляем фото с описанием
        if product_id in product_images:
            await update.message.reply_photo(
                photo=product_images[product_id],
                caption=message_text,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(message_text, parse_mode="Markdown")
        
    elif product_name in LIQUID_FLAVORS:
        flavors = LIQUID_FLAVORS[product_name]
        USER_CURRENT_PRODUCT[user_id] = product_id
        USER_CURRENT_FLAVORS[user_id] = flavors
        
        # Формируем сообщение со списком вкусов и ценой
        message_text = f"🎯 *{product_name}* - *{price} ₽*\n\n"
        message_text += "Выберите вкус:\n\n"
        for i, flavor in enumerate(flavors, 1):
            message_text += f"{i}. {flavor}\n"
        
        message_text += f"\n💵 Цена: *{price} ₽*"
        
        USER_STATES[user_id] = f"waiting_flavor_{product_id}"
        
        # Отправляем фото с описанием
        if product_id in product_images:
            await update.message.reply_photo(
                photo=product_images[product_id],
                caption=message_text,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(message_text, parse_mode="Markdown")
        
    else:
        # Если у продукта нет вариантов вкуса, добавляем сразу в корзину
        if user_id not in USER_CARTS:
            USER_CARTS[user_id] = []

        found = False
        for item in USER_CARTS[user_id]:
            if item['name'] == product_name:
                item['quantity'] += 1
                found = True
                break

        if not found:
            USER_CARTS[user_id].append({
                'name': product_name,
                'price': price,
                'quantity': 1
            })

        # Отправляем фото при добавлении в корзину
        if product_id in product_images:
            await update.message.reply_photo(
                photo=product_images[product_id],
                caption=f"✅ *{product_name}* - *{price} ₽* добавлен в корзину!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ *{product_name}* - *{price} ₽* добавлен в корзину!",
                parse_mode="Markdown"
            )


# Обработчик инлайн кнопок
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    user_id = user.id

    await query.answer()

    # Обработка добавления в корзину
    if query.data.startswith("add_"):
        product_id = query.data[4:]

        # Определяем товар по ID
        products = {
            "husky_malaysian": {"name": "HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml", "price": 400},
            "podonki_arcade": {"name": "PODONKI ARCADE Salt 2% 30 ml", "price": 400},
            "catswill": {"name": "CATSWILL Salt 2% 30 ml", "price": 450},
            "maxwells": {"name": "MAXWELLS Salt 2% 30 ml", "price": 400},
            "rell_green": {"name": "Rell Green Salt 2% 30 ml", "price": 450},
            "rell_ultima": {"name": "Rell Ultima Salt 2% 30 ml", "price": 600},
            # Новые товары для одноразок
            "hqd_neo_x": {"name": "HQD NEO X 25000 тяг", "price": 1600},
            "hqd_glaze": {"name": "HQD Glaze 12000 тяг", "price": 1350},
            "elfbar_nic_king": {"name": "ELF BAR NIC KING 30000 тяг", "price": 1450},
            "lost_mary_os": {"name": "Lost Mary OS 25000 тяг", "price": 1400},
            "plonq_ultra": {"name": "Plonq Ultra 12000 тяг", "price": 1850},
            "plonq_roqy_l": {"name": "Plonq Roqy L 20000 тяг", "price": 1700},
            "waka_blast": {"name": "WAKA Blast 38000 тяг", "price": 1600},
            "puffmi_tank": {"name": "PUFFMI TANK 20000 тяг", "price": 1650},
            "instabar_wt": {"name": "Instabar WT 15000 тяг", "price": 800},
            # Новые картриджи
            "plonq_cartridge": {"name": "Картридж PLONQ 3ml 0.4 Ом", "price": 400},
            "vaporesso_cartridge": {"name": "Картридж Vaporesso XROS 3ML 0.4 Ом", "price": 250}
        }

        if product_id in products:
            product = products[product_id]
            product_name = product["name"]
            price = product["price"]
            
            # Вызываем функцию обработки выбора вкуса
            await handle_flavor_selection(update, context, product_id, product_name, price)

    # Обработка перехода в корзину
    elif query.data == "go_to_cart":
        await show_cart_from_query(update, context)


async def show_cart_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    user_id = user.id

    cart = USER_CARTS.get(user_id, [])
    USER_STATES[user_id] = "cart"

    cart_text = "🛍️ *Ваша корзина*\n\n"
    if not cart:
        cart_text += "Ваша корзина пуста"
    else:
        total = 0
        for i, item in enumerate(cart, 1):
            cart_text += f"{i}. {item['name']} - {item['quantity']} шт. ({item['price']} ₽)\n"
            total += item['price'] * item['quantity']
        cart_text += f"\nИтого: *{total} ₽*\n"

    await query.edit_message_caption(
        caption=cart_text,
        parse_mode="Markdown"
    )

    # Отправляем отдельное сообщение с клавиатурой корзины
    await context.bot.send_message(
        chat_id=user_id,
        text="Выберите действие:",
        reply_markup=cart_keyboard()
    )


# ---- Обработчики сообщений ----

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    
    # Сначала проверяем навигационные команды, которые должны работать в любом состоянии
    navigation_commands = {
        "⬅️ назад к жидкостям": back_to_liquids,
        "⬅️ назад к одноразкам": back_to_disposable,
        "⬅️ назад к комплектующим": back_to_accessories,
        "⬅️ назад в каталог": back_to_catalog,
        "🏠 главное меню": back_to_main,
        "🛒 каталог": show_catalog,
        "🛍️ корзина": show_cart,
        "🚚 доставка": delivery_info,
        "❓ помощь": help_command,
        "📞 контакты": contacts
    }
    
    # Проверяем, является ли сообщение навигационной командой (без учета регистра)
    normalized_text = text.lower().strip()
    for command, handler in navigation_commands.items():
        if normalized_text == command.lower():
            # Если это навигационная команда, выполняем ее независимо от состояния
            await handler(update, context)
            # Сбрасываем состояние, если пользователь переходит в другое меню
            if command in ["🏠 главное меню", "⬅️ назад в каталог", "🛒 каталог"]:
                USER_STATES[user_id] = "main_menu" if command == "🏠 главное меню" else "catalog_menu"
            return

    # Обработка выбора вкуса (только если это не навигационная команда)
    current_state = USER_STATES.get(user_id, "")
    if current_state.startswith("waiting_flavor_"):
        if text.isdigit():
            flavor_index = int(text) - 1
            flavors = USER_CURRENT_FLAVORS.get(user_id, [])
            
            if 0 <= flavor_index < len(flavors):
                flavor = flavors[flavor_index]
                product_id = USER_CURRENT_PRODUCT[user_id]
                
                # Получаем информацию о продукте
                products = {
                    "husky_malaysian": {"name": "HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml", "price": 400},
                    "podonki_arcade": {"name": "PODONKI ARCADE Salt 2% 30 ml", "price": 400},
                    "catswill": {"name": "CATSWILL Salt 2% 30 ml", "price": 450},
                    "maxwells": {"name": "MAXWELLS Salt 2% 30 ml", "price": 400},
                    "rell_green": {"name": "Rell Green Salt 2% 30 ml", "price": 450},
                    "rell_ultima": {"name": "Rell Ultima Salt 2% 30 ml", "price": 600},
                    # Новые товары для одноразок
                    "hqd_neo_x": {"name": "HQD NEO X 25000 тяг", "price": 1600},
                    "hqd_glaze": {"name": "HQD Glaze 12000 тяг", "price": 1350},
                    "elfbar_nic_king": {"name": "ELF BAR NIC KING 30000 тяг", "price": 1450},
                    "lost_mary_os": {"name": "Lost Mary OS 25000 тяг", "price": 1400},
                    "plonq_ultra": {"name": "Plonq Ultra 12000 тяг", "price": 1850},
                    "plonq_roqy_l": {"name": "Plonq Roqy L 20000 тяг", "price": 1700},
                    "waka_blast": {"name": "WAKA Blast 38000 тяг", "price": 1600},
                    "puffmi_tank": {"name": "PUFFMI TANK 20000 тяг", "price": 1650},
                    "instabar_wt": {"name": "Instabar WT 15000 тяг", "price": 800},
                    # Новые картриджи
                    "plonq_cartridge": {"name": "Картридж PLONQ 3ml 0.4 Ом", "price": 400},
                    "vaporesso_cartridge": {"name": "Картридж Vaporesso XROS 3ML 0.4 Ом", "price": 250}
                }
                
                if product_id in products:
                    product = products[product_id]
                    product_name_with_flavor = f"{product['name']} - {flavor}"
                    
                    # Добавляем в корзину
                    if user_id not in USER_CARTS:
                        USER_CARTS[user_id] = []

                    found = False
                    for item in USER_CARTS[user_id]:
                        if item['name'] == product_name_with_flavor:
                            item['quantity'] += 1
                            found = True
                            break

                    if not found:
                        USER_CARTS[user_id].append({
                            'name': product_name_with_flavor,
                            'price': product['price'],
                            'quantity': 1
                        })

                    await update.message.reply_text(
                        f"✅ {product_name_with_flavor} добавлен в корзину!",
                        parse_mode="Markdown"
                    )
                    
                    # Сбрасываем состояние
                    USER_STATES[user_id] = "main_menu"
                else:
                    await update.message.reply_text("❌ Ошибка: продукт не найден")
            else:
                await update.message.reply_text("❌ Неверный номер вкуса. Пожалуйста, выберите цифру из списка.")
        else:
            await update.message.reply_text("❌ Пожалуйста, введите цифру, соответствующую вкусу, или используйте кнопки навигации.")
        return

    # Обработка главного меню
    if text == "🛒 Каталог":
        await show_catalog(update, context)
    elif text == "🛍️ Корзина":
        await show_cart(update, context)
    elif text == "🚚 Доставка":
        await delivery_info(update, context)
    elif text == "❓ Помощь":
        await help_command(update, context)
    elif text == "📞 Контакты":
        await contacts(update, context)

    # Обработка меню каталога
    elif text == "💧 Жидкости":
        await show_liquids(update, context)
    elif text == "🚬 Одноразки":
        await show_disposable(update, context)
    elif text == "🌿 Жевательный табак":
        await update.message.reply_text(
            "❌ *Товар отсутствует*\n\n"
            "К сожалению, Жевательный табак временно отсутствует в продаже. "
            "Выберите другие товары из каталога.",
            parse_mode="Markdown",
            reply_markup=back_to_catalog_keyboard()
        )
    elif text == "🔧 Под-системы":
        await update.message.reply_text(
            "❌ *товар отсутствует*\n\n"
            "К сожалению, под-системы временно отсутствуют в продаже. "
            "Выберите другие товары из каталога.",
            parse_mode="Markdown",
            reply_markup=back_to_catalog_keyboard()
        )
    elif text == "⚙️ Комплектующие для под-систем":
        await show_pod_accessories(update, context)
    elif text == "🏠 Главное меню":
        await back_to_main(update, context)

    # Обработка брендов жидкостей
    elif USER_STATES.get(user_id) == "liquids_brands" and text in ["HUSKY", "PODONKI", "CATSWILL", "MAXWELLS", "Rell"]:
        if text == "HUSKY":
            await show_husky_products(update, context)
        elif text == "PODONKI":
            await show_podonki_products(update, context)
        elif text == "CATSWILL":
            await show_catswill_products(update, context)
        elif text == "MAXWELLS":
            await show_maxwells_products(update, context)
        elif text == "Rell":
            await show_rell_products(update, context)

    # Обработка брендов одноразок
    elif USER_STATES.get(user_id) == "disposable_brands" and text in ["HQD", "ELF BAR", "LOST MARY", "PLONQ", "WAKA", "PUFFMI", "INSTABAR"]:
        if text == "HQD":
            await show_hqd_products(update, context)
        elif text == "ELF BAR":
            await show_elfbar_products(update, context)
        elif text == "LOST MARY":
            await show_lostmary_products(update, context)
        elif text == "PLONQ":
            await show_plonq_products(update, context)
        elif text == "WAKA":
            await show_waka_products(update, context)
        elif text == "PUFFMI":
            await show_puffmi_products(update, context)
        elif text == "INSTABAR":
            await show_instabar_products(update, context)

    # Обработка товаров HUSKY
    elif USER_STATES.get(user_id) == "husky_products":
        if text == "HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml":
            await handle_flavor_selection(update, context, "husky_malaysian", "HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml", 400)
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров PODONKI
    elif USER_STATES.get(user_id) == "podonki_products":
        if text == "PODONKI ARCADE Salt 2% 30 ml":
            await handle_flavor_selection(update, context, "podonki_arcade", "PODONKI ARCADE Salt 2% 30 ml", 400)
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров CATSWILL
    elif USER_STATES.get(user_id) == "catswill_products":
        if text == "CATSWILL Salt 2% 30 ml":
            await handle_flavor_selection(update, context, "catswill", "CATSWILL Salt 2% 30 ml", 450)
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров MAXWELLS
    elif USER_STATES.get(user_id) == "maxwells_products":
        if text == "MAXWELLS Salt 2% 30 ml":
            await handle_flavor_selection(update, context, "maxwells", "MAXWELLS Salt 2% 30 ml", 400)
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров Rell
    elif USER_STATES.get(user_id) == "rell_products":
        if text == "Rell Green Salt 2% 30 ml":
            await handle_flavor_selection(update, context, "rell_green", "Rell Green Salt 2% 30 ml", 450)
        elif text == "Rell Ultima Salt 2% 30 ml":
            await handle_flavor_selection(update, context, "rell_ultima", "Rell Ultima Salt 2% 30 ml", 600)
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров HQD
    elif USER_STATES.get(user_id) == "hqd_products":
        if text == "HQD NEO X 25000 тяг":
            await handle_flavor_selection(update, context, "hqd_neo_x", "HQD NEO X 25000 тяг", 1600)
        elif text == "HQD Glaze 12000 тяг":
            await handle_flavor_selection(update, context, "hqd_glaze", "HQD Glaze 12000 тяг", 1350)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров ELF BAR
    elif USER_STATES.get(user_id) == "elfbar_products":
        if text == "ELF BAR NIC KING 30000 тяг":
            await handle_flavor_selection(update, context, "elfbar_nic_king", "ELF BAR NIC KING 30000 тяг", 1450)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров LOST MARY
    elif USER_STATES.get(user_id) == "lostmary_products":
        if text == "Lost Mary OS 25000 тяг":
            await handle_flavor_selection(update, context, "lost_mary_os", "Lost Mary OS 25000 тяг", 1400)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров PLONQ
    elif USER_STATES.get(user_id) == "plonq_products":
        if text == "Plonq Ultra 12000 тяг":
            await handle_flavor_selection(update, context, "plonq_ultra", "Plonq Ultra 12000 тяг", 1850)
        elif text == "Plonq Roqy L 20000 тяг":
            await handle_flavor_selection(update, context, "plonq_roqy_l", "Plonq Roqy L 20000 тяг", 1700)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров WAKA
    elif USER_STATES.get(user_id) == "waka_products":
        if text == "WAKA Blast 38000 тяг":
            await handle_flavor_selection(update, context, "waka_blast", "WAKA Blast 38000 тяг", 1600)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров PUFFMI
    elif USER_STATES.get(user_id) == "puffmi_products":
        if text == "PUFFMI TANK 20000 тяг":
            await handle_flavor_selection(update, context, "puffmi_tank", "PUFFMI TANK 20000 тяг", 1650)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров INSTABAR
    elif USER_STATES.get(user_id) == "instabar_products":
        if text == "Instabar WT 15000 тяг":
            await handle_flavor_selection(update, context, "instabar_wt", "Instabar WT 15000 тяг", 800)
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка комплектующих
    elif USER_STATES.get(user_id) == "pod_accessories":
        if text == "Испарители":
            await update.message.reply_text(
                "❌ *Товар отсутствует*\n\n"
                "К сожалению, испарители временно отсутствуют в продаже. "
                "Выберите другие товары из каталога.",
                parse_mode="Markdown",
                reply_markup=back_to_catalog_keyboard()
            )
        elif text == "Картриджы":
            await show_cartridges(update, context)
        elif text == "⬅️ Назад в каталог":
            await back_to_catalog(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка картриджей
    elif USER_STATES.get(user_id) == "cartridges":
        if text == "PLONQ 3ml 0.4 Ом":
            if user_id not in USER_CARTS:
                USER_CARTS[user_id] = []

            found = False
            for item in USER_CARTS[user_id]:
                if item['name'] == "Картридж PLONQ 3ml 0.4 Ом":
                    item['quantity'] += 1
                    found = True
                    break

            if not found:
                USER_CARTS[user_id].append({
                    'name': "Картридж PLONQ 3ml 0.4 Ом",
                    'price': 400,
                    'quantity': 1
                })

            await update.message.reply_text(
                "✅ Картридж PLONQ 3ml 0.4 Ом добавлен в корзину!",
                parse_mode="Markdown"
            )
        elif text == "Vaporesso XROS 3ML 0.4 Ом":
            if user_id not in USER_CARTS:
                USER_CARTS[user_id] = []

            found = False
            for item in USER_CARTS[user_id]:
                if item['name'] == "Картридж Vaporesso XROS 3ML 0.4 Ом":
                    item['quantity'] += 1
                    found = True
                    break

            if not found:
                USER_CARTS[user_id].append({
                    'name': "Картридж Vaporesso XROS 3ML 0.4 Ом",
                    'price': 250,
                    'quantity': 1
                })

            await update.message.reply_text(
                "✅ Картридж Vaporesso XROS 3ML 0.4 Ом добавлен в корзину!",
                parse_mode="Markdown"
            )
        elif text == "⬅️ Назад к комплектующим":
            USER_STATES[user_id] = "pod_accessories"
            await show_pod_accessories(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка навигации
    elif text == "⬅️ Назад в каталог":
        await back_to_catalog(update, context)
    elif text == "⬅️ Назад к жидкостям":
        await back_to_liquids(update, context)
    elif text == "⬅️ Назад к одноразкам":
        await back_to_disposable(update, context)
    elif text == "⬅️ Назад к комплектующим":
        await back_to_accessories(update, context)

    # Обработка корзины
    elif text == "✅ Отправить заказ":
        await send_order(update, context)
    elif text == "✏️ Редактировать заказ":
        await edit_order(update, context)

    # Обработка редактирования корзины
    elif text.isdigit() and USER_STATES.get(user_id) == "editing_cart":
        item_num = int(text)
        cart = USER_CARTS.get(user_id, [])
        if 1 <= item_num <= len(cart):
            removed = cart.pop(item_num - 1)
            await update.message.reply_text(
                f"❌ Товар '{removed['name']}' удален из корзина",
                reply_markup=cart_keyboard()
            )
            USER_STATES[user_id] = "cart"
            await show_cart(update, context)
        else:
            await update.message.reply_text(
                "❌ Неверный номер товара",
                reply_markup=cart_keyboard()
            )
        return

    else:
        await update.message.reply_text(
            "Я не понял ваше сообщение. Пожалуйста, используйте кнопки меню или команду /start"
        )


# ---- Основная функция ----

def main() -> None:
    try:
        application = Application.builder().token(TOKEN).build()
        logger.info("Магазин CloudFM успешно запущен")
    except Exception as e:
        logger.error(f"Ошибка при создании приложения: {e}")
        return

    # Регистрация обработчиков команд пользователя
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Регистрация обработчиков команд администратора
    application.add_handler(CommandHandler("broadcast", admin_broadcast))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("admin_help", admin_help))
    application.add_handler(CommandHandler("stop", stop))

    # Регистрация обработчика инлайн кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Регистрация обработчиков сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    logger.info("Бот-магазин CloudFM запущен и работает")
    application.run_polling()


if __name__ == '__main__':
    main()
