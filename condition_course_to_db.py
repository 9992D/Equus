#!/usr/bin/env python3
import sqlite3
import json

def fill_races(db_file, json_file):
    """
    Insère dans la table 'races' uniquement les courses dont les champs critiques ne sont pas nuls.
    
    Les champs critiques sont :
      - hippodrome
      - style
      - discipline
      - nombre_de_partants
      - allocation
      - terrain
      - enjeux_sg
      - meteo : temperature, ciel, vent_vitesse, vent_direction
    """
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Lecture du fichier JSON
        with open(json_file, "r", encoding="utf-8") as f:
            races_data = json.load(f)

        # Insertion de chaque course dans la table 'races'
        for race in races_data:
            # Extraction des valeurs principales
            date = race.get("date")
            reunion = race.get("reunion")
            course = race.get("course")
            prix = race.get("prix")
            hippodrome = race.get("hippodrome")
            style = race.get("style")
            discipline = race.get("discipline")
            nombre_de_partants = race.get("nombre_de_partants")
            allocation = race.get("allocation")
            terrain = race.get("terrain")
            enjeux_sg = race.get("enjeux_sg")

            # Extraction des données météo
            meteo = race.get("meteo", {})
            temperature = meteo.get("temperature")
            ciel = meteo.get("ciel")
            vent_vitesse = meteo.get("vent_vitesse")
            vent_direction = meteo.get("vent_direction")

            # Vérifier que les champs critiques ne sont pas nuls
            if (hippodrome is None or style is None or discipline is None or
                nombre_de_partants is None or allocation is None or terrain is None or
                enjeux_sg is None or
                temperature is None or ciel is None or vent_vitesse is None or vent_direction is None):
                # On ignore cette ligne si l'un des champs critiques est null
                continue

            # Insertion de la course avec INSERT OR IGNORE pour éviter les doublons (clé UNIQUE)
            query = '''
                INSERT OR IGNORE INTO races (
                    date, reunion, course, prix, hippodrome, style, discipline,
                    nombre_de_partants, allocation, terrain, temperature, ciel, vent_vitesse, vent_direction, enjeux_sg
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (
                date, reunion, course, prix, hippodrome, style, discipline,
                nombre_de_partants, allocation, terrain, temperature, ciel, vent_vitesse, vent_direction, enjeux_sg
            ))

        # Validation de la transaction
        conn.commit()
        print("Les courses ont été insérées avec succès dans la table 'races'.")
    except sqlite3.Error as e:
        print("Erreur SQLite :", e)
    except Exception as e:
        print("Erreur :", e)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    db_file = "courses.db"
    json_file = "condition_course.json"
    fill_races(db_file, json_file)
