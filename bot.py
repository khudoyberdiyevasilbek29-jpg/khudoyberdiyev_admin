"""
Digital Agency Order Collection Bot
A production-ready Telegram bot using aiogram 3 for collecting client orders
with FSM-based state management and flexible pricing logic.
"""

import logging
import os
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class Language(str, Enum):
    """Available languages"""
    UZ = "uz"
    EN = "en"
    RU = "ru"


class ServiceType(str, Enum):
    """Available service types"""
    WEBSITE = "website"
    BOT = "telegram_bot"
    COMBO = "combo"


class WebPackage(str, Enum):
    """Web service packages"""
    START = "start"
    STANDARD = "standard"
    PREMIUM = "premium"


class ContactMethod(str, Enum):
    """Contact methods"""
    USERNAME = "username"
    PHONE = "phone"


# ============================================================================
# TRANSLATIONS
# ============================================================================

TRANSLATIONS = {
    Language.UZ: {
        "welcome": "👋 Raqamlash Agentligi Buyurtma Shakli!\n\nBiz siz bilan buyurtma yaratishda yordam beramiz. Keling, avvalo ismingizni so'raylik.",
        "first_name": "✅ Qabul qilindi! Endi familyangizni kiriting?",
        "last_name": "✅ Rahmat! Siz qanday biznesga shug'ullanasiz?",
        "business_type": "🏢 Biznes turi nima?",
        "contact_method": "📞 Qanday usul orqali bog'lanaylik?",
        "username_label": "👤 Telegram username'i",
        "phone_label": "📱 Telefon raqami",
        "enter_username": "👤 Telegram username'ingizni kiriting (@ belgisisiz):",
        "enter_phone": "📱 Telefon raqamingizni kiriting:",
        "select_service": "🛠️ Qaysi xizmatga qiziqasiz?",
        "website_only": "🌐 Faqat Vebsayt",
        "bot_only": "🤖 Faqat Telegram Bot",
        "combo": "✨ Vebsayt + Bot (Combo)",
        "select_package": "💻 Vebsayt paketini tanlang:",
        "start_package": "⭐ Start - 1.500M",
        "standard_package": "💫 Standard - 2.300M",
        "premium_package": "🌟 Premium - 3.000M",
        "confirm": "✅ Buyurtmani Tasdiqlash",
        "cancel": "❌ Bekor Qilish",
        "summary": "📋 Buyurtma Xulosasi",
        "full_name": "👤 F.I.O:",
        "business": "🏢 Biznes Turi:",
        "contact": "📞 Bog'lanish:",
        "contact_method_label": "📱 Bog'lanish Usuli:",
        "service": "🛠️ Xizmat:",
        "original_price": "💰 Asl Narxi:",
        "discount": "🎉 Chegirma:",
        "final_price": "✅ Yakuniy Narxi:",
        "confirm_order": "👇 Buyurtmani Tasdiqlash:",
        "order_confirmed": "🎉 Buyurtma Tasdiqlandi!\n\nBuyurtmangiz qabul qilindi va meneger'ga yuborildi. Tez orada siz bilan bog'lanamiz.\n\nBuyurtma ID: ",
        "order_cancelled": "❌ Buyurtma Bekor Qilindi. /start buyrugi bilan yangi buyurtma yaratishingiz mumkin.",
        "error_name": "❌ Iltimos, to'g'ri isim kiriting (kamida 2 ta harf).",
        "error_contact": "❌ Iltimos, to'g'ri bog'lanish ma'lumotini kiriting.",
        "select_language": "🌐 Tilni tanlang / Select language:",
        "uzbek": "🇺🇿 Uzbek",
        "english": "🇬🇧 English",
        "russian": "🇷🇺 Русский",
        "timeline": "📅 Loyiha Jarayoni:",
        "delivery": "📦 Topshirish vaqti:",
        "days": "kun",
    },
    Language.EN: {
        "welcome": "👋 Welcome to Digital Agency Order Form!\n\nI'll help you create an order for our services. Let's start with your first name.",
        "first_name": "✅ Got it! Now, what's your last name?",
        "last_name": "✅ Great! What type of business do you have?",
        "business_type": "🏢 What type of business?",
        "contact_method": "📞 How would you like us to contact you?",
        "username_label": "👤 Telegram Username",
        "phone_label": "📱 Phone Number",
        "enter_username": "👤 Please enter your Telegram username (without @):",
        "enter_phone": "📱 Please enter your phone number:",
        "select_service": "🛠️ What service are you interested in?",
        "website_only": "🌐 Website Only",
        "bot_only": "🤖 Telegram Bot Only",
        "combo": "✨ Web + Bot (Combo)",
        "select_package": "💻 Select your website package:",
        "start_package": "⭐ Start - 1.500M",
        "standard_package": "💫 Standard - 2.300M",
        "premium_package": "🌟 Premium - 3.000M",
        "confirm": "✅ Confirm Order",
        "cancel": "❌ Cancel",
        "summary": "📋 Order Summary",
        "full_name": "👤 Full Name:",
        "business": "🏢 Business Type:",
        "contact": "📞 Contact:",
        "contact_method_label": "📱 Contact Method:",
        "service": "🛠️ Service:",
        "original_price": "💰 Original Price:",
        "discount": "🎉 Discount:",
        "final_price": "✅ Final Price:",
        "confirm_order": "👇 Please confirm your order:",
        "order_confirmed": "🎉 Thank you for your order!\n\nYour order has been received and sent to our manager. We'll contact you shortly.\n\nReference ID: ",
        "order_cancelled": "Order cancelled. Type /start to create a new order.",
        "error_name": "❌ Please enter a valid name (at least 2 characters).",
        "error_contact": "❌ Please enter valid contact information.",
        "select_language": "🌐 Select language / Tilni tanlang / Выберите язык:",
        "uzbek": "🇺🇿 Uzbek",
        "english": "🇬🇧 English",
        "russian": "🇷🇺 Русский",
        "timeline": "📅 Project Timeline:",
        "delivery": "📦 Delivery time:",
        "days": "days",
    },
    Language.RU: {
        "welcome": "👋 Добро пожаловать в форму заказа Digital Agency!\n\nЯ помогу вам создать заказ наших услуг. Начнем с вашего имени.",
        "first_name": "✅ Спасибо! Теперь введите вашу фамилию?",
        "last_name": "✅ Отлично! Каким бизнесом вы занимаетесь?",
        "business_type": "🏢 Какой вид бизнеса?",
        "contact_method": "📞 Как мы можем с вами связаться?",
        "username_label": "👤 Имя пользователя Telegram",
        "phone_label": "📱 Номер телефона",
        "enter_username": "👤 Пожалуйста введите ваше имя пользователя Telegram (без @):",
        "enter_phone": "📱 Пожалуйста введите ваш номер телефона:",
        "select_service": "🛠️ Какая услуга вас интересует?",
        "website_only": "🌐 Только Веб-сайт",
        "bot_only": "🤖 Только Telegram Bot",
        "combo": "✨ Веб-сайт + Bot (Комбо)",
        "select_package": "💻 Выберите пакет вебсайта:",
        "start_package": "⭐ Start - 1.500M",
        "standard_package": "💫 Standard - 2.300M",
        "premium_package": "🌟 Premium - 3.000M",
        "confirm": "✅ Подтвердить заказ",
        "cancel": "❌ Отмена",
        "summary": "📋 Сводка заказа",
        "full_name": "👤 Полное имя:",
        "business": "🏢 Тип бизнеса:",
        "contact": "📞 Контакт:",
        "contact_method_label": "📱 Способ связи:",
        "service": "🛠️ Услуга:",
        "original_price": "💰 Оригинальная цена:",
        "discount": "🎉 Скидка:",
        "final_price": "✅ Итоговая цена:",
        "confirm_order": "👇 Пожалуйста подтвердите ваш заказ:",
        "order_confirmed": "🎉 Спасибо за ваш заказ!\n\nВаш заказ получен и отправлен менеджеру. Мы свяжемся с вами в ближайшее время.\n\nID заказа: ",
        "order_cancelled": "Заказ отменен. Введите /start чтобы создать новый заказ.",
        "error_name": "❌ Пожалуйста введите правильное имя (минимум 2 символа).",
        "error_contact": "❌ Пожалуйста введите правильный контактный номер.",
        "select_language": "🌐 Select language / Tilni tanlang / Выберите язык:",
        "uzbek": "🇺🇿 Uzbek",
        "english": "🇬🇧 English",
        "russian": "🇷🇺 Русский",
        "timeline": "📅 Временная шкала проекта:",
        "delivery": "📦 Время доставки:",
        "days": "дней",
    }
}


