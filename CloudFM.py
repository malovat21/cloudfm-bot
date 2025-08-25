import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

# Настройки
TOKEN = "8013532862:AAGG6ywOEfm7s6XgFJPBevxjIjmW_cZ8wZE"
ADMIN_IDS = [711876728, 789800147]

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Состояния и данные пользователей
USER_STATES = {}
USER_CARTS = {}
USER_CURRENT_SELECTION = {}

# Структурированные данные товаров
PRODUCTS = {
    "liquids": {
        "HUSKY": {
            "HUSKY IMPORT MALAYSIAN SALT (20MG) 30 ml": {
                "price": 400,
                "flavors": ["Gum Wolf (Арбузная жвачка)", "Sour Beast (Киви, клубника и перечная мята)"],
                "image": "https://iimg.su/i/QxOz3w"
            }
        },
        "PODONKI": {
            "PODONKI ARCADE Salt 2% 30 ml": {
                "price": 400,
                "flavors": ["Виноград Ежевика", "Вишневый энергетик", "Лимонад Голубика", "Манго Маракуйя", "Цитрусовый Микс"],
                "image": "https://iimg.su/i/Bkw383"
            }
        },
        "CATSWILL": {
            "CATSWILL Salt 2% 30 ml": {
                "price": 450,
                "flavors": ["Вишня Персик Мята", "Имбирный Лимонад с Малиной", "Кислый Малиновый Скитлс", 
                           "Лимонад Ежевика Сироп", "Мамба Кислое Яблоко Киви", "Скитлс из Винограда Изабеллы"],
                "image": "https://iimg.su/i/J8MdO8"
            }
        },
        "MAXWELLS": {
            "MAXWELLS Salt 2% 30 ml": {
                "price": 400,
                "flavors": ["Алтай", "Ягодный Мармелад", "Зеленый чаc с ягодами"],
                "image": "https://iimg.su/i/3ElcUl"
            }
        },
        "Rell": {
            "Rell Green Salt 2% 30 ml": {
                "price": 450,
                "flavors": ["Grapefruit (Грейпфрут)", "Nord Ice Nectarine (Северный Нектарин)", 
                           "Papaya Banana (Папайя с Бананом)", "Passion Citrus (Цитрус Маракуйя)",
                           "Pineapple Lemon (Ананас Лимон)", "Tropical Smoothie (Тропический Смузи)"],
                "image": "https://iimg.su/i/0KnwNB"
            },
            "Rell Ultima Salt 2% 30 ml": {
                "price": 600,
                "flavors": ["Jasmine Raspberry (Жасмин Малина)", "Kiwi Guava (Киви Гуава)", 
                           "Peach Grape (Персик Виноград)", "Peach Tea (Персиковый чай)"],
                "image": "https://iimg.su/i/tZq4Bl"
            }
        }
    },
    "disposables": {
        "HQD": {
            "HQD NEO X 25000 тяг": {
                "price": 1600,
                "flavors": ["Киви маракуйя гуава", "Малина лимон арбуз"],
                "image": "https://iimg.su/i/nPspGQ"
            },
            "HQD Glaze 12000 тяг": {
                "price": 1350,
                "flavors": ["Виноград Малина", "Черная смородина", "Черника"],
                "image": "https://iimg.su/i/4KJr2t"
            }
        },
        "ELF BAR": {
            "ELF BAR NIC KING 30000 тяг": {
                "price": 1450,
                "flavors": ["Арбуз Вишня", "Виноград Клюква", "Черника Малина лёд"],
                "image": "https://iimg.su/i/Q8bqko"
            }
        },
        "LOST MARY": {
            "Lost Mary OS 25000 тяг": {
                "price": 1400,
                "flavors": ["Ананас Апельсин", "Вишня Малина Лайм", "Кислый виноград лёд"],
                "image": "https://iimg.su/i/IMFhAh"
            }
        },
        "PLONQ": {
            "Plonq Ultra 12000 тяг": {
                "price": 1850,
                "flavors": ["Виноград", "Голубика Малина", "Клубника Манго", "Смородина"],
                "image": "https://iimg.su/i/sUggA0"
            },
            "Plonq Roqy L 20000 тяг": {
                "price": 1700,
                "flavors": ["Вишня Черника Клюква", "Кислое Киви Маракуйя", "Сакура Виноград"],
                "image": "https://iimg.su/i/tMBFds"
            }
        },
        "WAKA": {
            "WAKA Blast 38000 тяг": {
                "price": 1600,
                "flavors": ["Лимон Лайм + Ментол микс"],
                "image": "https://iimg.su/i/DjZBoz"
            }
        },
        "PUFFMI": {
            "PUFFMI TANK 20000 тяг": {
                "price": 1650,
                "flavors": ["Blueberry ice - Черничный лёд", "Pomegranate Lime - Гранат Лайм"],
                "image": "https://iimg.su/i/t1ibma"
            }
        },
        "INSTABAR": {
            "Instabar WT 15000 тяг": {
                "price": 800,
                "flavors": ["Сакура Виноград", "Ананас Кокос", "Арбузный Коктейль", "Вишня Персик Лимон"],
                "image": "https://iimg.su/i/53MBuB"
            }
        }
    },
    "accessories": {
        "cartridges": {
            "PLONQ 3ml 0.4 Ом": {"price": 400, "image": "https://iimg.su/i/L8HJGr"},
            "Vaporesso XROS 3ML 0.4 Ом": {"price": 250, "image": "https://iimg.su/i/BGCTN4"}
        }
    }
}

