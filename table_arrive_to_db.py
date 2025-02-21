#!/usr/bin/env python3
import sqlite3
import json
import re

# Charger les données JSON
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Nettoyer et convertir classement en int
def clean_classement(classement):
    if not classement:
        return None
    match = re.search(r'\d+', str(classement))
    return int(match.group()) if match else None

# Nettoyer et convertir poids en float
def clean_poids(poids):
    if not poids:
        return None
    try:
        # Remplacer la virgule par un point si nécessaire
        return float(poids.replace(',', '.'))
    except ValueError:
        return None

def insert_data(conn, data):
    """
    Pour chaque course dans le JSON, recherche la course correspondante dans la table 'races'
    à l'aide des champs date, reunion et course, et insère les résultats dans la table 'results'
    uniquement si les champs requis (numero, cheval, jockey, entraineur, corde, poids, classement) sont renseignés.
    """
    cursor = conn.cursor()
    
    for course in data:
        date = course.get('date')
        reunion = course.get('reunion')
        course_num = course.get('course')
        
        if not (date and reunion and course_num):
            print("Informations manquantes pour identifier la course, enregistrement ignoré.")
            continue

        # Recherche du race_id dans la table races
        cursor.execute("""
            SELECT id FROM races WHERE date = ? AND reunion = ? AND course = ?
        """, (date, reunion, course_num))
        race = cursor.fetchone()
        
        if race is None:
            print(f"Course non trouvée pour : date={date}, reunion={reunion}, course={course_num}")
            continue
        
        race_id = race[0]
        
        # Parcourir les résultats de la course
        for result in course.get('result', []):
            classement = clean_classement(result.get('classement'))
            numero = result.get('numero')
            cheval = result.get('cheval')
            jockey = result.get('jockey')
            entraineur = result.get('entraineur')
            corde = result.get('corde')
            poids = clean_poids(result.get('poids'))
            ecarts = result.get('ecarts')
            
            # Vérifier que les champs requis ne sont pas vides
            if not (numero and cheval and corde and (poids is not None) and (classement is not None)):
                print("Champ(s) requis manquant(s) dans le résultat, enregistrement ignoré.")
                continue

            cursor.execute("""
                INSERT INTO results (
                    race_id, classement, numero, cheval, jockey, entraineur, corde, poids, ecarts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race_id, classement, numero, cheval, jockey, entraineur, corde, poids, ecarts
            ))
    
    conn.commit()

if __name__ == "__main__":
    json_file = "table_arrive.json"  # Chemin vers votre fichier JSON contenant les résultats
    db_name = "courses.db"  # Nom de votre base de données SQLite
    
    data = load_json(json_file)
    
    # Connexion à la base de données (les tables 'races' et 'results' doivent déjà exister)
    conn = sqlite3.connect(db_name)
    
    insert_data(conn, data)
    conn.close()
    print("Données insérées avec succès dans la table 'results' de la base de données!")
