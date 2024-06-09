import csv
from datetime import datetime

# Ім'я файлу
filename = 'user-base.csv'

# Читання даних з CSV файлу
with open(filename, mode='r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)

    # Читання та вивід рядків даних з конвертацією activity у формат datetime
    for row in reader:
        row['activity'] = datetime.strptime(row['activity'], '%Y-%m-%d %H:%M:%S')
        print(row)

print(f"Дані успішно прочитані з файлу '{filename}'.")