# Универсальные функции для создания клавиатур
def create_keyboard(buttons, rows=2, resize=True):
    """Создание клавиатуры из списка кнопок"""
    keyboard = [buttons[i:i+rows] for i in range(0, len(buttons), rows)]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=resize)

# Стандартные клавиатуры
def main_menu_keyboard():
    return create_keyboard([
        ["🛒 Каталог", "🛍️ Корзина"],
        ["🚚 Доставка", "❓ Помощь"],
        ["📞 Контакты"]
    ])

def catalog_menu_keyboard():
    return create_keyboard([
        ["💧 Жидкости", "🚬 Одноразки"],
        ["🌿 Жевательный табак", "🔧 Под-системы"],
        ["⚙️ Комплектующие", "🏠 Главное меню"]
    ])

def back_keyboard(back_to="каталог"):
    return create_keyboard([f"⬅️ Назад в {back_to}", "🏠 Главное меню"])

def cart_keyboard():
    return create_keyboard([
        ["✅ Отправить заказ", "✏️ Редактировать заказ"],
        ["⬅️ Назад в каталог", "🏠 Главное меню"]
    ])

# Основные команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_STATES[user.id] = "main_menu"
    USER_CARTS[user.id] = []

    await update.message.reply_text(
        f"👋 Добро пожаловать в *CloudFM*, {user.first_name}!\n\n"
        "Мы предлагаем лучшие товары для вейпинга с быстрой доставкой!",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Справка по магазину CloudFM*\n\n"
        "Вот что вы можете сделать:\n"
        "- 🛒 *Каталог* - просмотреть товары\n"
        "- 🛍️ *Корзина* - посмотреть ваши заказы\n"
        "- 🚚 *Доставка* - узнать условия доставки\n"
        "- 📞 *Контакты* - связаться с нами",
        parse_mode="Markdown"
    )

async def delivery_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚚 *Условия доставки CloudFM*\n\n"
        "• *Самовывоз:* Адрес уточняется при заказе\n"
        "• *Доставка по городу:* Бесплатно от 1500 ₽\n"
        "• *Доставка в регионы:* От 300 ₽ (1-3 дня)\n"
        "• *Экспресс-доставка:* 500 ₽ (2 часа)",
        parse_mode="Markdown"
    )

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Контакты магазина CloudFM*\n\n"
        "• Телеграм: @CloudFMMSC\n"
        "• Часы работы: 24/7\n\n"
        "Оптовые закупки: @CloudFMMSC",
        parse_mode="Markdown"
    )

# Навигация по каталогу
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_STATES[user.id] = "catalog_menu"

    await update.message.reply_text(
        "🛒 *Выберите категорию товаров:*",
        reply_markup=catalog_menu_keyboard(),
        parse_mode="Markdown"
    )

async def show_liquids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_STATES[user.id] = "liquids_brands"

    brands = list(PRODUCTS["liquids"].keys())
    await update.message.reply_text(
        "💧 *Выберите бренд жидкости:*",
        reply_markup=create_keyboard(brands + ["⬅️ Назад в каталог", "🏠 Главное меню"]),
        parse_mode="Markdown"
    )

