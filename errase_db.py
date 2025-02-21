import sqlite3

def delete_all_tables(db_path):
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Récupérer la liste des tables (sauf sqlite_sequence)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
        tables = cursor.fetchall()
        
        # Supprimer chaque table
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            print(f"Table {table_name} supprimée.")
        
        # Valider les modifications
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erreur lors de la suppression des tables : {e}")
    finally:
        # Fermer la connexion
        conn.close()

# Exemple d'utilisation
db_path = "courses.db"
delete_all_tables(db_path)

