import json
import os
import sys
from datetime import datetime, timedelta
import subprocess

def load_list_course(file_path):
    """
    Charge les données depuis list_course.json
    """
    if not os.path.exists(file_path):
        print(f"Le fichier {file_path} n'existe pas.")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_course_data(date, reunion, course):
    """
    Fonction pour appeler scrapper_condition_course.py et sauvegarder les conditions des courses.
    """
    print(f"Récupération des données pour la date {date}, Réunion {reunion}, Course {course}...")
    subprocess.run(["python", "scrapper_condition_course.py", date, reunion, course])
    subprocess.run(["python", "scrapper_tracking_course.py", date, reunion, course])
    subprocess.run(["python", "scrapper_table_arrive.py", date, reunion, course])

def launch_scrappers(start_date):
    """
    Lance les scrapers pour toutes les dates depuis start_date jusqu'à aujourd'hui.
    """
    # Convertir start_date en objet datetime
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        print("Format de date invalide. Utilisez YYYY-MM-DD.")
        return
    
    today_date = datetime.now()
    
    # Itérer sur toutes les dates jusqu'à aujourd'hui
    current_date = start_date
    while current_date <= today_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"Lancement des scrapers pour la date {date_str}...")
        
        # Lancer scrapper_list_course.py pour mettre à jour list_course.json
        print(date_str)
        subprocess.run(["python", "scrapper_list_course.py", date_str])
        
        # Charger les données depuis list_course.json
        file_path = "list_course.json"
        courses_data = load_list_course(file_path)
        
        if not courses_data:
            print(f"Aucune donnée trouvée pour la date {date_str}.")
        else:
            for course_info in courses_data:
                date = course_info.get("date")
                reunion = course_info.get("reunion")
                nombre_courses = int(course_info.get("nombre_courses", 0))
                
                for i in range(1, nombre_courses + 1):
                    course_id = f"C{i}"
                    save_course_data(date, reunion, course_id)
        
        # Passer à la date suivante
        current_date += timedelta(days=1)
    
    print("Tous les scrappers ont été lancés avec succès pour toutes les dates.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py YYYY-MM-DD")
    else:
        launch_scrappers(sys.argv[1])