async def show_disposables(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_STATES[user.id] = "disposables_brands"

    brands = list(PRODUCTS["disposables"].keys())
    await update.message.reply_text(
        "🚬 *Выберите бренд одноразок:*",
        reply_markup=create_keyboard(brands + ["⬅️ Назад в каталог", "🏠 Главное меню"]),
        parse_mode="Markdown"
    )

async def show_accessories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_STATES[user.id] = "accessories_menu"

    await update.message.reply_text(
        "⚙️ *Комплектующие для под-систем:*\n\n"
        "• Картридж PLONQ 3ml 0.4 Ом - 400 ₽\n"
        "• Картридж Vaporesso XROS 3ML 0.4 Ом - 250 ₽",
        reply_markup=create_keyboard(["Картриджы", "⬅️ Назад в каталог", "🏠 Главное меню"]),
        parse_mode="Markdown"
    )

async def show_cartridges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_STATES[user.id] = "cartridges_menu"

    cartridges = PRODUCTS["accessories"]["cartridges"]
    message = "🔧 *Картриджы:*\n\n" + "\n".join([
        f"• {name} - {info['price']} ₽" for name, info in cartridges.items()
    ])
    
    await update.message.reply_text(
        message,
        reply_markup=create_keyboard(list(cartridges.keys()) + ["⬅️ Назад", "🏠 Главное меню"]),
        parse_mode="Markdown"
    )

# Показать товары бренда
async def show_brand_products(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, brand: str):
    user = update.effective_user
    USER_STATES[user.id] = f"{brand.lower()}_products"

    products = PRODUCTS[category][brand]
    message = f"*{brand} - Товары:*\n\n" + "\n".join([
        f"• {name} - {info['price']} ₽"
        for name, info in products.items()
    ])

    await update.message.reply_text(
        message,
        reply_markup=create_keyboard(list(products.keys()) + ["⬅️ Назад", "🏠 Главное меню"]),
        parse_mode="Markdown"
    )

# Работа с товарами
def add_to_cart(user_id, product_name, price, flavor=None):
    if user_id not in USER_CARTS:
        USER_CARTS[user_id] = []

    item_name = f"{product_name} - {flavor}" if flavor else product_name

    for item in USER_CARTS[user_id]:
        if item['name'] == item_name:
            item['quantity'] += 1
            return

    USER_CARTS[user_id].append({
        'name': item_name,
        'price': price,
        'quantity': 1
    })

async def handle_product_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, product_name: str):
    user = update.effective_user
    user_id = user.id

    # Поиск товара
    product_info = None
    category = None
    
    for cat in ["liquids", "disposables"]:
        for brand, products in PRODUCTS[cat].items():
            if product_name in products:
                product_info = products[product_name]
                category = cat
                break
    
    # Проверка аксессуаров
    if not product_info:
        for name, info in PRODUCTS["accessories"]["cartridges"].items():
            if name == product_name:
                product_info = info
                category = "accessories"
                break

    if not product_info:
        await update.message.reply_text("❌ Товар не найден")
        return

    # Товары с вкусами
    if "flavors" in product_info and product_info["flavors"]:
        USER_CURRENT_SELECTION[user_id] = {
            "product_name": product_name,
            "price": product_info["price"],
            "flavors": product_info["flavors"],
            "image": product_info.get("image")
        }
        USER_STATES[user_id] = f"waiting_flavor_{product_name}"

        flavors_text = "\n".join([f"{i+1}. {flavor}" for i, flavor in enumerate(product_info["flavors"])])
        message = f"🎯 *{product_name}* - *{product_info['price']} ₽*\n\nВыберите вкус:\n\n{flavors_text}"

        try:
            if product_info.get("image"):
                await update.message.reply_photo(
                    photo=product_info["image"],
                    caption=message,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(message, parse_mode="Markdown")
        except:
            await update.message.reply_text(message, parse_mode="Markdown")
    else:
        # Товары без вкусов
        add_to_cart(user_id, product_name, product_info["price"])
        message = f"✅ *{product_name}* - *{product_info['price']} ₽* добавлен в корзину!"
        
        try:
            if product_info.get("image"):
                await update.message.reply_photo(
                    photo=product_info["image"],
                    caption=message,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(message, parse_mode="Markdown")
        except:
            await update.message.reply_text(message, parse_mode="Markdown")

# Работа с корзиной
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    USER_STATES[user_id] = "cart"

    cart = USER_CARTS.get(user_id, [])
    if not cart:
        await update.message.reply_text("🛍️ *Ваша корзина пуста*", parse_mode="Markdown", reply_markup=main_menu_keyboard())
        return

    cart_text = "🛍️ *Ваша корзина*\n\n"
    total = 0
    for i, item in enumerate(cart, 1):
        item_total = item['price'] * item['quantity']
        cart_text += f"{i}. {item['name']} - {item['quantity']} шт. = {item_total} ₽\n"
        total += item_total

    cart_text += f"\n💵 *Итого: {total} ₽*"

    await update.message.reply_text(cart_text, reply_markup=cart_keyboard(), parse_mode="Markdown")

async def send_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = USER_CARTS.get(user.id, [])

    if not cart:
        await update.message.reply_text("❌ Ваша корзина пуста!")
        return

    order_text = f"🛒 *Новый заказ!*\n\n👤 Пользователь: {user.first_name}\n🆔 ID: {user.id}\n\n📝 *Состав заказа:*\n"
    total = 0
    
    for item in cart:
        item_total = item['price'] * item['quantity']
        order_text += f"- {item['name']} - {item['quantity']} шт. = {item_total} ₽\n"
        total += item_total

    order_text += f"\n💵 *Итого: {total} ₽*"

    # Отправка админам
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, order_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending order to admin {admin_id}: {e}")

    await update.message.reply_text(
        "✅ Ваш заказ оформлен! Скоро с вами свяжется оператор.",
        reply_markup=main_menu_keyboard()
    )
    USER_CARTS[user.id] = []

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    state = USER_STATES.get(user_id, "main_menu")

    logger.info(f"User {user_id} state: {state}, text: {text}")

    # Главное меню
    if state == "main_menu":
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
        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню")

    # Меню каталога
    elif state == "catalog_menu":
        if text == "💧 Жидкости":
            await show_liquids(update, context)
        elif text == "🚬 Одноразки":
            await show_disposables(update, context)
        elif text == "⚙️ Комплектующие":
            await show_accessories(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню")

    # Бренды жидкостей
    elif state == "liquids_brands":
        if text in PRODUCTS["liquids"]:
            await show_brand_products(update, context, "liquids", text)
        elif text == "⬅️ Назад в каталог":
            await show_catalog(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, выберите бренд из списка")

    # Бренды одноразок
    elif state == "disposables_brands":
        if text in PRODUCTS["disposables"]:
            await show_brand_products(update, context, "disposables", text)
        elif text == "⬅️ Назад в каталог":
            await show_catalog(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, выберите бренд из списка")

    # Товары бренда (универсальный обработчик)
    elif state.endswith("_products"):
        brand = state.replace("_products", "").upper()
        
        # Проверяем жидкости
        if brand in PRODUCTS["liquids"] and text in PRODUCTS["liquids"][brand]:
            await handle_product_selection(update, context, text)
        # Проверяем одноразки
        elif brand in PRODUCTS["disposables"] and text in PRODUCTS["disposables"][brand]:
            await handle_product_selection(update, context, text)
        elif text == "⬅️ Назад":
            if brand in PRODUCTS["liquids"]:
                await show_liquids(update, context)
            else:
                await show_disposables(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, выберите товар из списка")

    # Выбор вкуса
    elif state.startswith("waiting_flavor_"):
        if text.isdigit():
            flavor_index = int(text) - 1
            selection = USER_CURRENT_SELECTION.get(user_id, {})
            flavors = selection.get("flavors", [])
            
            if 0 <= flavor_index < len(flavors):
                add_to_cart(user_id, selection["product_name"], selection["price"], flavors[flavor_index])
                await update.message.reply_text(f"✅ {selection['product_name']} - {flavors[flavor_index]} добавлен в корзину!")
                USER_STATES[user_id] = "main_menu"
            else:
                await update.message.reply_text("❌ Неверный номер вкуса")
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("❌ Введите номер вкуса")

    # Комплектующие
    elif state == "accessories_menu":
        if text == "Картриджы":
            await show_cartridges(update, context)
        elif text == "⬅️ Назад в каталог":
            await show_catalog(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню")

    # Картриджы
    elif state == "cartridges_menu":
        if text in PRODUCTS["accessories"]["cartridges"]:
            await handle_product_selection(update, context, text)
        elif text == "⬅️ Назад":
            await show_accessories(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, выберите картридж из списка")

    # Корзина
    elif state == "cart":
        if text == "✅ Отправить заказ":
            await send_order(update, context)
        elif text == "✏️ Редактировать заказ":
            await update.message.reply_text("✏️ Для удаления товара отправьте его номер:")
            USER_STATES[user_id] = "editing_cart"
        elif text == "⬅️ Назад в каталог":
            await show_catalog(update, context)
        elif text == "🏠 Главное меню":
            USER_STATES[user_id] = "main_menu"
            await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки меню")

    # Редактирование корзины
    elif state == "editing_cart":
        if text.isdigit():
            item_num = int(text)
            cart = USER_CARTS.get(user_id, [])
            if 1 <= item_num <= len(cart):
                removed = cart.pop(item_num - 1)
                await update.message.reply_text(f"❌ Товар '{removed['name']}' удален из корзины")
                await show_cart(update, context)
            else:
                await update.message.reply_text("❌ Неверный номер товара")
        else:
            await update.message.reply_text("❌ Введите номер товара для удаления")

    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки меню")

# Обработчик инлайн кнопок (пустой, но нужен для работы)
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Функция в разработке")

def main():
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        logger.info("Бот CloudFM запущен и работает")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
