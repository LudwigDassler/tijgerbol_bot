#!/usr/bin/env python3
import re

# Читаем текущий файл
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Находим секцию COUNTRIES и заменяем на полный список
old_countries = r"COUNTRIES = \{[^}]+\}"

new_countries = """COUNTRIES = {
    'ru': {'name': 'Россия', 'code': '+7'},
    'ua': {'name': 'Украина', 'code': '+380'},
    'by': {'name': 'Беларусь', 'code': '+375'},
    'kz': {'name': 'Казахстан', 'code': '+7'},
    'us': {'name': 'США', 'code': '+1'},
    'uk': {'name': 'Великобритания', 'code': '+44'},
    'de': {'name': 'Германия', 'code': '+49'},
    'fr': {'name': 'Франция', 'code': '+33'},
    'it': {'name': 'Италия', 'code': '+39'},
    'es': {'name': 'Испания', 'code': '+34'},
    'pl': {'name': 'Польша', 'code': '+48'},
    'cz': {'name': 'Чехия', 'code': '+420'},
    'sk': {'name': 'Словакия', 'code': '+421'},
    'hu': {'name': 'Венгрия', 'code': '+36'},
    'ro': {'name': 'Румыния', 'code': '+40'},
    'bg': {'name': 'Болгария', 'code': '+359'},
    'rs': {'name': 'Сербия', 'code': '+381'},
    'hr': {'name': 'Хорватия', 'code': '+385'},
    'ba': {'name': 'Босния', 'code': '+387'},
    'si': {'name': 'Словения', 'code': '+386'},
    'al': {'name': 'Албания', 'code': '+355'},
    'mk': {'name': 'Северная Македония', 'code': '+389'},
    'me': {'name': 'Черногория', 'code': '+382'},
    'lt': {'name': 'Литва', 'code': '+370'},
    'lv': {'name': 'Латвия', 'code': '+371'},
    'ee': {'name': 'Эстония', 'code': '+372'},
    'fi': {'name': 'Финляндия', 'code': '+358'},
    'se': {'name': 'Швеция', 'code': '+46'},
    'no': {'name': 'Норвегия', 'code': '+47'},
    'dk': {'name': 'Дания', 'code': '+45'},
    'nl': {'name': 'Нидерланды', 'code': '+31'},
    'be': {'name': 'Бельгия', 'code': '+32'},
    'at': {'name': 'Австрия', 'code': '+43'},
    'ch': {'name': 'Швейцария', 'code': '+41'},
    'gr': {'name': 'Греция', 'code': '+30'},
    'tr': {'name': 'Турция', 'code': '+90'},
    'il': {'name': 'Израиль', 'code': '+972'},
    'ae': {'name': 'ОАЭ', 'code': '+971'},
    'sa': {'name': 'Саудовская Аравия', 'code': '+966'},
    'in': {'name': 'Индия', 'code': '+91'},
    'cn': {'name': 'Китай', 'code': '+86'},
    'jp': {'name': 'Япония', 'code': '+81'},
    'kr': {'name': 'Южная Корея', 'code': '+82'},
    'au': {'name': 'Австралия', 'code': '+61'},
    'nz': {'name': 'Новая Зеландия', 'code': '+64'},
    'ca': {'name': 'Канада', 'code': '+1'},
    'mx': {'name': 'Мексика', 'code': '+52'},
    'br': {'name': 'Бразилия', 'code': '+55'},
    'ar': {'name': 'Аргентина', 'code': '+54'},
    'cl': {'name': 'Чили', 'code': '+56'},
    'pe': {'name': 'Перу', 'code': '+51'},
    'co': {'name': 'Колумбия', 'code': '+57'},
    've': {'name': 'Венесуэла', 'code': '+58'},
}"""

content = re.sub(old_countries, new_countries, content, flags=re.DOTALL)

# Обновляем функцию normalize_phone для поддержки всех стран
old_normalize = r"def normalize_phone\(phone_raw, country='ru'\):.*?(?=\n\ndef |\n\n|$)"
new_normalize = """def normalize_phone(phone_raw, country='ru'):
    digits = re.sub(r'\\D', '', phone_raw)
    if phone_raw.startswith('+'): return phone_raw
    code = COUNTRIES.get(country, COUNTRIES['ru'])['code']
    
    # Россия и Казахстан (+7)
    if code == '+7':
        if len(digits) == 10: return '+7' + digits
        if len(digits) == 11 and digits.startswith('8'): return '+7' + digits[1:]
        if len(digits) == 11 and digits.startswith('7'): return '+' + digits
    # Украина (+380)
    elif code == '+380':
        if len(digits) == 9: return '+380' + digits
        if len(digits) == 12 and digits.startswith('380'): return '+' + digits
    # Беларусь (+375)
    elif code == '+375':
        if len(digits) == 9: return '+375' + digits
        if len(digits) == 12 and digits.startswith('375'): return '+' + digits
    # США, Канада (+1)
    elif code == '+1':
        if len(digits) == 10: return '+1' + digits
        if len(digits) == 11 and digits.startswith('1'): return '+' + digits
    # Европейские страны (большинство 9-12 цифр)
    else:
        # Убираем код страны из начала если есть
        if digits.startswith(code[1:]):
            return '+' + digits
        return code + digits
    
    return f'+{digits}'"""

content = re.sub(old_normalize, new_normalize, content, flags=re.DOTALL)

# Записываем обратно
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Страны добавлены!")
print("🌍 Теперь доступны: Россия, Украина, Беларусь, Казахстан, США, Европа, Азия и другие")
