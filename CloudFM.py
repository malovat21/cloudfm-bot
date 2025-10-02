import asyncio
import logging
import sqlite3
import csv
from typing import Dict, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    PersistenceInput,
    PicklePersistence
)

# Настройки с вашими данными
TOKEN = "8013532862:AAGG6ywOEfm7s6XgFJPBevxjIjmW_cZ8wZE"
ADMIN_IDS = [711876728, 789800147, 7664673453]
ADMIN_USERNAME = "@malovat21"

# ---- Функции для работы с CSV ----

def load_products_from_csv() -> List[Dict]:
    """Загружает список продуктов из CSV файла"""
    products = []
    try:
        with open('products.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Конвертируем цену в число и флаг в булево значение
                row['price'] = int(row['price'])
                row['has_flavors'] = row['has_flavors'].lower() == 'true'
                products.append(row)
        logging.info(f"Загружено {len(products)} товаров из CSV")
    except FileNotFoundError:
        logging.error("Файл products.csv не найден!")
    except Exception as e:
        logging.error(f"Ошибка при чтении products.csv: {e}")
    return products

def load_flavors_from_csv() -> Dict[str, List[str]]:
    """Загружает вкусы из CSV файла и группирует по product_id"""
    flavors_dict = {}
    try:
        with open('flavors.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                product_id = row['product_id']
                if product_id not in flavors_dict:
                    flavors_dict[product_id] = []
                flavors_dict[product_id].append(row['flavor_name'])
        logging.info(f"Загружено вкусов для {len(flavors_dict)} товаров из CSV")
    except FileNotFoundError:
        logging.error("Файл flavors.csv не найден!")
    except Exception as e:
        logging.error(f"Ошибка при чтении flavors.csv: {e}")
    return flavors_dict

# Глобальные переменные для хранения данных
PRODUCTS_DATA = load_products_from_csv()
FLAVORS_DATA = load_flavors_from_csv()

# ---- Функции для работы с базой данных ----

def init_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, is_active)
        VALUES (?, ?, ?, ?, 1)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE is_active = 1')
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def deactivate_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ---- Настройка логгирования ----

class Utf8FileHandler(logging.FileHandler):
    def __init__(self, filename, mode='a', encoding='utf-8', delay=False):
        super().__init__(filename, mode, encoding, delay)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = Utf8FileHandler("bot.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ---- Состояния и данные пользователей ----

USER_STATES = {}
USER_CARTS = {}
USER_CURRENT_PRODUCT = {}
USER_CURRENT_FLAVORS = {}

# ---- Клавиатуры ----

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

def liquids_brands_keyboard():
    # Динамически получаем бренды жидкостей из CSV
    brands = set()
    for product in PRODUCTS_DATA:
        if product['category'] == 'Жидкости':
            brands.add(product['brand'])
    
    # Сортируем бренды и ограничиваем по 3 в ряду
    sorted_brands = sorted(brands)
    keyboard = []
    row = []
    
    for i, brand in enumerate(sorted_brands):
        row.append(brand)
        # Максимум 3 кнопки в ряду
        if len(row) == 3 or i == len(sorted_brands) - 1:
            keyboard.append(row)
            row = []
    
    # Всегда добавляем кнопки навигации в отдельный ряд
    keyboard.append(["⬅️ Назад в каталог", "🏠 Главное меню"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def disposable_brands_keyboard():
    # Динамически получаем бренды одноразок из CSV
    brands = set()
    for product in PRODUCTS_DATA:
        if product['category'] == 'Одноразки':
            brands.add(product['brand'])
    
    # Сортируем бренды и ограничиваем по 3 в ряду
    sorted_brands = sorted(brands)
    keyboard = []
    row = []
    
    for i, brand in enumerate(sorted_brands):
        row.append(brand)
        # Максимум 3 кнопки в ряду
        if len(row) == 3 or i == len(sorted_brands) - 1:
            keyboard.append(row)
            row = []
    
    # Всегда добавляем кнопки навигации в отдельный ряд
    keyboard.append(["⬅️ Назад в каталог", "🏠 Главное меню"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_products_keyboard(category, brand):
    """Создает клавиатуру для товаров конкретного бренда"""
    products = []
    for product in PRODUCTS_DATA:
        if product['category'] == category and product['brand'] == brand:
            products.append(product['name'])
    
    keyboard = []
    row = []
    
    # Максимум 2 товара в ряду (так лучше смотрится)
    for i, product in enumerate(products):
        row.append(product)
        if len(row) == 2 or i == len(products) - 1:
            keyboard.append(row)
            row = []
    
    back_text = "⬅️ Назад к жидкостям" if category == "Жидкости" else "⬅️ Назад к одноразкам"
    keyboard.append([back_text, "🏠 Главное меню"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def back_to_catalog_keyboard():
    return ReplyKeyboardMarkup([
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)

def cart_keyboard():
    return ReplyKeyboardMarkup([
        ["✅ Отправить заказ", "✏️ Редактировать заказ"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)

def pod_accessories_keyboard():
    return ReplyKeyboardMarkup([
        ["Испарители", "Картриджы"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ], resize_keyboard=True)

def cartridges_keyboard():
    return ReplyKeyboardMarkup([
        ["PLONQ 3ml 0.4 Ом", "Vaporesso XROS 3ML 0.4 Ом"],
        ["⬅️ Назад к комплектующим", "🏠 Главное меню"]
    ], resize_keyboard=True)

# ---- Функции для администраторов ----

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Использование: /broadcast <сообщение>")
        return
    
    message = update.message.text.replace('/broadcast ', '', 1).strip()
    await send_broadcast(context, message)
    await update.message.reply_text("✅ Рассылка запущена!")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE("now")')
    new_today = cursor.fetchone()[0]
    conn.close()
    
    active_users = len(USER_CARTS)
    active_carts = sum(1 for cart in USER_CARTS.values() if cart)
    
    stats_text = f"📊 *Статистика бота:*\n\n"
    stats_text += f"👥 Всего пользователей: {total_users}\n"
    stats_text += f"📈 Новых сегодня: {new_today}\n"
    stats_text += f"🔥 Активных сессий: {active_users}\n"
    stats_text += f"🛒 Активных корзин: {active_carts}\n"
    stats_text += f"📝 Состояний пользователей: {len(USER_STATES)}\n"
    stats_text += f"📦 Товаров в каталоге: {len(PRODUCTS_DATA)}\n"
    stats_text += f"🎯 Вкусов загружено: {sum(len(v) for v in FLAVORS_DATA.values())}"
    
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
        "/reload - Перезагрузить данные из CSV\n"
        "/stop - Остановить бота\n"
        "/admin_help - Справка по командам админа\n\n"
        f"👑 Администраторы: {', '.join(str(admin_id) for admin_id in ADMIN_IDS)}"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def reload_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перезагружает данные из CSV файлов"""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ У вас нет прав для этой команды")
        return
    
    global PRODUCTS_DATA, FLAVORS_DATA
    PRODUCTS_DATA = load_products_from_csv()
    FLAVORS_DATA = load_flavors_from_csv()
    
    await update.message.reply_text(
        f"✅ Данные обновлены!\n"
        f"Товаров: {len(PRODUCTS_DATA)}\n"
        f"Товаров с вкусами: {len(FLAVORS_DATA)}"
    )
    logger.info(f"Data reloaded by admin {user.id}")

async def send_broadcast(context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
    success_count = 0
    fail_count = 0
    
    broadcast_text = (
        "📢 *РАССЫЛКА ОТ АДМИНИСТРАТОРА*\n\n"
        f"{message}\n\n"
        "_Это автоматическое сообщение, пожалуйста, не отвечайте на него._"
    )
    
    user_ids = get_all_users()
    
    if not user_ids:
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text="❌ Нет пользователей для рассылки",
                parse_mode="Markdown"
            )
        return
    
    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                parse_mode="Markdown"
            )
            success_count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Ошибка отправки рассылки пользователю {user_id}: {e}")
            deactivate_user(user_id)
            fail_count += 1
    
    report_text = (
        f"📊 *Отчет о рассылке:*\n\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не удалось отправить: {fail_count}\n"
        f"👥 Всего пользователей в базе: {len(user_ids)}\n"
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

    add_user(user.id, user.username, user.first_name, user.last_name)

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
        "- 📞 *Контакта* - связаться с нами\n"
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

async def show_disposable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "disposable_brands"

    await update.message.reply_text(
        "🚬 *Одноразовые электронные сигареты:*\n\n"
        "Выберите бренд:",
        reply_markup=disposable_brands_keyboard(),
        parse_mode="Markdown"
    )

async def show_pod_accessories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "pod_accessories"

    await update.message.reply_text(
        "⚙️ *Комплектующие для под-систем:*\n\n"
        "Выберите категорию комплектующих:",
        reply_markup=pod_accessories_keyboard(),
        parse_mode="Markdown"
    )

async def show_cartridges(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "cartridges"

    await update.message.reply_text(
        "🔧 *Картриджы для под-систем:*\n\n"
        "Выберите тип картриджа:",
        reply_markup=cartridges_keyboard(),
        parse_mode="Markdown"
    )

async def handle_brand_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, brand: str, category: str) -> None:
    user = update.effective_user
    USER_STATES[user.id] = f"{category.lower()}_products"
    
    # Получаем товары этого бренда
    products = [p for p in PRODUCTS_DATA if p['category'] == category and p['brand'] == brand]
    
    if not products:
        await update.message.reply_text(
            f"❌ Товары бренда {brand} временно отсутствуют",
            reply_markup=back_to_catalog_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    message_text = f"🎯 *Товары {brand}:*\n\n"
    for product in products:
        message_text += f"• {product['name']} - {product['price']} ₽\n"
    
    message_text += "\nВыберите продукт:"
    
    await update.message.reply_text(
        message_text,
        reply_markup=get_products_keyboard(category, brand),
        parse_mode="Markdown"
    )

async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, product_name: str) -> None:
    user = update.effective_user
    user_id = user.id
    
    # Находим продукт по имени
    product = None
    for p in PRODUCTS_DATA:
        if p['name'] == product_name:
            product = p
            break
    
    if not product:
        await update.message.reply_text("❌ Продукт не найден")
        return
    
    product_id = product['product_id']
    price = product['price']
    image_url = product['image_url']
    
    # Проверяем, есть ли вкусы у этого продукта
    if product['has_flavors'] and product_id in FLAVORS_DATA:
        flavors = FLAVORS_DATA[product_id]
        USER_CURRENT_PRODUCT[user_id] = product_id
        USER_CURRENT_FLAVORS[user_id] = flavors
        
        # Формируем сообщение со списком вкусов
        message_text = f"🎯 *{product_name}* - *{price} ₽*\n\n"
        message_text += "Выберите вкус:\n\n"
        for i, flavor in enumerate(flavors, 1):
            message_text += f"{i}. {flavor}\n"
        
        message_text += f"\n💵 Цена: *{price} ₽*"
        
        USER_STATES[user_id] = f"waiting_flavor_{product_id}"
        
        # Отправляем фото с описанием
        if image_url:
            await update.message.reply_photo(
                photo=image_url,
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
        if image_url:
            await update.message.reply_photo(
                photo=image_url,
                caption=f"✅ *{product_name}* - *{price} ₽* добавлен в корзину!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ *{product_name}* - *{price} ₽* добавлен в корзину!",
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

# ---- Обработчик инлайн кнопок ----

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    user_id = user.id

    await query.answer()

    # Обработка добавления в корзину
    if query.data.startswith("add_"):
        product_id = query.data[4:]
        
        # Проверяем, существует ли продукт
        product_exists = any(p['product_id'] == product_id for p in PRODUCTS_DATA)
        
        if product_exists:
            # Вызываем функцию обработки выбора вкуса
            await handle_flavor_selection_from_id(update, context, product_id)
        else:
            await query.edit_message_caption(
                caption="❌ Этот товар временно отсутствует",
                parse_mode="Markdown"
            )

async def handle_flavor_selection_from_id(update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: str):
    """Обработка выбора вкуса по product_id (для инлайн кнопок)"""
    user = update.effective_user
    user_id = user.id
    
    # Находим продукт по ID
    product = None
    for p in PRODUCTS_DATA:
        if p['product_id'] == product_id:
            product = p
            break
    
    if not product:
        await update.callback_query.edit_message_caption(
            caption="❌ Продукт не найден",
            parse_mode="Markdown"
        )
        return
    
    product_name = product['name']
    price = product['price']
    image_url = product['image_url']
    
    # Проверяем, есть ли вкусы у этого продукта
    if product['has_flavors'] and product_id in FLAVORS_DATA:
        flavors = FLAVORS_DATA[product_id]
        USER_CURRENT_PRODUCT[user_id] = product_id
        USER_CURRENT_FLAVORS[user_id] = flavors
        
        # Формируем сообщение со списком вкусов
        message_text = f"🎯 *{product_name}* - *{price} ₽*\n\n"
        message_text += "Выберите вкус:\n\n"
        for i, flavor in enumerate(flavors, 1):
            message_text += f"{i}. {flavor}\n"
        
        message_text += f"\n💵 Цена: *{price} ₽*"
        
        USER_STATES[user_id] = f"waiting_flavor_{product_id}"
        
        # Редактируем сообщение с фото
        if image_url:
            await update.callback_query.edit_message_caption(
                caption=message_text,
                parse_mode="Markdown"
            )
        else:
            await update.callback_query.edit_message_text(
                text=message_text,
                parse_mode="Markdown"
            )
        
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

        await update.callback_query.edit_message_caption(
            caption=f"✅ *{product_name}* - *{price} ₽* добавлен в корзину!",
            parse_mode="Markdown"
        )

# ---- Обработчики сообщений ----

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    user = update.effective_user
    user_id = user.id

    logger.info(f"=== ОБРАБОТКА СООБЩЕНИЯ ===")
    logger.info(f"Пользователь: {user_id}")
    logger.info(f"Текст: '{text}'")
    logger.info(f"Текущее состояние: {USER_STATES.get(user_id, 'не установлено')}")
    
    # Навигационные команды
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
    
    # Проверяем навигационные команды
    normalized_text = text.lower().strip()
    for command, handler in navigation_commands.items():
        if normalized_text == command.lower():
            await handler(update, context)
            if command in ["🏠 главное меню", "⬅️ назад в каталог", "🛒 каталог"]:
                USER_STATES[user_id] = "main_menu" if command == "🏠 главное меню" else "catalog_menu"
            return

    # Обработка выбора вкуса
    current_state = USER_STATES.get(user_id, "")
    if current_state.startswith("waiting_flavor_"):
        if text.isdigit():
            flavor_index = int(text) - 1
            product_id = USER_CURRENT_PRODUCT.get(user_id)
            flavors = USER_CURRENT_FLAVORS.get(user_id, [])
            
            if not product_id or not flavors:
                await update.message.reply_text("❌ Ошибка при выборе вкуса")
                return
            
            if 0 <= flavor_index < len(flavors):
                flavor = flavors[flavor_index]
                
                # Находим продукт
                product = None
                for p in PRODUCTS_DATA:
                    if p['product_id'] == product_id:
                        product = p
                        break
                
                if product:
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
    elif USER_STATES.get(user_id) == "liquids_brands":
        # Получаем все бренды жидкостей из CSV
        liquid_brands = set()
        for product in PRODUCTS_DATA:
            if product['category'] == 'Жидкости':
                liquid_brands.add(product['brand'])
        
        if text in liquid_brands:
            await handle_brand_selection(update, context, text, "Жидкости")

    # Обработка брендов одноразок
    elif USER_STATES.get(user_id) == "disposable_brands":
        # Получаем все бренды одноразок из CSV
        disposable_brands = set()
        for product in PRODUCTS_DATA:
            if product['category'] == 'Одноразки':
                disposable_brands.add(product['brand'])
        
        if text in disposable_brands:
            await handle_brand_selection(update, context, text, "Одноразки")

    # Обработка товаров жидкостей
    elif USER_STATES.get(user_id) in ["жидкости_products", "одноразки_products"]:
        category = "Жидкости" if USER_STATES[user_id] == "жидкости_products" else "Одноразки"
        
        # Проверяем, есть ли такой товар в CSV
        product_exists = any(p['name'] == text for p in PRODUCTS_DATA if p['category'] == category)
        
        if product_exists:
            await handle_product_selection(update, context, text)
        elif text in ["⬅️ Назад к жидкостям", "⬅️ Назад к одноразкам"]:
            if "жидкости" in text:
                await back_to_liquids(update, context)
            else:
                await back_to_disposable(update, context)
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
            await handle_product_selection(update, context, "Картридж PLONQ 3ml 0.4 Ом")
        elif text == "Vaporesso XROS 3ML 0.4 Ом":
            await handle_product_selection(update, context, "Картридж Vaporesso XROS 3ML 0.4 Ом")
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
    # Инициализируем базу данных
    init_database()
    
    try:
        persistence = PicklePersistence(filepath="bot_persistence")
        application = Application.builder().token(TOKEN).persistence(persistence).build()
        logger.info("Магазин CloudFM успешно запущен")
    except Exception as e:
        logger.error(f"Ошибка при создании приложения: {e}")
        return

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("broadcast", admin_broadcast))
    application.add_handler(CommandHandler("stats", admin_stats))
    application.add_handler(CommandHandler("admin_help", admin_help))
    application.add_handler(CommandHandler("reload", reload_data))
    application.add_handler(CommandHandler("stop", stop))

    # Регистрация обработчика инлайн кнопок
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Регистрация обработчиков сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    logger.info("Бот-магазин CloudFM запущен и работает")
    logger.info(f"Загружено {len(PRODUCTS_DATA)} товаров и {sum(len(v) for v in FLAVORS_DATA.values())} вкусов")
    application.run_polling()

if __name__ == '__main__':
    main()


