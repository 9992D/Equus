import sqlite3
import pandas as pd
import numpy as np

# Connexion à la base de données
conn = sqlite3.connect("courses.db")
cursor = conn.cursor()

# Exécution de la requête SELECT
cursor.execute("SELECT * FROM results LIMIT 100")

# Récupération des résultats
rows = cursor.fetchall()

# Récupération des noms des colonnes
columns = [description[0] for description in cursor.description]

# Conversion en DataFrame Pandas
df = pd.DataFrame(rows, columns=columns)

# Enregistrement des données dans un fichier CSV
df.to_csv("test.csv", index=False)

# Fermeture de la connexion
conn.close()
