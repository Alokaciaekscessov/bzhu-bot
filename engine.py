import csv 
import os 
 

def calculate_nutrition(weight: float, height: float, age: int, gender: str, activity_coef: float) -> dict:
    # Суточная норма калорий и БЖУ
    # Формула Миффлина Сан Жеора
    if gender == "мужской":
       bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5 
    else: 
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
   
    # Коофициент активности (AMR)
    calories = bmr * activity_coef
    
    # Расчет БЖУ (30 / 30 / 40)
    proteins = (calories * 0.30) / 4 
    fats = (calories * 0.30) / 9
    carbs = (calories * 0.40) / 4  
     
    return {
        "calories": round(calories, 1), 
        "proteins": round(proteins, 1), 
        "fats": round(fats, 1), 
        "carbs": round(carbs, 1)
    } 


def save_to_csv(weight: float, height: float, nutrition: dict, filename: str = "result.csv"):
    # Таблица
    headers = ["Вес (кг)", "Рост (см)", "Калории (ккал)", "Белки (г)", "Жиры (г)", "Углеводы (г)"]
    row = [
        weight,
        height, 
        nutrition["calories"],
        nutrition["proteins"], 
        nutrition["fats"], 
        nutrition["carbs"]
    ]
    with open(filename, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(headers)
        writer.writerow(row) 
