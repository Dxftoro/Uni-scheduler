dict1 = {'a': 1, 'b': [1, 2, 3], 'c': 3}
dict2 = {'b': [1, 2], 'c': 3, 'd': 6}

# 1. Пересечение ключей
#keys_intersection = dict1.keys() & dict2.keys()  # Или set(dict1.keys()).intersection(dict2.keys())
#print(f"Пересечение ключей: {keys_intersection}")

# 2. Пересечение значений (требует преобразования в множество)
#values_intersection = set(dict1.values()).intersection(dict2.values())
#print(f"Пересечение значений: {values_intersection}")

# 3. Пересечение пар ключ-значение (items())
#items_intersection = dict1.items() & dict2.items()
#print(f"Пересечение пар ключ-значение: {items_intersection}")

# 4. Использование генераторов для получения пересечения значений по ключам
#values_intersection_by_key = {k: dict1[k] for k in dict1.keys() & dict2.keys()}
#print(f"Пересечение значений по ключам: {values_intersection_by_key}")

# 5. Вложенные циклы (менее эффективный, но гибкий)
common_items = {}
for key, value in dict1.items():
    if key in dict2 and dict2[key] == value:
        common_items[key] = value
print(f"Общие пары ключ-значение (вложенные циклы): {common_items}")