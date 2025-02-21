#!/usr/bin/env python3
import json
import sqlite3
from datetime import datetime

def clean_int(value):
    """Convertit une valeur en int si possible, sinon retourne None."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def clean_float(value):
    """Convertit une valeur en float si possible, sinon retourne None."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def clean_date(date_str):
    """Convertit une date au format 'YYYY-MM-DD' en objet date ou retourne None."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def time_to_seconds(time_str):
    """
    Convertit un temps au format mm'ss''SS en secondes.
    Exemple : "1'30''50" donnera 90.50 secondes.
    """
    try:
        parts = time_str.replace("'", ":").replace("''", ".").split(":")
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    except (ValueError, IndexError, AttributeError):
        return None

def process_json(data):
    """
    Traite la liste de courses contenue dans le JSON.
    Pour chaque course, extrait les informations de suivi (tracking) pour chaque détail.
    Seuls les enregistrements dont les champs critiques ne sont pas nuls seront conservés.
    Les champs critiques sont :
      - vitessemax_kmh
      - temps_officiel
      - derniers600m
      - derniers200m
      - derniers100m
      - distance_reelle
      - distance_vainqueur
    """
    results = []
    for course in data:
        date = clean_date(course.get("date"))
        reunion = course.get("reunion")
        course_id = course.get("course")
        discipline = course.get("discipline")
        
        for detail in course.get("details", []):
            result = {
                "date": date,
                "reunion": reunion,
                "course": course_id,
                "discipline": discipline,
                "numero": detail.get("numero"),
                "nom": detail.get("nom"),
                "classement": clean_int(detail.get("classement")),
                "vitessemax_kmh": clean_float(detail.get("vitessemax_(km/h)")),
                "temps_officiel": time_to_seconds(detail.get("temps_officiel")),
                "derniers600m": time_to_seconds(detail.get("derniers600m")),
                "derniers200m": time_to_seconds(detail.get("derniers200m")),
                "derniers100m": time_to_seconds(detail.get("derniers100m")),
                "distance_reelle": clean_float(detail.get("distanceréelle")),
                "distance_vainqueur": clean_float(detail.get("distance/vainqueur")),
            }
            # Filtrer les enregistrements dont l'un des champs critiques est nul
            if (result["vitessemax_kmh"] is None or 
                result["temps_officiel"] is None or 
                result["derniers600m"] is None or 
                result["derniers200m"] is None or 
                result["derniers100m"] is None or 
                result["distance_reelle"] is None or 
                result["distance_vainqueur"] is None):
                continue

            results.append(result)
    return results

def save_to_db(results, db_name="courses.db"):
    """
    Enregistre les données de suivi dans la table 'tracking' de la base SQLite existante.
    Pour chaque enregistrement, le script recherche l'identifiant (race_id) correspondant
    dans la table 'races' à partir de la date, de la réunion et du numéro de course.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for entry in results:
        # Vérifier que les champs servant à identifier la course existent
        if entry["date"] is None or entry["reunion"] is None or entry["course"] is None:
            continue

        # Recherche de l'id de la course dans la table races
        cursor.execute("""
            SELECT id FROM races WHERE date = ? AND reunion = ? AND course = ?
        """, (entry["date"], entry["reunion"], entry["course"]))
        race = cursor.fetchone()

        if race is None:
            print(f"Course non trouvée pour tracking: date={entry['date']}, reunion={entry['reunion']}, course={entry['course']}")
            continue

        race_id = race[0]

        # Insertion de l'enregistrement dans la table tracking
        cursor.execute("""
            INSERT INTO tracking (
                race_id, discipline, numero, nom, classement, vitessemax_kmh, 
                temps_officiel, derniers600m, derniers200m, derniers100m, 
                distance_reelle, distance_vainqueur
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            race_id,
            entry["discipline"],
            entry["numero"],
            entry["nom"],
            entry["classement"],
            entry["vitessemax_kmh"],
            str(entry["temps_officiel"]),
            str(entry["derniers600m"]),
            str(entry["derniers200m"]),
            str(entry["derniers100m"]),
            entry["distance_reelle"],
            entry["distance_vainqueur"]
        ))

    conn.commit()
    conn.close()
    print("Les données de tracking ont été enregistrées dans la base SQLite.")

if __name__ == '__main__':
    # Nom du fichier JSON contenant les données de tracking
    json_file = "tracking_course.json"  # Adaptez le nom du fichier JSON si nécessaire

    # Lecture et traitement du fichier JSON
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    processed_data = process_json(data)
    save_to_db(processed_data)
