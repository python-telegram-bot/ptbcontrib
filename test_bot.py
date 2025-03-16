# 1. Импорты стандартных библиотек
import os
import sys
import json
import logging
import asyncio
import re
from datetime import datetime

# 2. Импорты внешних библиотек
import aiohttp
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# 3. Загрузка переменных окружения
env_files = [
    "C:/telegram_bot/TELEGRAM_BOT_TOKEN.env",
    "C:/telegram_bot/MULTIBANK.env",
    "C:/telegram_bot/FAKTURA_TOKEN.env",
    "C:/telegram_bot/E-DOC.env",
    "C:/telegram_bot/SOLIQ_API_KEY.env"
]

for env_file in env_files:
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        print(f"⚠️ Файл {env_file} не найден!")

# 4. Глобальные переменные
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MULTIBANK_BASE_URL = os.getenv("MULTIBANK_BASE_URL")
API_KEY = os.getenv("API_KEY")

# 5. Проверка загрузки переменных
if not TELEGRAM_BOT_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не загружен!")
if not MULTIBANK_BASE_URL:
    print("⚠️ Внимание: MULTIBANK_BASE_URL не загружен.")
if not API_KEY:
    print("⚠️ Внимание: API_KEY не загружен.")

# 6. Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Загружаем каждое .env
for env_file in env_files:
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        print(f"⚠️ Файл {env_file} не найден!")

# Проверяем, загрузился ли главный токен
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не загружен! Проверь .env файлы.")
else:
    print(f"✅ Токен Telegram загружен: {TOKEN[:5]}... (скрыто)")

print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))
print("MULTIBANK_BASE_URL:", os.getenv("MULTIBANK_BASE_URL"))
print("API_KEY:", os.getenv("API_KEY"))

async def get_multibank_data(company_tin: str, data_type: str, refresh: bool = True):
    """
    Запрашивает данные о компании из Multibank API.
    
    :param company_tin: ИНН компании (строка)
    :param data_type: Тип данных ('court', 'license', 'marks')
    :param refresh: Обновлять данные (True/False)
    :return: JSON-ответ API или None в случае ошибки
    """
    MULTIBANK_BASE_URL = os.getenv("MULTIBANK_BASE_URL")
    url = f"{MULTIBANK_BASE_URL}/{data_type}/{company_tin}?refresh={str(refresh).lower()}"
        
    auth = aiohttp.BasicAuth(MULTIBANK_USERNAME, MULTIBANK_PASSWORD)

    try:
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Ошибка {response.status}: {await response.text()}"}
    except Exception as e:
        return {"error": f"Ошибка запроса: {e}"}

