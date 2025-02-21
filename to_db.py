#!/usr/bin/env python3
import sqlite3

def create_tables(db_file):
    """Crée la base de données et les tables si elles n'existent pas."""
    try:
        # Connexion à la base de données (le fichier sera créé s'il n'existe pas)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Création de la table 'races'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS races (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                reunion TEXT NOT NULL,
                course TEXT NOT NULL,
                prix TEXT,
                hippodrome TEXT,
                style TEXT,
                discipline TEXT,
                nombre_de_partants INTEGER,
                allocation INTEGER,
                terrain TEXT,
                temperature INTEGER,
                ciel TEXT,
                vent_vitesse INTEGER,
                vent_direction TEXT,
                enjeux_sg INTEGER,
                UNIQUE(date, reunion, course)
            );
        ''')

        # Création de la table 'results'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_id INTEGER NOT NULL,
                classement INTEGER,
                numero TEXT,
                cheval TEXT,
                jockey TEXT,
                entraineur TEXT,
                corde TEXT,
                poids REAL,
                ecarts TEXT,
                FOREIGN KEY(race_id) REFERENCES races(id) ON DELETE CASCADE
            );
        ''')

        # Création de la table 'tracking'
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_id INTEGER NOT NULL,
                discipline TEXT,
                numero TEXT,
                nom TEXT,
                classement INTEGER,
                vitessemax_kmh REAL,
                temps_officiel TEXT,
                derniers600m TEXT,
                derniers200m TEXT,
                derniers100m TEXT,
                distance_reelle REAL,
                distance_vainqueur REAL,
                FOREIGN KEY(race_id) REFERENCES races(id) ON DELETE CASCADE
            );
        ''')

        # Création des index pour optimiser les jointures et les recherches
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_races_date_reunion_course ON races(date, reunion, course);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_results_race_id ON results(race_id);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tracking_race_id ON tracking(race_id);
        ''')

        # Valider les modifications et fermer la connexion
        conn.commit()
        print("Les tables ont été créées avec succès.")
    except sqlite3.Error as e:
        print(f"Une erreur s'est produite lors de la création des tables : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Spécifiez le nom du fichier de base de données SQLite
    db_file = 'courses.db'
    create_tables(db_file)
