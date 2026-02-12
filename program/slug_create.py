import re

def generate_slug(text):
    # Преобразование русских букв в соответствующие латинские символы
    cyrillic_to_latin = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g',
        'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
        'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
        'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
        'я': 'ya', ' ': '-'
    }
    
    # Замена русских букв на латинские
    for key in cyrillic_to_latin.keys():
        text = text.replace(key.lower(), cyrillic_to_latin[key])
    
    # Удаляем всё кроме латинских букв, цифр и дефисов
    cleaned_text = re.sub(r'[^A-Za-z0-9\-]+', '-', text).strip('-')
    
    # Приведение результата к нижнему регистру
    result = cleaned_text.lower()
    
    return result