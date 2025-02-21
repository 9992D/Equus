import sys
import json
from bs4 import BeautifulSoup
import requests

def scrape_table_arrive_data(date, reunion, course):
    """
    Fonction pour extraire les données de la table d'arrivée.
    """
    try:
        url = f"https://www.equidia.fr/courses/{date}/{reunion}/{course}"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', class_='course-result-table')
        if not table:
            print("❌ Table des résultats introuvable.")
            return None

        rows = table.find_all('tr')
        data = []
        for row in rows:
            cells = row.find_all('td')
            if cells:
                classement = cells[0].get_text(strip=True)
                numero = cells[1].get_text(strip=True)
                
                if classement == "NP":
                    cheval = cells[2].find('span', class_='name-cheval').get_text(strip=True)
                    details = cells[2].find_all('span')
                    jockey_entraineur = details[1].get_text(strip=True) if len(details) > 1 else ""
                    jockey, entraineur = jockey_entraineur.split('|') if '|' in jockey_entraineur else (jockey_entraineur, "")
                    
                    row_data = {
                        'classement': classement,
                        'numero': numero,
                        'cheval': cheval,
                        'jockey': jockey.strip(),
                        'entraineur': entraineur.strip(),
                        'status': 'NON PARTANT'
                    }
                else:
                    if 'partant-driver-entraineur' in cells[2].get('class', []):
                        cheval = cells[2].find('span', class_='name-cheval').get_text(strip=True)
                        details = cells[2].find_all('span')
                        jockey_entraineur = details[1].get_text(strip=True) if len(details) > 1 else ""
                        jockey, entraineur = jockey_entraineur.split('|') if '|' in jockey_entraineur else (jockey_entraineur, "")
                    else:
                        cheval = ""
                        jockey = ""
                        entraineur = ""
                    corde = cells[3].get_text(strip=True)
                    poids = cells[4].get_text(strip=True)
                    ecarts = cells[5].get_text(strip=True)

                    row_data = {
                        'classement': classement,
                        'numero': numero,
                        'cheval': cheval,
                        'jockey': jockey.strip(),
                        'entraineur': entraineur.strip(),
                        'corde': corde,
                        'poids': poids,
                        'ecarts': ecarts,
                    }
                
                data.append(row_data)

        return {
            'date': date,
            'reunion': reunion,
            'course': course,
            'result': data
        }
    except Exception as e:
        print(f"Erreur lors du scraping : {e}")
        return None

def save_table_arrive_data(date, reunion, course):
    """
    Sauvegarde les données de la table d'arrivée dans un fichier JSON.
    """
    try:
        try:
            with open("table_arrive.json", "r", encoding="utf-8") as json_file:
                table_arrive_list = json.load(json_file)
                if not isinstance(table_arrive_list, list):
                    table_arrive_list = []
        except (FileNotFoundError, json.JSONDecodeError):
            print("Fichier table_arrive.json introuvable ou vide. Initialisation d'une nouvelle liste.")
            table_arrive_list = []

        table_arrive_data = scrape_table_arrive_data(date, reunion, course)

        if table_arrive_data and any(table_arrive_data.values()):
            table_arrive_list.append(table_arrive_data)
            with open("table_arrive.json", "w", encoding="utf-8") as json_file:
                json.dump(table_arrive_list, json_file, ensure_ascii=False, indent=4)
            print(f"✅ Données de la table d'arrivée ajoutées pour la course {date} | Réunion {reunion} | {course}.")
        else:
            print(f"❌ Données de la table d'arrivée invalides pour la course {date} | Réunion {reunion} | {course}.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données de la table d'arrivée : {e}")

def main():
    if len(sys.argv) != 4:
        print("Usage: scrapper_table_arrive.py <date> <reunion> <course>")
        sys.exit(1)

    date = sys.argv[1]
    reunion = sys.argv[2]
    course = sys.argv[3]

    print(f"Lancement du scraping de la table d'arrivée pour la course {date} - Réunion {reunion} - {course}")
    save_table_arrive_data(date, reunion, course)

if __name__ == "__main__":
    main()