def get_text(lang: Language, key: str) -> str:
    """Get translated text"""
    return TRANSLATIONS.get(lang, TRANSLATIONS[Language.EN]).get(key, key)


# ============================================================================
# PRICING CONFIGURATION
# ============================================================================

# Pricing configuration (in currency units)
PRICING = {
    ServiceType.WEBSITE: {
        WebPackage.START: 1_500_000,
        WebPackage.STANDARD: 2_300_000,
        WebPackage.PREMIUM: 3_000_000,
    },
    ServiceType.BOT: 3_500_000,
    ServiceType.COMBO: {
        WebPackage.START: 1_500_000 + 3_500_000,
        WebPackage.STANDARD: 2_300_000 + 3_500_000,
        WebPackage.PREMIUM: 3_000_000 + 3_500_000,
    },
}

# Discount configuration
DISCOUNT_RATES = {
    (ServiceType.COMBO, WebPackage.PREMIUM): 0.20,
    (ServiceType.COMBO, WebPackage.START): 0.10,
    (ServiceType.COMBO, WebPackage.STANDARD): 0.10,
}

# Queue/Order counter (starts from 1)
ORDER_QUEUE_COUNTER = 1

# ============================================================================
# PROJECT TIMELINE CONFIGURATION
# ============================================================================