async def check_multibank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /check_multibank."""
    if not context.args:
        await update.message.reply_text("❌ Пожалуйста, укажите ИНН после команды. Пример:\n`/check_multibank 123456789`", parse_mode="Markdown")
        return

    company_tin = context.args[0].strip()
    if not company_tin.isdigit() or len(company_tin) != 9:
        await update.message.reply_text("❌ Неверный формат ИНН. Должно быть 9 цифр.")
        return

    await update.message.reply_text("⏳ Запрашиваю данные...")

    # Запрашиваем данные из Multibank API
    court_data = await get_multibank_data(company_tin, "court")
    license_data = await get_multibank_data(company_tin, "license")
    marks_data = await get_multibank_data(company_tin, "marks")

    # Формируем ответ
    response = f"📌 *Данные по ИНН {company_tin}:*\n\n"

    # Судебные дела
    if "error" not in court_data and court_data.get("court"):
        response += f"⚖️Судебные истории: {len(court_data['court'])} найдено\n"
        for case in court_data["court"][:30]:
            response += f"🔹 Дело №{case.get('court_case_number', '—')} ({case.get('court_hearing_date', '—')})\n"
        response += "\n"
    else:
        response += "⚖️Судебные истории: Нет данных\n"

    # Лицензии
    if "error" not in license_data and license_data.get("license"):
        response += f"🗞Лицензии: {len(license_data['license'])} найдено\n"
        for lic in license_data["license"][:30]:
            response += f"🔹 {lic.get('license_name', '—')} (№{lic.get('license_number', '—')})\n"
        response += "\n"
    else:
        response += "📜 Лицензии: Нет данных\n\n"

    # Торговые знаки
    if "error" not in marks_data and marks_data.get("marks"):
        response += f"™ Торговые знаки: {len(marks_data['marks'])} найдено\n"
        for mark in marks_data["marks"][:30]:
            response += f"🔹 {mark.get('ima_marks_name', '—')} (№{mark.get('ima_marks_number', '—')})\n"
        response += "\n"
    else:
        response += "™ Торговые знаки: Нет данных\n\n"

    await update.message.reply_text(response, parse_mode="Markdown")

# Автоматически определяем путь к JSON-файлам
BASE_DIR = os.getcwd()  
file_path = os.path.join(BASE_DIR, "opf.json")  
translations_path = os.path.join(BASE_DIR, "translations.json")

# Загружаем OPF JSON безопасно
try:
    with open(file_path, "r", encoding="utf-8") as f:
        OPF_DATA = json.load(f)
except Exception as e:
    OPF_DATA = {}
    print(f"⚠ Ошибка загрузки opf.json: {e}")

# Функция для получения OPF
def get_opf_name(opf_code):
    return OPF_DATA.get(str(opf_code), "Неизвестно")

# Загружаем переводы
try:
    with open(translations_path, "r", encoding="utf-8") as f:
        TRANSLATIONS = json.load(f)
except Exception as e:
    TRANSLATIONS = {}
    print(f"⚠ Ошибка загрузки translations.json: {e}")

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = "https://data.egov.uz/apiPartner/Partner/WebService"

logger = logging.getLogger(__name__)
async def fetch_dominant_company_info(inn: str):
    """
    Запрашивает информацию о доминирующей компании по ИНН через API data.egov.uz.
    """
    url = f"https://data.egov.uz/api/market-dominance/{inn}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
                # Логируем полный ответ API
                logger.info(f"📢 Полный ответ API для доминирующей компании ({inn}): {json.dumps(data, ensure_ascii=False, indent=2)}")

                return data  # Возвращаем данные API
    except Exception as e:
        logger.error(f"❌ Ошибка при запросе к API data.egov.uz: {e}")
        return None

async def check_dominant_company(inn: str) -> bool:
    """
    Проверяет, является ли компания доминирующей через API data.egov.uz.
    """
    params = {
        "token": API_TOKEN,
        "name": "2-009-0017",
        "offset": 0,
        "limit": 100,  # Получаем сразу 100 записей
        "lang": "uz"
    }
    logger = logging.getLogger(__name__)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"❌ Ошибка API ({response.status}): {await response.text()}")
                    return False
                
                data = await response.json()
                
                # Логируем полный ответ API
                logger = logging.getLogger(__name__)
                logger.info(f"📢 Ответ API для доминирующих компаний: {json.dumps(data, ensure_ascii=False, indent=2)}")
                
                # Проверяем, есть ли результат в ответе API
                if not data or "result" not in data or "data" not in data["result"]:
                    logger.warning("⚠ API вернуло пустой или некорректный ответ")
                    return False

                # Ищем компанию с заданным ИНН (STIR)
                for company in data["result"]["data"]:
                    if str(company.get("STIR")) == str(inn):  # Сравниваем ИНН как строки
                        logger.info(f"✅ Компания {inn} найдена в списке доминирующих!")
                        return True
                
                logger.info(f"❌ Компания {inn} не найдена в списке доминирующих.")
                return False

    except Exception as e:
        logger.error(f"❌ Ошибка при запросе к API data.egov.uz: {e}")
        return False

def translate_activity(activity_uz):
    """Переводит вид деятельности с узбекского на русский."""
    return TRANSLATIONS.get(activity_uz, activity_uz)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="utf-8"  # Фикс кодировки для эмодзи и кириллицы
)



# Константы
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if API_TOKEN is None:
    raise ValueError("Не установлен TELEGRAM_BOT_TOKEN в переменных окружения.")
API_KEY = os.getenv("API_KEY")  # Загружаем API-ключ из переменной среды
OWNER_ID = 6116094248  # ID владельца для уведомлений

semaphore = asyncio.Semaphore(5)  # Максимум 5 одновременных запросов

# Функции для работы с API

async def fetch_company_info(inn):
    """Получает информацию о компании по ИНН."""
    url = f"https://my3.soliq.uz/api/remote-access-api/company/info/{inn}?type=full"
    headers = {
        "X-API-KEY": API_KEY,
        "Accept": "application/json"
    }

    timeout = aiohttp.ClientTimeout(total=10)  # ⏳ Ограничиваем время ожидания 10 сек

    async with semaphore:  # ⚡ Ограничиваем количество запросов
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error") and data["error"].get("rusText") == "Table Not Found":
                            return "❌ Ошибка: Данные по этому ИНН отсутствуют в базе."
                        return data
                    else:  # Убираем лишний if и правим отступы
                        logger.error(f"❌ Ошибка API: {response.status}, {await response.text()}")
                        return None
        except asyncio.TimeoutError:
            logger.error("❌ Ошибка: Тайм-аут при запросе к API")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе к API: {e}")
            return None


async def fetch_entrepreneur_info(pinfl):
    """Получает информацию о предпринимателе по ПИНФЛ, с ограничением запросов."""
    url = f"https://my3.soliq.uz/api/remote-access-api/entrepreneur/info/{pinfl}"
    headers = {
        "X-API-KEY": API_KEY,
        "Accept": "application/json"
    }
    
    timeout = aiohttp.ClientTimeout(total=10)  # Таймаут в 10 секунд

    async with semaphore:  # Ограничение количества запросов
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return await response.json()  # ✅ Исправленный отступ
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Ошибка API: {response.status}, {error_text}")
                            return None
                except aiohttp.ClientResponseError as e:
                    logger.error(f"❌ Ошибка ответа API: {e.status} - {e.message}")
                except aiohttp.ClientConnectionError:
                    logger.error("❌ Ошибка соединения с API")
                except aiohttp.ClientPayloadError:
                    logger.error("❌ Ошибка обработки данных от API")
        except asyncio.TimeoutError:
            logger.error("❌ Ошибка: Таймаут при запросе к API")
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при запросе к API: {e}")
        
        return None

# Функция для проверки ИНН и получения информации о компании
async def check_inn(inn: str) -> str:
    if not (isinstance(inn, str) and inn.isdigit() and len(inn) == 9):
        return "❌ Неверный формат ИНН. Должно быть 9 цифр."

    company_info = await fetch_company_info(inn)  # ⬅️ Здесь вызывается API
    logger.debug(f"📢 Ответ API в check_inn: {company_info}")

    if not company_info or not isinstance(company_info, dict):
        logger.error(f"❌ Ошибка API: company_info = {company_info}")  # Логируем неожиданные данные
        return "❌ Ошибка: Юр.лицо с таким ИНН не найдено."

    if "error" in company_info and isinstance(company_info["error"], dict):
        error_text = company_info["error"].get("rusText", "Неизвестная ошибка")
        logger.error(f"❌ Ошибка API: {error_text}")  # Логируем точную ошибку API
        return f"❌ Ошибка API: {error_text}"

    response = await format_company_response(company_info)
    return response
       
async def send_large_message(update, text):
    max_length = 4096  # Лимит Telegram

    try:
        if not isinstance(text, str):  # Проверяем, что text — строка
            text = str(text)

        logger.info(f"📩 Длина перед отправкой: {len(text)} символов")  # Логируем длину

        messages = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        for msg in messages:
            msg = msg.strip().replace("\u200e", "").replace("\u202e", "")
            await update.message.reply_text(msg)

        # Разбиваем сообщение по строкам
        lines = text.split("\n")
        message = ""

        for line in lines:
            if len(message) + len(line) + 1 > max_length:
                logger.info(f"📩 Отправка блока: {len(message)} символов")
                await update.message.reply_text(message)
                message = ""

            message += line + "\n"

        if message:
            logger.info(f"📩 Отправка последнего блока: {len(message)} символов")
            await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"❌ Ошибка при отправке сообщения: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при отправке сообщения. Попробуйте позже.")

async def check_pinfl(pinfl):
    """Проверяет ПИНФЛ и возвращает информацию о ИП."""
    if isinstance(pinfl, str) and len(pinfl) == 14 and pinfl.isdigit():
        try:
            response = await fetch_entrepreneur_info(pinfl)
        except Exception as e:
            logger.error(f"❌ Ошибка запроса к API: {e}")
            return "❌ Ошибка при получении данных. Попробуйте позже."

        if not response or not isinstance(response, dict):
            return "❌ Ошибка: Данные по ПИНФЛ недоступны."

        # 🔹 Основные данные
        pinfl_masked = mask_pinfl(response.get("pinfl", "Не указано"))
        registration_date = response.get("registrationDate", "Не указано")
        begin_date = response.get("beginDate", "Не указано")
        end_date = response.get("endDate", "Не указано")

        if end_date == "01.01.3000":
            end_date = "Без срока окончания"

        # 🔹 Деятельность и адрес
        activity_uz = response.get("activityTypeName", {}).get("uz")
        activity_ru = translate_activity(activity_uz) if activity_uz else "Не указано"
        activity = activity_ru if activity_ru != activity_uz else activity_uz or "Не указано"
        address = response.get("entrepreneurshipAddress", {}).get("address", "Не указано")

        # 🔹 Руководство
        director = response.get("entrepreneurshipDirector") or {}
        director_last = director.get("lastName", "").strip()
        director_first = director.get("firstName", "").strip()
        director_middle = director.get("middleName", "").strip()
        director_full = " ".join(filter(None, [director_last, director_first, director_middle])) or "Не указано"

        # Контактные данные
        phone_data = response.get("entrepreneurshipContact")
        phone = str(phone_data.get("phoneNumber", "Не указано")).strip() if phone_data and isinstance(phone_data, dict) else "Не указано"

        # 🔹 Налоговая информация
        status = response.get("status", {}).get("name", {}).get("uz") or "Не указано"
        is_vat_taxpayer = response.get("isVatTaxpayer")
        vat_status = "Является плательщиком НДС" if is_vat_taxpayer else "Не является плательщиком НДС"
        tax_mode = response.get("taxModeName", {}).get("ru") or "Не указано"
        taxpayer_type = response.get("taxpayerTypeName", {}).get("ru") or "Не указано"

        return (
            f"📌 ПИНФЛ: {pinfl_masked}\n"
            f"👤 ФИО предпринимателя: {director_full}\n"
            f"📆 Дата регистрации: {registration_date}\n"
            f"📆 Дата начала: {begin_date}\n"
            f"📆 Дата окончания: {end_date}\n"
            f"💼 Вид деятельности: {activity}\n"
            f"🏠 Адрес: {address}\n"
            f"📞 Контактная информация: {phone}\n"
            f"📍 Статус: {status}\n"
            f"📜 Налоговый режим: {tax_mode}\n"
            f"🆔 Тип налогоплательщика: {taxpayer_type}\n"
            f"📜 НДС: {vat_status}"
        )

    return "❌ ИП с таким ПИНФЛ не найдено."


MCHJ_VARIANTS = [
    "MAS'ULIYATI CHEKLANGAN JAMIYAT",
    "Masʼuliyati cheklangan jamiyat",
    "MAS‘ULIYATI CHEKLANGAN YOKI QO‘SHIMCHA MAS‘ULIYATLI JAMIYAT",
    "MCHJ"
]

from datetime import datetime

def pluralize_years(years):
    return f"{years} " + ("лет" if 11 <= years % 100 <= 19 or years % 10 in [0, 5, 6, 7, 8, 9] else "года" if years % 10 in [2, 3, 4] else "год")

def calculate_company_age(registration_date):
    """
    Вычисляет срок деятельности компании в годах и днях.
    :param registration_date: строка в формате "DD.MM.YYYY" или "YYYY-MM-DD"
    :return: строка "X лет Y дней" или "Неизвестно"
    """
    if not registration_date or registration_date in ["Неизвестно", "—", ""]:
        return "Неизвестно"

    try:
        # Определяем формат даты
        if "." in registration_date:  # Формат "DD.MM.YYYY"
            reg_date = datetime.strptime(registration_date, "%d.%m.%Y").date()
        elif "-" in registration_date:  # Формат "YYYY-MM-DD"
            reg_date = datetime.strptime(registration_date, "%Y-%m-%d").date()
        else:
            return "Неизвестно"

        today = datetime.today().date()
        delta = today - reg_date

        from dateutil.relativedelta import relativedelta
        years = relativedelta(today, reg_date).years
        days = (today - (reg_date + relativedelta(years=years))).days
        
        # Форматируем корректно "год", "года" или "лет"
        years_text = pluralize_years(years)

        return f"{years_text} {days} дней" if years > 0 else f"{days} дней"
    except ValueError:
        return "Неизвестно"
        
import re

# Список юридических форм, которые надо убирать
LEGAL_FORMS = ["ООО", "АО", "МЧЖ", "СП", "ЗАО", "ГУП", "ЧП", "ДП"]

def extract_company_name(full_name):
    """Извлекает чистое название компании, убирая кавычки и юр. форму."""
    if not full_name:
        return "Не указано"

    # 1️⃣ Попытка извлечь текст в кавычках
    match = re.search(r'"([^"]+)"', full_name)
    if match:
        return match.group(1)  # Берём только содержимое кавычек

    # 2️⃣ Если кавычек нет, убираем юр. форму (ООО, МЧЖ и т. д.)
    words = full_name.split()
    words = [word for word in words if word not in LEGAL_FORMS]  # Убираем юр. форму
    return " ".join(words).strip() if words else "Не указано"

# Утилиты
def mask_pinfl(pinfl):
    return f"{pinfl[0]}{'*' * 12}{pinfl[-1]}" if str(pinfl).isdigit() and len(pinfl) == 14 else "Некорректный ПИНФЛ"

def validate_pinfl(pinfl):
    """Проверяет, что ПИНФЛ состоит максимум из 14 цифр и ничего больше."""
    pinfl = str(pinfl).strip()  # Убираем пробелы и приводим к строке

    if not pinfl.isdigit():  # Проверяем, что только цифры
        return None  

    if len(pinfl) > 14:  # Если больше 14 символов – обрезаем
        pinfl = pinfl[:14]

    return pinfl if len(pinfl) == 14 else None  # Возвращаем только если ровно 14 цифр
   
def format_full_name(name):
    """Приводит ФИО к формату: Фамилия Имя Отчество."""
    if not name or name == "Не указано":
        return "Не указано"

    parts = name.split()

    if len(parts) == 3:  # Если три слова (Имя Фамилия Отчество)
        return f"{parts[1]} {parts[0]} {parts[2]}"  # Меняем местами Имя и Фамилию
    elif len(parts) == 2:  # Если только Имя Фамилия
        return f"{parts[1]} {parts[0]}"
    
    return name  # Если формат странный, оставляем как есть
    
def format_founder(founder):
    """Определяет правильное отображение учредителей по ИНН."""
    tin = founder.get('tin', '')
    name = founder.get('name', 'Не указано')
    share = founder.get('sharePersent', 'Не указано')

    cleaned_name = name  # Инициализация по умолчанию

    if tin.isdigit():
        if len(tin) == 14:  # Физлицо (ИНН 14 цифр)
            return f"🔹 {format_full_name(name)} (Доля: {share}%)"

    elif len(tin) == 9:
        cleaned_name = clean_company_name(name)

        if tin.startswith('2') or tin.startswith('3'):
            return f"🔹 {cleaned_name} (ИНН: {tin}, Доля: {share}%)"
        elif tin.startswith('9'):
            return f"🔹 {cleaned_name} (ИНН: {tin}, Доля: {share}%)"

    # Если не попало в условия, используем исправленное название
    return f"🔹 {cleaned_name} (ИНН: {tin}, Доля: {share}%)"

# Загружаем businessStructure.json
try:
    with open("businessStructure.json", "r", encoding="utf-8") as f:
        BUSINESS_STRUCTURE = json.load(f)
except Exception as e:
    BUSINESS_STRUCTURE = []
    print(f"⚠ Ошибка загрузки businessStructure.json: {e}")

# Функция для поиска businessStructure по коду
def get_business_structure_name(code):
    """Возвращает название бизнес-структуры по коду из API."""
    for entry in BUSINESS_STRUCTURE:
        if entry["CODE"] == code:
            return entry["NAME_RU"]  # Берём русское название
    return "Неизвестно"

async def format_company_response(data):
    """Форматирует информацию о компании для вывода."""
    response = ""
    company = data.get('company', {}) or {}

    # 🛑 Логируем входные данные перед обработкой
    logger.info(f"📢 Входные данные в format_company_response: {json.dumps(data, ensure_ascii=False, indent=2)}")

    # Основные данные
    is_dominant = await check_dominant_company(company.get('tin', ''))
    company_name = extract_company_name(company.get('name', 'Не указано'))
    
    director = data.get('director', {}) or {}
    director_contact = data.get('directorContact', {}) or {}
    phone_director = director_contact.get('phone', 'Не указано')
    accountant = data.get('accountant', {}) or {}
    accountant_contact = data.get('accountantContact', {}) or {}
    founders = data.get('founders', []) or []
    company_contact = company.get('companyContact', {}) or {}

    # Получаем код ОПФ
    opf_code = company.get("opf", "Неизвестно")
    opf_name = get_opf_name(opf_code)  # Полное название ОПФ

    # Получаем код ОКЭД
    oked_code = company.get("oked", "Не указан")

    # Получаем вид деятельности
    activity_uz = company.get('okedDetail', {}).get('name_uz', 'Не указано')
    activity_ru = company.get('okedDetail', {}).get('name_ru', 'Не указано')
    activity = activity_ru if activity_ru != 'Не указано' else activity_uz

    # Формируем итоговое название с ОПФ в начале и кавычками
    business_structure_code = company.get("businessStructure", None)
    business_structure_name = get_business_structure_name(business_structure_code)
    formatted_name = f'{business_structure_name} "{company_name}"'
    
    # Получаем статус компании
    company_status = company.get("status", "Не указано")

    # Получаем дату ликвидации и дату обновления статуса
    liquidation_date = company.get("liquidationDate", "Не указана")
    status_updated = company.get("statusUpdated", "Не указана")

    # Формируем строку с информацией о ликвидации (если есть)
    liquidation_info = ""
    if liquidation_date != "Не указана":
        liquidation_info = f"📅 Дата ликвидации: {liquidation_date}\n"
    if status_updated != "Не указана":
        liquidation_info += f"📅 Дата обновления статуса: {status_updated}\n"
        
    # Телефон и Email из directorContact
    phone = director_contact.get('phone', 'Не указано')
    email = director_contact.get('email', 'Не указано')

    # НДС
    raw_vat_status = company.get('vatStatus', '')
    vat_status = raw_vat_status  # Копируем оригинальное значение

    # Инициализируем risk_message, чтобы избежать ошибки UnboundLocalError
    risk_message = ""

    if vat_status in [None, ""]:
        vat_status = "Не является плательщиком НДС"
    elif vat_status == "ACTIVE":
        vat_status = "✅Сертификат активный✅"
    elif vat_status == "SUSPENDED":
        vat_status = '⛔ У компании "приостановлен" НДС!'
        risk_message = (
            "⚠ Внимание: НДС компании временно неактивен!\n"
            "📌 Возможные причины:\n"
            " 🆘 Компания временно приостановила деятельность.\n"
            " 💰 Возможны налоговые проблемы.\n"
            " 🏢 Возможны проверки со стороны налоговых органов.\n"
            "🔎 Рекомендуется проверить актуальные данные в налоговой службе."
        )

    # Логирование перед отправкой пользователю
    print(f"[DEBUG] Анализ рисков НДС: {risk_message}")  # Теперь ошибки не будет

    # Получаем юридический адрес (Billing Address)
    billing_address = data.get("companyBillingAddress", {})

    # Извлекаем данные с безопасной обработкой
    region = billing_address.get("region", {}).get("name_ru", "")
    district = billing_address.get("district", {}).get("name_ru", "")
    street = billing_address.get("streetName", "")
    postcode = billing_address.get("postcode", "")

    # Логируем, что получили
    logger.info(f"📍 Исправленный юридический адрес: {billing_address}")

    # Собираем строку адреса
    address_parts = [region, district, street]
    company_address = ", ".join(filter(None, address_parts)).strip()

    # Логируем итоговый адрес
    logger.info(f"📍 Итоговый исправленный адрес: {company_address}")

    print(f"Итоговый адрес: {company_address}")

    # Дата первичной регистрации
    registration_date = company.get("registrationDate", "Не указано")
    if registration_date and registration_date not in ["Не указано", ""]:
        registration_date = f"{registration_date} г."

    # Дата перерегистрации (если есть)
    reregistration_date = company.get("reregistrationDate", "")
    if reregistration_date:
        reregistration_date = f"{reregistration_date} г."
    else:
        reregistration_date = "—"

    # Номер регистрации
    registration_number = company.get("registrationNumber", "Не указано")

    # Считаем срок деятельности
    company_age = calculate_company_age(company.get("registrationDate", ""))
        
    # Логируем API-ответ полностью
    logger.debug("📢 Ответ API", extra={"data": data})

    # Берём avgNumberEmployees напрямую из data, а НЕ из company
    employees = data.get('companyExtraInfo', {}).get('avgNumberEmployees')

    # Логируем полученные данные
    logger.info(f"👥 avgNumberEmployees (до обработки): {employees}")

    # Проверяем, если employees — число, иначе "Не указано"
    employees = str(employees) if isinstance(employees, (int, float)) else "Не указано"

    # Логируем итоговый результат
    logger.info(f"👥 Количество сотрудников (после обработки): {employees}")

    # Форматирование уставного фонда
    business_fund = f"{int(company.get('businessFund', 0)):,} сум".replace(",", " ")

    # Формирование списка учредителей
    founders_info = "\n".join(f"🔹 {format_founder(f)}" for f in founders[:10]) or "Не указано"
    
    # Дополнительные данные
    vat_number = company.get('vatNumber', 'Не указано')
    business_type = company.get('businessTypeDetail', {}).get('name_ru', 'Не указано')

    # Формируем список учредителей (до 10)
    max_founders_display = 10  
    extra_founders = max(0, len(founders) - max_founders_display)

    founders_info = "\n".join([format_founder(founder) for founder in founders[:10]])

    if extra_founders:
        founders_info = (founders_info + "\n" if founders_info else "") + f"...и еще {extra_founders} учредителей."

    if not founders_info:
        founders_info = "Не указано"
        
    # Обработка бухгалтера (чтобы не было "Не указано Не указано Не указано")
    buh_first = accountant.get('firstName', '').strip()
    buh_last = accountant.get('lastName', '').strip()
    buh_middle = accountant.get('middleName', '').strip()

    # Проверяем, есть ли хотя бы одно поле бухгалтера
    if any([buh_first, buh_last, buh_middle]):
        buh_full = " ".join(filter(None, [buh_last, buh_first, buh_middle])).strip()
    else:
        buh_full = "Нет"
    
    # Проверяем телефон бухгалтера
    buh_phone = accountant_contact.get('phone', '').strip()
    if not buh_phone:
        buh_phone = "Нет"

    # Получаем статус компании
    company_status = company.get("statusDetail", {}).get("name_ru", "Не указано")
       
    # Добавляем срок деятельности перед основным формированием response
    registration_date = company.get("registrationDate", "")
    company_age = calculate_company_age(registration_date)

    # После расчёта снова добавляем "г.", чтобы не потерять его
    if registration_date:
        registration_date = f"{registration_date} г."

    # 🔹 Запрашиваем данные из Multibank API
    court_data = await get_multibank_data(company.get("tin", ""), "court")
    license_data = await get_multibank_data(company.get("tin", ""), "license")
    marks_data = await get_multibank_data(company.get("tin", ""), "marks")

    # 🔹 Формируем блок с судебными делами
    if "error" not in court_data and court_data.get("court"):
        response += "\n=== ⚖️ Судебные дела ===\n"
        for case in court_data["court"][:3]:  # Берём максимум 3 дела
            response += (
                f"🔹 Дело №{case.get('court_case_number', '—')}, {case.get('court_hearing_date', '—')}\n"
                f"📌 Суд: {case.get('court_name', '—')}\n"
                f"⚔ Истец: {case.get('court_claimant', '—')}\n"
                f"⚖ Ответчик: {case.get('court_defendant', '—')}\n"
                f"📜 Статья: {case.get('court_article', '—')}\n"
                f"📅 Дата заседания: {case.get('court_hearing_date', '—')} {case.get('court_hearing_time', '—')}\n"
                f"🏛 Судья: {case.get('court_judge', '—')}\n"
                f"📜 Результат: {case.get('court_result', '—')}\n\n"
            )
    else:
        response += "⚖️ Судебные дела: Нет данных\n"

    # 🔹 Формируем блок с лицензиями
    if "error" not in license_data and license_data.get("license"):
        response += "\n=== 📜 Лицензии ===\n"
        for lic in license_data["license"][:3]:  # Берём максимум 3 лицензии
            response += (
                f"🔹 {lic.get('license_name', '—')} (№{lic.get('license_number', '—')})\n"
                f"📅 Регистрация: {lic.get('license_registration_date', '—')}\n"
                f"📅 Действует до: {lic.get('license_expiry_date', '—')}\n"
                f"🏛 Орган: {lic.get('license_organization', '—')}\n\n"
            )
    else:
        response += "📜 Лицензии: Нет данных\n"

    # 🔹 Формируем блок с торговыми знаками
    if "error" not in marks_data and marks_data.get("marks"):
        response += "\n=== ™ Торговые знаки ===\n"
        for mark in marks_data["marks"][:3]:  # Берём максимум 3 ТЗ
            response += (
                f"🔹 {mark.get('ima_marks_name', '—')} (№{mark.get('ima_marks_number', '—')})\n"
            )
    else:
        response += "™ Торговые знаки: Нет данных\n"

    logger.info(f"📢 Данные Multibank добавлены в ответ: {response}")

    # Форматирование ответа
    response = (
        f"🔹 {formatted_name}\n"
        f"📍 Адрес: {company_address}\n"
        f"⚔️ Статус субъекта: {company_status}\n"
        f"🏢 ОПФ: {opf_name}\n"
        f"📆 Дата регистрации: {registration_date}\n"
        f"🔢 Номер регистрации: {registration_number}\n"
        f"🖇 Дата перерегистрации: {reregistration_date}\n"
        f"📆 Срок деятельности: {company_age}\n"
    )

    response += (
        f"🆔 Код ОКЭД: {oked_code}\n"
        f"💼 Вид деятельности: {activity}\n"
        f"💲 Уставной капитал: {business_fund}\n"
        f"👥 Количество сотрудников: {employees}\n"
        f"🏢 Категория предприятия: {company.get('businessTypeDetail', {}).get('name_ru', 'Не указано')}\n"
        f"📞 Контактная информация: {phone}\n"
        f"📫 Email: {email}\n\n"
        "=== Налоговая информация ===\n"
        f"📜 Статус НДС: {vat_status}\n"
        f"🆔 Номер свидетельства НДС: {company.get('vatNumber', 'Не указан')}\n"
        f"{risk_message}\n\n"
        "=== Важные данные ===\n"
        "⚡️Рейтинг предпринимательской деятельности: Нет данных\n"
        f"🔥️Доминирует на товарном или финансовом рынке: {'Да ✅' if is_dominant else 'Нет ❌'}\n\n"
        "=== Дополнительная информация ===\n"
        "❌Является сомнительной компанией: Нет данных\n"
        "👮Исполнительные производства в БПИ: Нет данных\n"
        "⛩Резидент IT PARK: Нет данных\n"
        f"⚖️Судебные истории: Нет данных\n"
        f"🗞Лицензии: Нет данных\n"
        f"🛒Торговые знаки: Нет данных\n"
        "👥Взаимосвязанные лица: Нет данных\n\n"
        "=== Руководство ===\n"
        f"👤 Директор: {director.get('lastName', 'Не указано')} {director.get('firstName', 'Не указано')} {director.get('middleName', 'Не указано')}\n"
        f"📞 Телефон директора: {phone_director}\n\n"
        f"📊 Бухгалтер: {accountant.get('lastName', 'Не указано')} {accountant.get('firstName', 'Не указано')} {accountant.get('middleName', 'Не указано')}\n"
        f"📞 Телефон бухгалтера: {accountant_contact.get('phone', 'Не указано')}\n\n"
        "=== Учредители ===\n"
        f"{founders_info}"
    )
    
    return response

ERROR_CHAT_ID = 6116094248  # ID владельца бота

async def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": ERROR_CHAT_ID, "text": message}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

# Отправка ошибки в Telegram    
async def fetch_data(url):
    """Фейковая функция для запроса данных (замените на реальную логику)."""
    import asyncio
    await asyncio.sleep(1)  # Имитация задержки запроса
    return {"status": "ok", "data": f"Данные с {url}"}
    
# Запускаем async-функцию из main()
async def main():
    print("Бот запущен!")
    # Здесь нужно запустить Telegram-бота
    # Например, если у тебя используется `Application` из `python-telegram-bot`:
    # app = Application.builder().token(API_TOKEN).build()
    # app.add_handler(CommandHandler("start", start))
    # await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()  # Фикс для Jupyter и Windows
    asyncio.run(main())   # Запуск главной функции


# Telegram-бот
def main_keyboard():
    """Генерирует клавиатуру для меню."""
    keyboard = [
        ["Проверить Юр.лицо", "Проверить ИП"],
        ["Стоимость", "Отчёт", "Связаться с нами"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    keyboard = [
        ["Проверить Юр.лицо", "Проверить ИП"],
        ["Стоимость", "Отчёт", "Связаться с нами"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Привет! Бот работает!", reply_markup=reply_markup)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    print("✅ Бот запущен в режиме Polling...")
    application.run_polling()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений."""
    try:
        user_data = context.user_data
        text = update.message.text.strip()
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name

        logger.info(f"📢 Получено сообщение от {user_name} (ID: {user_id}): {text}")

        if text == "Проверить Юр.лицо":
            user_data["waiting_for_inn"] = True
            await update.message.reply_text("Введите ИНН (9 цифр):")
            return

        elif text == "Проверить ИП":
            user_data["waiting_for_pinfl"] = True
            await update.message.reply_text("Введите ПИНФЛ (14 цифр):")
            return

        elif text == "Стоимость":
            await update.message.reply_text("Стоимость:\n- 100 000 сум, за один запрос с отчётом, 50 000 сум без отчёта")

        elif text == "Отчёт":
            await update.message.reply_text("Полный отчёт доступен, в личном кабинете")

        elif text == "Связаться с нами":
            await update.message.reply_text("Введите имя и номер телефона")
            user_data["waiting_for_contact"] = True

        if user_data.get("waiting_for_inn"):
            if text.isdigit() and len(text) == 9:
                user_data["waiting_for_inn"] = False
                try:
                    response = await check_inn(text)
                    await send_large_message(update, response)
                except Exception as e:
                    logger.error(f"❌ Ошибка в check_inn: {e}", exc_info=True)
                    await update.message.reply_text("❌ Ошибка при проверке ИНН. Попробуйте позже.")
            else:
                 await update.message.reply_text("❌ Неверный формат ИНН. Должно быть 9 цифр.")
            return
            
        else:
            await update.message.reply_text("❌ Неизвестная команда. Выберите действие из меню.")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_message: {e}", exc_info=True)
        await update.message.reply_text("❌ Внутренняя ошибка. Попробуйте позже.")

        if user_data.get("waiting_for_pinfl"):
            text = text.strip()
            if text.isdigit() and len(text) == 14:
                user_data["waiting_for_pinfl"] = False
                try:
                    response = await check_pinfl(text)
                    await send_large_message(update, response)
                except Exception as e:
                    logger.error(f"❌ Ошибка в check_pinfl: {e}", exc_info=True)
                    response = "❌ Ошибка при проверке ПИНФЛ. Попробуйте позже."

                await update.message.reply_text("❌ Ошибка: ПИНФЛ должен содержать ровно 14 цифр.")
                
        if user_data.get("waiting_for_contact"):
            logger.info(f"📩 Отправляем владельцу (ID: {OWNER_ID}): {text}")

            try:
                if not isinstance(OWNER_ID, int):  # Проверяем, что OWNER_ID - это число
                    logger.error("❌ Ошибка: OWNER_ID не задан или имеет неверный формат!")
                else:
                    await context.bot.send_message(
                        chat_id=OWNER_ID,
                        text=f"📩 Новый запрос от {user_name} (ID: {user_id})\n\n{text}"
                    )
                    await update.message.reply_text("✅ Данные отправлены! Мы свяжемся с вами.")
                       
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке сообщения владельцу: {e}", exc_info=True)
                await update.message.reply_text("❌ Ошибка при отправке данных. Попробуйте позже.")

            user_data["waiting_for_contact"] = False

    except Exception as e:  # ✅ Теперь верхний try закрывается
        logger.error(f"❌ Ошибка в handle_message: {e}", exc_info=True)
        await update.message.reply_text("❌ Внутренняя ошибка. Попробуйте позже.")

# ✅ Теперь `try:` закрыт, и можно писать `async def main():`
async def main():
    """Основная функция для запуска бота."""
    try:
        application = ApplicationBuilder().token(TOKEN).build()
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_handler(CommandHandler("check_multibank", check_multibank))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("🚀 Бот запущен и ожидает сообщения...")
        await application.run_polling()

    except Exception as e:
        logger.error(f"❌ Ошибка в main: {e}", exc_info=True)

if __name__ == "__main__":
    nest_asyncio.apply()  # Фикс для Jupyter и Windows

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Проверяем, не выполняется ли уже event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
