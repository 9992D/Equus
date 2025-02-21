import requests
from bs4 import BeautifulSoup
import json
import re
import sys

def scraper_course(date, reunion, course):
    url = f"https://www.equidia.fr/courses/{date}/{reunion}/{course}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Erreur lors du scraping de la page {url}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    course_data = {
        "date": date,
        "reunion": reunion,
        "course": course,
        "prix": None,
        "hippodrome": None,
        "style": None,
        "discipline": None,
        "nombre_de_partants": None,
        "allocation": None,
        "terrain": None,
        "meteo": {
            "temperature": None,
            "ciel": None,
            "vent_vitesse": None,
            "vent_direction": None
        },
        "enjeux_sg": None
    }

    try:
        header_section = soup.find("div", {"class": "title-holder fill-primary-blue"})
        if header_section:
            h1 = header_section.find("h1")
            if h1:
                b = h1.find("b")
                if b:
                    # Utiliser string=True au lieu de text=True
                    hippodrome_sibling = b.find_next_sibling(string=True)
                    hippodrome = hippodrome_sibling.strip() if hippodrome_sibling else ""
                    course_data["hippodrome"] = hippodrome

                prix_text = h1.text.strip()
                if "PRIX" in prix_text:
                    prix_index = prix_text.find("PRIX")
                    course_data["prix"] = prix_text[prix_index:].strip()

        style_section = soup.find("p", {"class": "text-primary-blue"})
        if style_section:
            course_data["style"] = style_section.text.strip()

        conditions_section = soup.find("div", {"id": "conditions", "class": "default"})
        
        if conditions_section:
            condition_infos = conditions_section.find_all("div", {"class": "condition-summary--main--info"})
            
            for info in condition_infos:
                text = info.find("div", {"class": "condition-summary--main--info--text"})
                if text:
                    text_content = text.text.strip()

                    if "Terrain" in text_content:
                        terrain_info = text_content.replace("Terrain", "").strip()
                        course_data["terrain"] = terrain_info if terrain_info != "" else None

                    elif "Discipline" in text_content:
                        course_data["discipline"] = text_content.replace("Discipline", "").strip()

                    elif "Partants" in text_content:
                        partants_str = text_content.replace("Partants", "").strip()
                        try:
                            course_data["nombre_de_partants"] = int(partants_str)
                        except ValueError:
                            course_data["nombre_de_partants"] = partants_str

                    elif "Allocations" in text_content:
                        allocation_str = text_content.replace("Allocations", "").strip()
                        allocation_str = allocation_str.replace("€", "").replace(" ", "").strip()
                        try:
                            course_data["allocation"] = int(allocation_str)
                        except ValueError:
                            course_data["allocation"] = allocation_str

                    elif "Enjeux SG" in text_content:
                        enjeux_str = text_content.replace("Enjeux SG", "").strip()
                        enjeux_str = enjeux_str.replace("€", "").replace(" ", "").strip()
                        try:
                            course_data["enjeux_sg"] = int(enjeux_str)
                        except ValueError:
                            course_data["enjeux_sg"] = enjeux_str

                    else:
                        # Vérifier si c'est la météo (présence de ° et km/h)
                        if "°" in text_content and "km/h" in text_content:
                            meteo_info = text_content.split()
                            # On s'attend à quelque chose du genre : ["7°", "très", "nuageux", "9km/h", "Sud-Ouest"]
                            if len(meteo_info) >= 1:
                                # Temperature
                                temp_str = meteo_info[0].replace("°", "")
                                try:
                                    course_data["meteo"]["temperature"] = int(temp_str)
                                except ValueError:
                                    course_data["meteo"]["temperature"] = temp_str

                                # Trouver l'index du vent
                                vent_index = None
                                for i in range(1, len(meteo_info)):
                                    if re.match(r"^\d+km/h$", meteo_info[i]):
                                        vent_index = i
                                        break

                                if vent_index is not None:
                                    # Le ciel est tout ce qui se trouve entre l'indice 1 et vent_index
                                    ciel_parts = meteo_info[1:vent_index]
                                    if ciel_parts:
                                        course_data["meteo"]["ciel"] = " ".join(ciel_parts)
                                    else:
                                        course_data["meteo"]["ciel"] = None

                                    # vent vitesse
                                    vent_speed_str = meteo_info[vent_index].replace("km/h", "")
                                    try:
                                        course_data["meteo"]["vent_vitesse"] = int(vent_speed_str)
                                    except ValueError:
                                        course_data["meteo"]["vent_vitesse"] = vent_speed_str

                                    # vent direction (si présente)
                                    if vent_index < len(meteo_info) - 1:
                                        course_data["meteo"]["vent_direction"] = " ".join(meteo_info[vent_index+1:])
                                    else:
                                        course_data["meteo"]["vent_direction"] = None
                                else:
                                    # Pas de vent, donc tout le reste est le ciel
                                    if len(meteo_info) > 1:
                                        course_data["meteo"]["ciel"] = " ".join(meteo_info[1:])
                                    else:
                                        course_data["meteo"]["ciel"] = None
    except Exception as e:
        print(f"Erreur lors de l'extraction des données pour {date}/{reunion}/{course}: {e}")
    
    return course_data

def save_course_data(date, reunion, course):
    try:
        # Charger le fichier condition_course.json
        try:
            with open("condition_course.json", "r", encoding="utf-8") as json_file:
                course_list = json.load(json_file)
                if not isinstance(course_list, list):
                    course_list = []
        except (FileNotFoundError, json.JSONDecodeError):
            print("Fichier condition_course.json introuvable ou vide. Initialisation d'une nouvelle liste.")
            course_list = []

        # Extraire les données de la course
        course_data = scraper_course(date, reunion, course)
        
        if course_data and any(course_data.values()):
            # Ajout des données si elles sont valides
            course_list.append(course_data)
            with open("condition_course.json", "w", encoding="utf-8") as json_file:
                json.dump(course_list, json_file, ensure_ascii=False, indent=4)
            print(f"✅ Données ajoutées pour la course {date} | Réunion {reunion} | {course}.")
        else:
            print(f"❌ Données invalides pour la course {date} | Réunion {reunion} | {course}.")

    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données : {e}")

def main():
    if len(sys.argv) != 4:
        print("Usage: scrapper_condition_course.py <date> <reunion> <course>")
        sys.exit(1)

    date = sys.argv[1]
    reunion = sys.argv[2]
    course = sys.argv[3]

    print(f"Lancement du scraping pour la course {date} - {reunion} - {course}")
    save_course_data(date, reunion, course)

if __name__ == "__main__":
    main()