PROJECT_TIMELINE = {
    WebPackage.START: {
        "delivery_days": 21,
        "steps": [
            ("Buyurtma qabul qilish / Order intake", 2),
            ("Dizayn va mockup / Design & mockup", 5),
            ("Tasdiqlash / Approval", 3),
            ("Development / Development", 8),
            ("Testing / Testing", 3),
        ]
    },
    WebPackage.STANDARD: {
        "delivery_days": 28,
        "steps": [
            ("Buyurtma qabul qilish / Order intake", 2),
            ("Dizayn va mockup / Design & mockup", 5),
            ("Tasdiqlash / Approval", 3),
            ("Development / Development", 12),
            ("Testing / Testing", 4),
            ("Topshirish / Delivery", 2),
        ]
    },
    WebPackage.PREMIUM: {
        "delivery_days": 35,
        "steps": [
            ("Buyurtma qabul qilish / Order intake", 2),
            ("Dizayn va mockup / Design & mockup", 7),
            ("Tasdiqlash / Approval", 3),
            ("Development / Development", 15),
            ("Testing / Testing", 5),
            ("Topshirish / Delivery", 3),
        ]
    },
}


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class OrderData:
    """Data structure for order information"""
    language: str
    first_name: str
    last_name: str
    business_type: str
    contact: str
    contact_method: str
    service_type: str
    web_package: Optional[str] = None
    original_price: int = 0
    discount_percent: int = 0
    final_price: int = 0
    queue_number: int = 0  # Navbat raqami

    def to_summary(self) -> str:
        """Generate a formatted order summary"""
        summary = (
            f"📋 <b>Order Summary</b>\n\n"
            f"👤 <b>Full Name:</b> {self.first_name} {self.last_name}\n"
            f"🏢 <b>Business Type:</b> {self.business_type}\n"
            f"📞 <b>Contact:</b> {self.contact}\n"
            f"📱 <b>Contact Method:</b> {self.contact_method.capitalize()}\n"
            f"🛠️ <b>Service:</b> {self._format_service()}\n"
            f"💰 <b>Original Price:</b> {self.original_price:,}\n"
        )
        
        if self.discount_percent > 0:
            summary += f"🎉 <b>Discount:</b> {self.discount_percent}%\n"
        
        summary += f"✅ <b>Final Price:</b> <u>{self.final_price:,}</u>"
        return summary

    def _format_service(self) -> str:
        """Format service description for display"""
        if self.service_type == ServiceType.WEBSITE:
            return f"Website ({self.web_package.capitalize()} package)"
        elif self.service_type == ServiceType.BOT:
            return "Telegram Bot"
        else:  # COMBO
            return f"Website ({self.web_package.capitalize()}) + Telegram Bot"


# ============================================================================
# FSM STATE DEFINITIONS
# ============================================================================

