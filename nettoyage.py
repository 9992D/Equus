import sqlite3

def print_logo():
    logo = """
     ____                       _           
    / ___| ___   ___   ___  ___| |_ ___  _ __ 
   | |  _ / _ \ / _ \ / _ \/ __| __/ _ \| '__|
   | |_| | (_) | (_) |  __/\__ \ || (_) | |   
    \____|\___/ \___/ \___||___/\__\___/|_|   
    """
    print(logo)
    print("=== Nettoyage des courses orphelines en cours... ===\n")

def clean_condition_courses(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM condition_courses
        WHERE NOT EXISTS (
            SELECT 1 FROM courses
            WHERE courses.date = condition_courses.date
            AND courses.reunion = condition_courses.reunion
            AND courses.course = condition_courses.course
        )
    ''')

    conn.commit()
    conn.close()
    print("\n✅ Nettoyage terminé : suppression des courses inexistantes.")

    import sqlite3

def delete_invalid_tracking_rows(db_name="courses.db"):
    """Supprime les lignes de tracking dont (date, reunion, course) ne figurent pas dans la table courses."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Requête SQL pour supprimer les lignes de tracking non correspondantes
    cursor.execute("""
    DELETE FROM tracking
    WHERE (date, reunion, course) NOT IN (
        SELECT date, reunion, course FROM courses
    )
    """)

    # Affichage du nombre de lignes supprimées
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"{rows_deleted} lignes supprimées de la table tracking.")


# Exemple d'utilisation
if __name__ == "__main__":
    print_logo()
    db_name = "courses.db"  # Remplace par le nom de ta base
    delete_invalid_tracking_rows(db_name)
