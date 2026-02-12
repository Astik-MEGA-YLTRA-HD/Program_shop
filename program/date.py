def fun(a, m_count, d=[31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]):
    parts = a.split("-")
    year = int(parts[0])
    month = int(parts[1]) - 1  # Начинаем счёт месяцев с 0
    day = int(parts[2])

    result_dates = []

    for _ in range(m_count):
        # Берём минимум между максимальным числом дней в месяце и выбранным днем
        current_day = min(d[month], day)
        
        # Создаем строку даты
        date_str = f"{year}-{(month + 1):02}-{current_day:02}"
        result_dates.append(date_str)
        
        # Переходим к следующему месяцу
        month += 1
        if month >= len(d):
            month = 0
            year += 1

    return result_dates