class OrderFormStates(StatesGroup):
    """State group for order collection form"""
    
    waiting_for_language = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_business_type = State()
    waiting_for_contact_method = State()
    waiting_for_contact = State()
    waiting_for_service_selection = State()
    waiting_for_web_package = State()
    waiting_for_confirmation = State()


# ============================================================================
# KEYBOARD BUILDERS
# ============================================================================

def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for language selection"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🇺🇿 Uzbek",
            callback_data=f"lang_{Language.UZ.value}"
        ),
        InlineKeyboardButton(
            text="🇬🇧 English",
            callback_data=f"lang_{Language.EN.value}"
        ),
    )
    builder.add(
        InlineKeyboardButton(
            text="🇷🇺 Русский",
            callback_data=f"lang_{Language.RU.value}"
        )
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_service_selection_keyboard(lang: Language) -> InlineKeyboardMarkup:
    """Build keyboard for service selection"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=get_text(lang, "website_only"),
            callback_data=f"service_{ServiceType.WEBSITE.value}"
        ),
        InlineKeyboardButton(
            text=get_text(lang, "bot_only"),
            callback_data=f"service_{ServiceType.BOT.value}"
        ),
    )
    builder.add(
        InlineKeyboardButton(
            text=get_text(lang, "combo"),
            callback_data=f"service_{ServiceType.COMBO.value}"
        )
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def get_web_package_keyboard(lang: Language) -> InlineKeyboardMarkup:
    """Build keyboard for web package selection"""
    builder = InlineKeyboardBuilder()
    
    packages = [
        (WebPackage.START, "start_package"),
        (WebPackage.STANDARD, "standard_package"),
        (WebPackage.PREMIUM, "premium_package"),
    ]
    
    for package, label_key in packages:
        builder.add(
            InlineKeyboardButton(
                text=get_text(lang, label_key),
                callback_data=f"package_{package.value}"
            )
        )
    
    return builder.as_markup()


def get_contact_method_keyboard(lang: Language) -> InlineKeyboardMarkup:
    """Build keyboard for contact method selection"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=get_text(lang, "username_label"),
            callback_data=f"contact_{ContactMethod.USERNAME.value}"
        ),
        InlineKeyboardButton(
            text=get_text(lang, "phone_label"),
            callback_data=f"contact_{ContactMethod.PHONE.value}"
        ),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_confirmation_keyboard(lang: Language) -> InlineKeyboardMarkup:
    """Build keyboard for order confirmation"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=get_text(lang, "confirm"), callback_data="confirm_yes"),
        InlineKeyboardButton(text=get_text(lang, "cancel"), callback_data="confirm_no"),
    )
    builder.adjust(1)
    return builder.as_markup()


# ============================================================================
# PRICING & CALCULATION LOGIC
# ============================================================================

def calculate_order_price(order: OrderData) -> None:
    """Calculate original, discount, and final price for the order"""
    
    # Convert string to enum if needed
    service_type = ServiceType(order.service_type) if isinstance(order.service_type, str) else order.service_type
    
    if service_type == ServiceType.WEBSITE:
        web_pkg = WebPackage(order.web_package) if isinstance(order.web_package, str) else order.web_package
        order.original_price = PRICING[ServiceType.WEBSITE][web_pkg]
        order.discount_percent = 0
    
    elif service_type == ServiceType.BOT:
        order.original_price = PRICING[ServiceType.BOT]
        order.discount_percent = 0
    
    elif service_type == ServiceType.COMBO:
        web_pkg = WebPackage(order.web_package) if isinstance(order.web_package, str) else order.web_package
        order.original_price = PRICING[ServiceType.COMBO][web_pkg]
        
        # Apply discount based on package
        discount_key = (ServiceType.COMBO, web_pkg)
        order.discount_percent = int(DISCOUNT_RATES.get(discount_key, 0) * 100)
    
    # Calculate final price
    discount_amount = order.original_price * (order.discount_percent / 100)
    order.final_price = int(order.original_price - discount_amount)


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

async def cmd_start(message: Message, state: FSMContext) -> None:
    """Handle /start command"""
    await state.clear()
    await message.answer(
        "🌐 Tilni tanlang / Select language:",
        reply_markup=get_language_selection_keyboard(),
    )
    await state.set_state(OrderFormStates.waiting_for_language)


async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Handle /cancel command"""
    await state.clear()
    await message.answer(
        "❌ Order form cancelled. Type /start to begin again.",
        reply_markup=types.ReplyKeyboardRemove(),
    )


