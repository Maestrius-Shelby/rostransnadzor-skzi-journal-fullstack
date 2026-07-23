import pandas as pd

file_path = "/var/tmp/rostransnadzor_parser/backend/output/Журнал_СКЗИ.xlsx"

# Читаем с заголовками
df = pd.read_excel(file_path, header=0)

print("📊 Структура файла:")
print(f"  - Строк: {len(df)}")
print(f"  - Колонок: {len(df.columns)}")
print(f"\n📋 Колонки: {list(df.columns)}")

if len(df) > 0:
    print(f"\n✅ Найдено {len(df)} строк с данными")
    print("\n📝 Первые 3 строки:")
    print(df.head(3))
else:
    print("\n❌ Нет данных (только заголовки)")
    
    # Проверяем, есть ли данные во второй строке
    df_raw = pd.read_excel(file_path, header=None)
    print(f"\n🔍 Сырые данные (первые 5 строк):")
    print(df_raw.head(5))
    
    print(f"\n💡 Подсказка: Данные могут начинаться со строки {len(df_raw[df_raw[0].notna()])}")