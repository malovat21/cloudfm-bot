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
        ["🌿 Снюс", "🔧 Под-системы"],
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


# ---- Основные функции магазина ----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "main_menu"
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
        "• 🌿 Снюс и никотиновые пакетики\n"
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
        "Выберите продукт:",
        reply_markup=husky_products_keyboard(),
        parse_mode="Markdown"
    )


# Функция для показа товаров PODONKI
async def show_podonki_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "podonki_products"

    await update.message.reply_text(
        "💧 *Т товары PODONKI:*\n\n"
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
        "Выберите продукт:",
        reply_markup=rell_products_keyboard(),
        parse_mode="Markdown"
    )


# НОВЫЕ ФУНКЦИИ ДЛЯ ОДНОРАЗОК

async def show_hqd_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "hqd_products"

    await update.message.reply_text(
        "🚬 *Товары HQD:*\n\n"
        "Выберите продукт:",
        reply_markup=hqd_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_elfbar_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "elfbar_products"

    await update.message.reply_text(
        "🚬 *Товары ELF BAR:*\n\n"
        "Выберите продукт:",
        reply_markup=elfbar_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_lostmary_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "lostmary_products"

    await update.message.reply_text(
        "🚬 *Товары LOST MARY:*\n\n"
        "Выберите продукт:",
        reply_markup=lostmary_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_plonq_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "plonq_products"

    await update.message.reply_text(
        "🚬 *Товары PLONQ:*\n\n"
        "Выберите продукт:",
        reply_markup=plonq_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_waka_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "waka_products"

    await update.message.reply_text(
        "🚬 *Товары WAKA:*\n\n"
        "Выберите продукт:",
        reply_markup=waka_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_puffmi_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "puffmi_products"

    await update.message.reply_text(
        "🚬 *Товары PUFFMI:*\n\n"
        "Выберите продукт:",
        reply_markup=puffmi_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_instabar_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "instabar_products"

    await update.message.reply_text(
        "🚬 *Товары INSTABAR:*\n\n"
        "Выберите продукт:",
        reply_markup=instabar_products_keyboard(),
        parse_mode="Markdown"
    )


async def show_snus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "snus_brands"

    await update.message.reply_text(
        "🌿 *Снюс:*\n\n"
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
        "• *Самовывоз:* Адрес уточняется при заказе (Пн-Вс 10:00-22:00)\n"
        "• *Доставка по городу:* Бесплатно при заказе от 1500 ₽\n"
        "• *Доставка в регионы:* От 300 ₽ (срок 1-3 дня)\n"
        "• *Экспресс-доставка:* 500 ₽ (в течение 2 часов)\n\n"
        "Все заказы оформляются анонимно!"
    )
    await update.message.reply_text(info, parse_mode="Markdown")


async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    contact_info = (
        "📞 *Контакты магазина CloudFM*\n\n"
        "• Телеграм: @CloudFMMSC\n"
        "Часы работы: 24/7\n\n"
        "По вопросам оптовых закупок: @CloudFMMSC"
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

    cart_text = "✏️ *Редактирование корзины*\n\n"
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
            "hqd_neo_x": {"name": "HQD NEO X 25000 тяг", "price": 1200},
            "hqd_glaze": {"name": "HQD Glaze 12000 тяг", "price": 800},
            "elfbar_nic_king": {"name": "ELF BAR NIC KING 30000 тяг", "price": 1500},
            "lost_mary_os": {"name": "Lost Mary OS 25000 тяг", "price": 1300},
            "plonq_ultra": {"name": "Plonq Ultra 12000 тяг", "price": 900},
            "plonq_roqy_l": {"name": "Plonq Roqy L 20000 тяг", "price": 1100},
            "waka_blast": {"name": "WAKA Blast 38000 тяг", "price": 1800},
            "puffmi_tank": {"name": "PUFFMI TANK 20000 тяг", "price": 1200},
            "instabar_wt": {"name": "Instabar WT 15000 тяг", "price": 1000},
            # Новые картриджи
            "plonq_cartridge": {"name": "Картридж PLONQ 3ml 0.4 Ом", "price": 400},
            "vaporesso_cartridge": {"name": "Картридж Vaporesso XROS 3ML 0.4 Ом", "price": 300}
        }

        if product_id in products:
            product = products[product_id]
            product_name = product["name"]
            price = product["price"]

            # Добавляем товар в корзину
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

            await query.edit_message_caption(
                caption=query.message.caption + f"\n\n✅ *Добавлено в корзину!*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard(product_id)
            )

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
    elif text == "🌿 Снюс":
        await update.message.reply_text(
            "❌ *Товар отсутствует*\n\n"
            "К сожалению, снюс временно отсутствует в продаже. "
            "Выберите другие товары из каталога.",
            parse_mode="Markdown",
            reply_markup=back_to_catalog_keyboard()
        )
    elif text == "🔧 Под-системы":
        await update.message.reply_text(
            "❌ *Товар отсутствует*\n\n"
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
            USER_CURRENT_PRODUCT[user_id] = "husky_malaysian"
            photo_url = "https://iimg.su/i/QxOz3w"
            await update.message.reply_photo(
                photo=photo_url,
                caption="💧 *HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml*\n\nЦена: *400 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("husky_malaysian")
            )
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров PODONKI
    elif USER_STATES.get(user_id) == "podonki_products":
        if text == "PODONKI ARCADE Salt 2% 30 ml":
            USER_CURRENT_PRODUCT[user_id] = "podonki_arcade"
            photo_url = "https://iimg.su/i/Bkw383"
            await update.message.reply_photo(
                photo=photo_url,
                caption="💧 *PODONKI ARCADE Salt 2% 30 ml*\n\nЦена: *400 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("podonki_arcade")
            )
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров CATSWILL
    elif USER_STATES.get(user_id) == "catswill_products":
        if text == "CATSWILL Salt 2% 30 ml":
            USER_CURRENT_PRODUCT[user_id] = "catswill"
            photo_url = "https://iimg.su/i/J8MdO8"
            await update.message.reply_photo(
                photo=photo_url,
                caption="💧 *CATSWILL Salt 2% 30 ml*\n\nЦена: *450 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("catswill")
            )
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров MAXWELLS
    elif USER_STATES.get(user_id) == "maxwells_products":
        if text == "MAXWELLS Salt 2% 30 ml":
            USER_CURRENT_PRODUCT[user_id] = "maxwells"
            photo_url = "https://iimg.su/i/3ElcUl"
            await update.message.reply_photo(
                photo=photo_url,
                caption="💧 *MAXWELLS Salt 2% 30 ml*\n\nЦена: *400 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("maxwells")
            )
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров Rell
    elif USER_STATES.get(user_id) == "rell_products":
        if text == "Rell Green Salt 2% 30 ml":
            USER_CURRENT_PRODUCT[user_id] = "rell_green"
            photo_url = "https://iimg.su/i/0KnwNB"
            await update.message.reply_photo(
                photo=photo_url,
                caption="💧 *Rell Green Salt 2% 30 ml*\n\nЦена: *450 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("rell_green")
            )
        elif text == "Rell Ultima Salt 2% 30 ml":
            USER_CURRENT_PRODUCT[user_id] = "rell_ultima"
            photo_url = "https://iimg.su/i/tZq4Bl"
            await update.message.reply_photo(
                photo=photo_url,
                caption="💧 *Rell Ultima Salt 2% 30 ml*\n\nЦена: *600 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("rell_ultima")
            )
        elif text == "⬅️ Назад к жидкостям":
            USER_STATES[user_id] = "liquids_brands"
            await show_liquids(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров HQD
    elif USER_STATES.get(user_id) == "hqd_products":
        if text == "HQD NEO X 25000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "hqd_neo_x"
            photo_url = "https://iimg.su/i/nPspGQ"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *HQD NEO X 25000 тяг*\n\nКоличество тяг: 25000\nЦена: *1200 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("hqd_neo_x")
            )
        elif text == "HQD Glaze 12000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "hqd_glaze"
            photo_url = "https://iimg.su/i/4KJr2t"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *HQD Glaze 12000 тяг*\n\nКоличество тяг: 12000\nЦена: *800 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("hqd_glaze")
            )
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров ELF BAR
    elif USER_STATES.get(user_id) == "elfbar_products":
        if text == "ELF BAR NIC KING 30000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "elfbar_nic_king"
            photo_url = "https://iimg.su/i/QmBAIU"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *ELF BAR NIC KING 30000 тяг*\n\nКоличество тяг: 30000\nЦена: *1500 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("elfbar_nic_king")
            )
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров LOST MARY
    elif USER_STATES.get(user_id) == "lostmary_products":
        if text == "Lost Mary OS 25000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "lost_mary_os"
            photo_url = "https://iimg.su/i/RfstON"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *Lost Mary OS 25000 тяг*\n\nКоличество тяг: 25000\nЦена: *1300 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("lost_mary_os")
            )
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров PLONQ
    elif USER_STATES.get(user_id) == "plonq_products":
        if text == "Plonq Ultra 12000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "plonq_ultra"
            photo_url = "https://iimg.su/i/sUggA0"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *Plonq Ultra 12000 тяг*\n\nКоличество тяг: 12000\nЦена: *900 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("plonq_ultra")
            )
        elif text == "Plonq Roqy L 20000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "plonq_roqy_l"
            photo_url = "https://iimg.su/i/tMBFds"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *Plonq Roqy L 20000 тяг*\n\nКоличество тяг: 20000\nЦена: *1100 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("plonq_roqy_l")
            )
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров WAKA
    elif USER_STATES.get(user_id) == "waka_products":
        if text == "WAKA Blast 38000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "waka_blast"
            photo_url = "https://iimg.su/i/DjZBoz"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *WAKA Blast 38000 тяг*\n\nКоличество тяг: 38000\nЦена: *1800 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("waka_blast")
            )
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товары PUFFMI
    elif USER_STATES.get(user_id) == "puffmi_products":
        if text == "PUFFMI TANK 20000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "puffmi_tank"
            photo_url = "https://iimg.su/i/t1ibma"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *PUFFMI TANK 20000 тяг*\n\nКоличество тяг: 20000\nЦена: *1200 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("puffmi_tank")
            )
        elif text == "⬅️ Назад к одноразкам":
            USER_STATES[user_id] = "disposable_brands"
            await show_disposable(update, context)
        elif text == "🏠 Главное меню":
            await back_to_main(update, context)

    # Обработка товаров INSTABAR
    elif USER_STATES.get(user_id) == "instabar_products":
        if text == "Instabar WT 15000 тяг":
            USER_CURRENT_PRODUCT[user_id] = "instabar_wt"
            photo_url = "https://iimg.su/i/ebkUPF"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🚬 *Instabar WT 15000 тяг*\n\nКоличество тяг: 15000\nЦена: *1000 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("instabar_wt")
            )
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
            USER_CURRENT_PRODUCT[user_id] = "plonq_cartridge"
            photo_url = "https://iimg.su/i/L8HJGr"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🔧 *Картридж PLONQ 3ml 0.4 Ом*\n\nОбъем: 3ml\nСопротивление: 0.4 Ом\nЦена: *400 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("plonq_cartridge")
            )
        elif text == "Vaporesso XROS 3ML 0.4 Ом":
            USER_CURRENT_PRODUCT[user_id] = "vaporesso_cartridge"
            photo_url = "https://iimg.su/i/BGCTN4"
            await update.message.reply_photo(
                photo=photo_url,
                caption="🔧 *Картридж Vaporesso XROS 3ML 0.4 Ом*\n\nОбъем: 3ml\nСопротивление: 0.4 Ом\nЦена: *300 ₽*",
                parse_mode="Markdown",
                reply_markup=add_to_cart_keyboard("vaporesso_cartridge")
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

    # Обработка добавления товаров (для старых товаров)
    elif text.isdigit() and USER_STATES.get(user_id) not in ["editing_cart"]:
        num = int(text)
        if 1 <= num <= 5:
            product_name = f"Товар #{num}"
            price = 500 + num * 100

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

            await update.message.reply_text(
                f"✅ Товар #{num} добавлен в корзину!\n"
                "Продолжайте покупки или перейдите в 🛍️ Корзину",
                parse_mode="Markdown"
            )
            return

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

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
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