async def process_language(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Process language selection"""
    try:
        lang_str = callback.data.split("_")[1]
        # lang_str will be like "uz", "en", "ru"
        lang_enum = Language(lang_str)
        
        await state.update_data(language=lang_enum)
        await callback.answer()
        
        # DON'T use ReplyKeyboardRemove with edit_text! Just pass None
        await callback.message.edit_text(
            get_text(lang_enum, "welcome")
        )
        await state.set_state(OrderFormStates.waiting_for_first_name)
        logger.info(f"Language selected: {lang_enum}")
    
    except Exception as e:
        logger.error(f"Language selection error: {e}")
        await callback.answer("❌ Xatolik! /start qayta bosing.", show_alert=True)


async def process_first_name(message: Message, state: FSMContext) -> None:
    """Process first name input"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    if not message.text or len(message.text) < 2:
        await message.answer(get_text(lang, "error_name"))
        return
    
    await state.update_data(first_name=message.text)
    await message.answer(get_text(lang, "first_name"))
    await state.set_state(OrderFormStates.waiting_for_last_name)


async def process_last_name(message: Message, state: FSMContext) -> None:
    """Process last name input"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    if not message.text or len(message.text) < 2:
        await message.answer(get_text(lang, "error_name"))
        return
    
    await state.update_data(last_name=message.text)
    await message.answer(get_text(lang, "last_name"))
    await state.set_state(OrderFormStates.waiting_for_business_type)


async def process_business_type(message: Message, state: FSMContext) -> None:
    """Process business type input"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    if not message.text or len(message.text) < 3:
        await message.answer(get_text(lang, "error_name"))
        return
    
    await state.update_data(business_type=message.text)
    await message.answer(
        get_text(lang, "contact_method"),
        reply_markup=get_contact_method_keyboard(lang),
    )
    await state.set_state(OrderFormStates.waiting_for_contact_method)


async def process_contact_method(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Process contact method selection"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    method = callback.data.split("_")[1]
    await state.update_data(contact_method=method)
    
    prompt_key = "enter_username" if method == ContactMethod.USERNAME.value else "enter_phone"
    
    await callback.message.edit_text(get_text(lang, prompt_key))
    await callback.answer()
    await state.set_state(OrderFormStates.waiting_for_contact)


async def process_contact(message: Message, state: FSMContext) -> None:
    """Process contact information input"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    contact_method = data.get("contact_method")
    
    if contact_method == ContactMethod.USERNAME.value:
        if not message.text or len(message.text) < 3:
            await message.answer(get_text(lang, "error_contact"))
            return
        contact = f"@{message.text.lstrip('@')}"
    else:  # PHONE
        if not message.text or len(message.text.replace("+", "").replace(" ", "")) < 10:
            await message.answer(get_text(lang, "error_contact"))
            return
        contact = message.text
    
    await state.update_data(contact=contact)
    await message.answer(
        get_text(lang, "select_service"),
        reply_markup=get_service_selection_keyboard(lang),
    )
    await state.set_state(OrderFormStates.waiting_for_service_selection)


async def process_service_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Process service type selection"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    service = callback.data.split("_")[1]
    await state.update_data(service_type=service)
    
    await callback.answer()
    
    if service == ServiceType.WEBSITE.value:
        await callback.message.edit_text(
            get_text(lang, "select_package"),
            reply_markup=get_web_package_keyboard(lang),
        )
        await state.set_state(OrderFormStates.waiting_for_web_package)
    
    elif service == ServiceType.BOT.value:
        await state.update_data(web_package=None)
        await show_order_summary(callback.message, state)
    
    else:  # COMBO
        await callback.message.edit_text(
            get_text(lang, "select_package"),
            reply_markup=get_web_package_keyboard(lang),
        )
        await state.set_state(OrderFormStates.waiting_for_web_package)


async def process_web_package(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Process web package selection"""
    package = callback.data.split("_")[1]
    await state.update_data(web_package=package)
    await callback.answer()
    
    await show_order_summary(callback.message, state)


async def show_order_summary(message: Message, state: FSMContext) -> None:
    """Display order summary and ask for confirmation"""
    global ORDER_QUEUE_COUNTER
    
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    # Create order object
    order = OrderData(
        language=lang,
        first_name=data["first_name"],
        last_name=data["last_name"],
        business_type=data["business_type"],
        contact=data["contact"],
        contact_method=data["contact_method"],
        service_type=data["service_type"],
        web_package=data.get("web_package"),
        queue_number=ORDER_QUEUE_COUNTER,  # Assign queue number
    )
    
    # Increment for next order
    ORDER_QUEUE_COUNTER += 1
    
    # Calculate pricing
    calculate_order_price(order)
    
    # Store order in state for later use
    await state.update_data(order_data=asdict(order))
    
    # Generate summary
    summary = _generate_summary(order, lang)
    
    # Display summary
    await message.edit_text(
        summary + "\n\n" + get_text(lang, "confirm_order"),
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard(lang),
    )
    
    await state.set_state(OrderFormStates.waiting_for_confirmation)


def _generate_summary(order: OrderData, lang: Language) -> str:
    """Generate order summary in the specified language"""
    service_desc = _format_service(order)
    
    summary = (
        f"📋 <b>{get_text(lang, 'summary')}</b>\n\n"
        f"{get_text(lang, 'full_name')} {order.first_name} {order.last_name}\n"
        f"{get_text(lang, 'business')} {order.business_type}\n"
        f"{get_text(lang, 'contact')} {order.contact}\n"
        f"{get_text(lang, 'contact_method_label')} {order.contact_method.capitalize()}\n"
        f"{get_text(lang, 'service')} {service_desc}\n"
        f"{get_text(lang, 'original_price')} {order.original_price:,}\n"
    )
    
    if order.discount_percent > 0:
        summary += f"{get_text(lang, 'discount')} {order.discount_percent}%\n"
    
    summary += f"{get_text(lang, 'final_price')} <u>{order.final_price:,}</u>\n"
    
    # Add timeline if web package is selected
    if order.web_package:
        try:
            web_pkg = WebPackage(order.web_package) if isinstance(order.web_package, str) else order.web_package
            timeline = PROJECT_TIMELINE.get(web_pkg)
            if timeline:
                summary += f"\n\n{get_text(lang, 'timeline')}\n"
                summary += f"{get_text(lang, 'delivery')} <b>{timeline['delivery_days']} {get_text(lang, 'days')}</b>\n\n"
                for step_name, step_days in timeline['steps']:
                    summary += f"• {step_name}: {step_days} {get_text(lang, 'days')}\n"
        except Exception as e:
            logger.warning(f"Could not add timeline: {e}")
    
    return summary


def _format_service(order: OrderData) -> str:
    """Format service description for display"""
    if order.service_type == ServiceType.WEBSITE.value:
        return f"Website ({order.web_package.capitalize()} package)"
    elif order.service_type == ServiceType.BOT.value:
        return "Telegram Bot"
    else:  # COMBO
        return f"Website ({order.web_package.capitalize()}) + Telegram Bot"


async def process_confirmation(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Process order confirmation"""
    data = await state.get_data()
    lang = data.get("language", Language.EN)
    
    if callback.data == "confirm_yes":
        await callback.answer("✅ Order confirmed!", show_alert=False)
        
        order_data = data.get("order_data")
        queue_num = order_data.get("queue_number", 1)
        
        # Build confirmation message with queue info
        confirmation_msg = get_text(lang, "order_confirmed") + generate_order_id()
        
        if lang == Language.UZ:
            queue_text = (
                f"\n\n📋 <b>Navbat Raqami:</b> #{queue_num}\n"
                f"⏳ <b>Kutish Vaqti:</b> 3 hafta\n"
                f"📞 <b>Aloqa:</b> 1-2 kun ichida siz bilan bog'lanamiz"
            )
        elif lang == Language.RU:
            queue_text = (
                f"\n\n📋 <b>Номер очереди:</b> #{queue_num}\n"
                f"⏳ <b>Время ожидания:</b> 3 недели\n"
                f"📞 <b>Контакт:</b> Мы свяжемся с вами в течение 1-2 дней"
            )
        else:  # English
            queue_text = (
                f"\n\n📋 <b>Queue Number:</b> #{queue_num}\n"
                f"⏳ <b>Waiting Time:</b> 3 weeks\n"
                f"📞 <b>Contact:</b> We'll reach out in 1-2 days"
            )
        
        # Send confirmation to user
        await callback.message.edit_text(
            confirmation_msg + queue_text,
            parse_mode="HTML",
        )
        
        # Send to admin with queue info
        await send_order_to_admin(callback.bot, order_data)
        
        await state.clear()
    
    else:  # confirm_no
        await callback.answer("❌ Order cancelled", show_alert=False)
        await callback.message.edit_text(
            get_text(lang, "order_cancelled")
        )
        await state.clear()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_order_id() -> str:
    """Generate a simple order ID"""
    import time
    return f"ORD-{int(time.time())}"


async def send_order_to_admin(bot: Bot, order_data: Dict) -> None:
    """Send order details to admin"""
    try:
        queue_num = order_data.get("queue_number", 1)
        
        message_text = (
            f"📋 <b>New Order Received</b>\n"
            f"📍 <b>Queue #:</b> {queue_num}\n\n"
            f"👤 <b>Name:</b> {order_data['first_name']} {order_data['last_name']}\n"
            f"🏢 <b>Business:</b> {order_data['business_type']}\n"
            f"📞 <b>Contact:</b> {order_data['contact']}\n"
            f"📱 <b>Method:</b> {order_data['contact_method'].capitalize()}\n"
            f"🛠️ <b>Service:</b> {_format_admin_service(order_data)}\n"
            f"💰 <b>Original Price:</b> {order_data['original_price']:,}\n"
            f"🎉 <b>Discount:</b> {order_data['discount_percent']}%\n"
            f"✅ <b>Final Price:</b> {order_data['final_price']:,}\n"
        )
        
        # Add timeline if web package exists
        if order_data.get('web_package'):
            try:
                web_pkg = WebPackage(order_data['web_package']) if isinstance(order_data['web_package'], str) else order_data['web_package']
                timeline = PROJECT_TIMELINE.get(web_pkg)
                if timeline:
                    message_text += f"\n📅 <b>Project Timeline:</b> {timeline['delivery_days']} days\n"
                    for step_name, step_days in timeline['steps']:
                        message_text += f"• {step_name}: {step_days} days\n"
            except Exception as e:
                logger.warning(f"Could not add timeline to admin message: {e}")
        
        message_text += f"\n⏳ <b>Action:</b> Contact client in 1-2 days"
        
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=message_text,
            parse_mode="HTML",
        )
        logger.info(f"Order #{queue_num} sent to admin: {order_data}")
    
    except Exception as e:
        logger.error(f"Failed to send order to admin: {e}")


def _format_admin_service(order_data: Dict) -> str:
    """Format service for admin notification"""
    service = order_data["service_type"]
    
    if service == ServiceType.WEBSITE.value:
        return f"Website ({order_data['web_package'].capitalize()})"
    elif service == ServiceType.BOT.value:
        return "Telegram Bot"
    else:
        return f"Website ({order_data['web_package'].capitalize()}) + Bot"


# ============================================================================
# MAIN APPLICATION
# ============================================================================

async def main() -> None:
    """Main function to start the bot"""
    
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Register handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_cancel, Command("cancel"))
    
    # FSM handlers
    dp.callback_query.register(
        process_language,
        OrderFormStates.waiting_for_language,
        F.data.startswith("lang_"),
    )
    dp.message.register(
        process_first_name,
        OrderFormStates.waiting_for_first_name,
    )
    dp.message.register(
        process_last_name,
        OrderFormStates.waiting_for_last_name,
    )
    dp.message.register(
        process_business_type,
        OrderFormStates.waiting_for_business_type,
    )
    dp.callback_query.register(
        process_contact_method,
        OrderFormStates.waiting_for_contact_method,
        F.data.startswith("contact_"),
    )
    dp.message.register(
        process_contact,
        OrderFormStates.waiting_for_contact,
    )
    dp.callback_query.register(
        process_service_selection,
        OrderFormStates.waiting_for_service_selection,
        F.data.startswith("service_"),
    )
    dp.callback_query.register(
        process_web_package,
        OrderFormStates.waiting_for_web_package,
        F.data.startswith("package_"),
    )
    dp.callback_query.register(
        process_confirmation,
        OrderFormStates.waiting_for_confirmation,
        F.data.startswith("confirm_"),
    )
    
    # Start polling
    logger.info("🤖 Bot started successfully")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())