import asyncio
import logging
import sqlite3
import csv
import re
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

def clean_string(text: str) -> str:
    """Очищает строку от лишних символов и нормализует пробелы"""
    if not text:
        return ""
    # Удаляем лишние пробелы и непечатаемые символы
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def normalize_category(category: str) -> str:
    """Нормализует названия категорий"""
    category = clean_string(category)
    
    # Исправляем опечатки и варианты написания
    category_mapping = {
        'фодноразки': 'Одноразки',
        'одноразки': 'Одноразки',
        'жидкости': 'Жидкости',
        'комплектующие для под систем': 'Комплектующие',
        'комплектующие': 'Комплектующие'
    }
    
    lower_category = category.lower()
    return category_mapping.get(lower_category, category)

def load_products_from_csv() -> List[Dict]:
    """Загружает список продуктов из CSV файла"""
    products = []
    try:
        with open('products.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, 1):
                # Пропускаем пустые строки
                if not any(row.values()):
                    continue
                
                # Очищаем и нормализуем данные
                cleaned_row = {}
                for key, value in row.items():
                    cleaned_key = clean_string(key)
                    cleaned_value = clean_string(value)
                    cleaned_row[cleaned_key] = cleaned_value
                
                # Проверяем наличие обязательных полей
                if 'price' not in cleaned_row or not cleaned_row['price']:
                    logging.warning(f"Пропущен продукт без цены в строке {row_num}: {cleaned_row}")
                    continue
                
                # Нормализуем категорию
                if 'category' in cleaned_row:
                    cleaned_row['category'] = normalize_category(cleaned_row['category'])
                
                # Конвертируем цену в число и флаг в булево значение
                try:
                    cleaned_row['price'] = int(cleaned_row['price'])
                    cleaned_row['has_flavors'] = cleaned_row.get('has_flavors', 'false').lower() == 'true'
                    
                    # Добавляем значения по умолчанию для отсутствующих полей
                    cleaned_row['category'] = cleaned_row.get('category', '')
                    cleaned_row['brand'] = cleaned_row.get('brand', '')
                    cleaned_row['subcategory'] = cleaned_row.get('subcategory', '')
                    cleaned_row['product_id'] = cleaned_row.get('product_id', '')
                    cleaned_row['image_url'] = cleaned_row.get('image_url', '')
                    cleaned_row['name'] = cleaned_row.get('name', '')
                    
                    products.append(cleaned_row)
                except (ValueError, KeyError) as e:
                    logging.error(f"Ошибка обработки строки {row_num} {cleaned_row}: {e}")
                    continue
                    
        logging.info(f"Загружено {len(products)} товаров из CSV")
        
        # Логируем статистику по категориям для отладки
        category_stats = {}
        for product in products:
            category = product.get('category', 'Без категории')
            category_stats[category] = category_stats.get(category, 0) + 1
        
        for category, count in category_stats.items():
            logging.info(f"Категория '{category}': {count} товаров")
            
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
                # Пропускаем пустые строки
                if not any(row.values()):
                    continue
                    
                product_id = clean_string(row.get('product_id', ''))
                flavor_name = clean_string(row.get('flavor_name', ''))
                
                if product_id and flavor_name:
                    if product_id not in flavors_dict:
                        flavors_dict[product_id] = []
                    flavors_dict[product_id].append(flavor_name)
                    
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
    """Клавиатура для брендов жидкостей"""
    brands = set()
    for product in PRODUCTS_DATA:
        category = product.get('category', '')
        if category == 'Жидкости':
            brand = product.get('brand', '')
            if brand:
                brands.add(brand)
    
    if not brands:
        return ReplyKeyboardMarkup([
            ["⬅️ Назад в каталог", "🏠 Главное меню"]
        ], resize_keyboard=True)
    
    # Сортируем бренды и создаем клавиатуру
    sorted_brands = sorted(brands)
    keyboard = []
    row = []
    
    for i, brand in enumerate(sorted_brands):
        row.append(brand)
        if len(row) == 3 or i == len(sorted_brands) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append(["⬅️ Назад в каталог", "🏠 Главное меню"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def disposable_brands_keyboard():
    """Клавиатура для брендов одноразок"""
    brands = set()
    for product in PRODUCTS_DATA:
        category = product.get('category', '')
        if category == 'Одноразки':
            brand = product.get('brand', '')
            if brand:
                brands.add(brand)
    
    if not brands:
        return ReplyKeyboardMarkup([
            ["⬅️ Назад в каталог", "🏠 Главное меню"]
        ], resize_keyboard=True)
    
    # Сортируем бренды и создаем клавиатуру
    sorted_brands = sorted(brands)
    keyboard = []
    row = []
    
    for i, brand in enumerate(sorted_brands):
        row.append(brand)
        if len(row) == 3 or i == len(sorted_brands) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append(["⬅️ Назад в каталог", "🏠 Главное меню"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_products_keyboard(category, brand):
    """Создает клавиатуру для товаров конкретного бренда"""
    products = []
    for product in PRODUCTS_DATA:
        product_category = product.get('category', '')
        product_brand = product.get('brand', '')
        if product_category == category and product_brand == brand:
            product_name = product.get('name', '')
            if product_name:
                products.append(product_name)
    
    keyboard = []
    row = []
    
    # Максимум 2 товара в ряду
    for i, product in enumerate(products):
        row.append(product)
        if len(row) == 2 or i == len(products) - 1:
            keyboard.append(row)
            row = []
    
    if not keyboard:
        keyboard.append(["Товары временно отсутствуют"])
    
    back_text = "⬅️ Назад к жидкостям" if category == "Жидкости" else "⬅️ Назад к одноразкам"
    keyboard.append([back_text, "🏠 Главное меню"])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_accessories_categories_keyboard():
    """Создает клавиатуру для категорий комплектующих"""
    categories = set()
    for product in PRODUCTS_DATA:
        category = product.get('category', '')
        if category == 'Комплектующие':
            subcategory = product.get('subcategory', '')
            if subcategory:
                categories.add(subcategory)
    
    if not categories:
        return ReplyKeyboardMarkup([
            ["⬅️ Назад в каталог", "🏠 Главное меню"]
        ], resize_keyboard=True)
    
    keyboard = []
    row = []
    
    for i, category in enumerate(sorted(categories)):
        row.append(category)
        if len(row) == 2 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append(["⬅️ Назад в каталог", "🏠 Главное меню"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_accessory_products_keyboard(category: str):
    """Создает клавиатуру для товаров конкретной категории комплектующих"""
    products = []
    for product in PRODUCTS_DATA:
        product_category = product.get('category', '')
        product_subcategory = product.get('subcategory', '')
        if product_category == 'Комплектующие' and product_subcategory == category:
            product_name = product.get('name', '')
            if product_name:
                products.append(product_name)
    
    keyboard = []
    row = []
    
    for i, product in enumerate(products):
        row.append(product)
        if len(row) == 2 or i == len(products) - 1:
            keyboard.append(row)
            row = []
    
    if not keyboard:
        keyboard.append(["Товары временно отсутствуют"])
    
    keyboard.append(["⬅️ Назад к комплектующим", "🏠 Главное меню"])
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

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "catalog_menu"

    await update.message.reply_text(
        "🛒 *Выберите категорию товаров:*\n\n"
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

    # Проверяем есть ли жидкости в каталоге
    has_liquids = any(product.get('category') == 'Жидкости' for product in PRODUCTS_DATA)
    
    if not has_liquids:
        await update.message.reply_text(
            "❌ *Жидкости временно отсутствуют*\n\n"
            "К сожалению, жидкости временно отсутствуют в продаже. "
            "Выберите другие товары из каталога.",
            parse_mode="Markdown",
            reply_markup=back_to_catalog_keyboard()
        )
        return

    await update.message.reply_text(
        "💧 *Выберите бренд жидкости:*",
        reply_markup=liquids_brands_keyboard(),
        parse_mode="Markdown"
    )

async def show_disposable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "disposable_brands"

    # Проверяем есть ли одноразки в каталоге
    has_disposable = any(product.get('category') == 'Одноразки' for product in PRODUCTS_DATA)
    
    if not has_disposable:
        await update.message.reply_text(
            "❌ *Одноразки временно отсутствуют*\n\n"
            "К сожалению, одноразки временно отсутствуют в продаже. "
            "Выберите другие товары из каталога.",
            parse_mode="Markdown",
            reply_markup=back_to_catalog_keyboard()
        )
        return

    await update.message.reply_text(
        "🚬 *Одноразовые электронные сигареты:*\n\n"
        "Выберите бренд:",
        reply_markup=disposable_brands_keyboard(),
        parse_mode="Markdown"
    )

async def show_pod_accessories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    USER_STATES[user.id] = "pod_accessories"
    
    # Проверяем есть ли комплектующие в каталоге
    has_accessories = any(product.get('category') == 'Комплектующие' for product in PRODUCTS_DATA)
    
    if not has_accessories:
        await update.message.reply_text(
            "❌ *Комплектующие временно отсутствуют*\n\n"
            "К сожалению, комплектующие временно отсутствуют в продаже. "
            "Выберите другие товары из каталога.",
            parse_mode="Markdown",
            reply_markup=back_to_catalog_keyboard()
        )
        return

    await update.message.reply_text(
        "⚙️ *Комплектующие для под-систем:*\n\n"
        "Выберите категорию:",
        reply_markup=get_accessories_categories_keyboard(),
        parse_mode="Markdown"
    )

async def handle_brand_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, brand: str, category: str) -> None:
    user = update.effective_user
    USER_STATES[user.id] = f"{category.lower()}_products"
    
    # Получаем товары этого бренда
    products = []
    for p in PRODUCTS_DATA:
        product_category = p.get('category', '')
        product_brand = p.get('brand', '')
        if product_category == category and product_brand == brand:
            products.append(p)
    
    if not products:
        await update.message.reply_text(
            f"❌ Товары бренда {brand} временно отсутствуют",
            reply_markup=back_to_catalog_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    message_text = f"🎯 *Товары {brand}:*\n\n"
    for product in products:
        product_name = product.get('name', 'Без названия')
        product_price = product.get('price', 0)
        message_text += f"• {product_name} - {product_price} ₽\n"
    
    message_text += "\nВыберите продукт:"
    
    await update.message.reply_text(
        message_text,
        reply_markup=get_products_keyboard(category, brand),
        parse_mode="Markdown"
    )

async def show_accessory_products(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    user = update.effective_user
    USER_STATES[user.id] = f"accessory_{category}"
    
    # Получаем товары этой категории
    products = []
    for product in PRODUCTS_DATA:
        product_category = product.get('category', '')
        product_subcategory = product.get('subcategory', '')
        if product_category == 'Комплектующие' and product_subcategory == category:
            products.append(product)
    
    if not products:
        await update.message.reply_text(
            f"❌ Товары в категории '{category}' временно отсутствуют",
            reply_markup=get_accessories_categories_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    message_text = f"🔧 *Товары {category}:*\n\n"
    for product in products:
        product_name = product.get('name', 'Без названия')
        product_price = product.get('price', 0)
        message_text += f"• {product_name} - {product_price} ₽\n"
    
    message_text += "\nВыберите продукт:"
    
    await update.message.reply_text(
        message_text,
        reply_markup=get_accessory_products_keyboard(category),
        parse_mode="Markdown"
    )

async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, product_name: str) -> None:
    user = update.effective_user
    user_id = user.id
    
    # Находим продукт по имени
    product = None
    for p in PRODUCTS_DATA:
        if p.get('name') == product_name:
            product = p
            break
    
    if not product:
        await update.message.reply_text("❌ Продукт не найден")
        return
    
    product_id = product.get('product_id', '')
    price = product.get('price', 0)
    image_url = product.get('image_url', '')
    
    # Проверяем, есть ли вкусы у этого продукта
    has_flavors = product.get('has_flavors', False)
    if has_flavors and product_id in FLAVORS_DATA:
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

# ... (остальные функции остаются такими же, как в предыдущем исправленном коде)

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

# ... (остальной код обработчиков сообщений и команд остается без изменений)

def main() -> None:
    # Инициализируем базу данных
    init_database()
    
    try:
        persistence = PicklePersistence(filepath="bot_persistence")
        application = Application.builder().token(TOKEN).persistence(persistence).build()
        logger.info("Магазин CloudFM успешно запущен")
        
        # Логируем загруженные категории для отладки
        categories = set()
        for product in PRODUCTS_DATA:
            category = product.get('category', 'Без категории')
            categories.add(category)
        logger.info(f"Загружены категории: {', '.join(categories)}")
        
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
