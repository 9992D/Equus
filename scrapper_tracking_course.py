import json
import re
import sys
import requests
from bs4 import BeautifulSoup

def scrape_tracking_data(date, reunion, course):
    url = f"https://www.equidia.fr/courses/{date}/{reunion}/{course}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Erreur lors du scraping de la page {url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    tracking_data = {
        "date": date,
        "reunion": reunion,
        "course": course,
        "discipline": None,
        "details": []
    }

    try:
        # Extraire la discipline
        discipline_section = soup.find("div", {"id": "conditions", "class": "default"})
        if discipline_section:
            discipline_info = discipline_section.find("div", {"class": "condition-summary--main--info"})
            if discipline_info and "Discipline" in discipline_info.text:
                tracking_data["discipline"] = discipline_info.text.replace("Discipline", "").strip()

        # Extraction des headers
        headers = []
        table_header = soup.find("tr", {"class": "tracking-table--header"})
        if table_header:
            headers = [th.text.strip().lower().replace(" ", "_") for th in table_header.find_all("th")]

        # Extraction des lignes de données
        table_rows = soup.find_all("tr")[1:]  # Ignorer les headers
        for row in table_rows:
            horse_data = {}

            # Extraire les premières valeurs fixes
            num_span = row.find("span", {"class": "partant-col--num"})
            nom_span = row.find("span", {"class": "partant-col--cheval"})
            classement_td = row.find("td", {"class": "first-col strong-col"})

            horse_data["numero"] = num_span.text.strip() if num_span else None
            horse_data["nom"] = nom_span.text.strip() if nom_span else None
            horse_data["classement"] = classement_td.text.strip() if classement_td else None

            # Extraire les données imbriquées dans les <span align-group>
            data_spans = row.find_all("span", class_="align-group")
            for idx, span in enumerate(data_spans):
                if idx + 3 < len(headers):  # Ajuster pour aligner avec les headers
                    header = headers[idx + 3]
                    horse_data[header] = span.text.strip()

            # Ajouter les données si elles sont valides
            if horse_data.get("numero") and horse_data.get("nom"):
                tracking_data["details"].append(horse_data)

    except Exception as e:
        print(f"Erreur lors de l'extraction des données pour {date}/{reunion}/{course}: {e}")

    return tracking_data

def save_tracking_data(date, reunion, course):
    try:
        # Charger le fichier tracking_course.json
        try:
            with open("tracking_course.json", "r", encoding="utf-8") as json_file:
                tracking_list = json.load(json_file)
                if not isinstance(tracking_list, list):
                    tracking_list = []
        except (FileNotFoundError, json.JSONDecodeError):
            print("Fichier tracking_course.json introuvable ou vide. Initialisation d'une nouvelle liste.")
            tracking_list = []

        # Extraire les donnees de la course
        tracking_data = scrape_tracking_data(date, reunion, course)

        if tracking_data and any(tracking_data.values()):
            # Ajout des donnees si elles sont valides
            tracking_list.append(tracking_data)
            with open("tracking_course.json", "w", encoding="utf-8") as json_file:
                json.dump(tracking_list, json_file, ensure_ascii=False, indent=4)
            print(f"✅ Données de tracking ajoutées pour la course {date} | Reunion {reunion} | {course}.")
        else:
            print(f"❌ Données de tracking invalides pour la course {date} | Reunion {reunion} | {course}.")

    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données de tracking : {e}")

def main():
    if len(sys.argv) != 4:
        print("Usage: scrapper_tracking_course.py <date> <reunion> <course>")
        sys.exit(1)

    date = sys.argv[1]
    reunion = sys.argv[2]
    course = sys.argv[3]

    print(f"Lancement du scraping de tracking pour la course {date} - {reunion} - {course}")
    save_tracking_data(date, reunion, course)

if __name__ == "__main__":
    main()
