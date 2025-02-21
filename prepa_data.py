#!/usr/bin/env python3
import sqlite3
import pandas as pd
import numpy as np

def load_merged_data(db_name):
    """
    Charge les données en joignant les 3 tables (races, results, tracking).
    On sélectionne uniquement les colonnes utiles pour un modèle de prédiction.
    """
    conn = sqlite3.connect(db_name)
    query = """
    SELECT
        r.id AS race_id,
        r.date,
        r.hippodrome,
        r.style,
        r.discipline AS race_discipline,
        r.nombre_de_partants,
        r.allocation,
        r.terrain,
        r.temperature,
        r.ciel,
        r.vent_vitesse,
        r.vent_direction,

        res.classement,
        res.numero,
        res.cheval,
        res.corde,
        res.poids,

        t.vitessemax_kmh,
        t.temps_officiel,
        t.derniers600m,
        t.derniers200m,
        t.derniers100m,
        t.distance_reelle,
        t.distance_vainqueur

    FROM races r
    INNER JOIN results res
        ON r.id = res.race_id
    LEFT JOIN tracking t
        ON r.id = t.race_id
        AND CAST(res.numero AS TEXT) = CAST(t.numero AS TEXT);
    """
    df = pd.read_sql_query(query, conn)
    df.to_csv("test2.csv", index=False)
    conn.close()
    return df

def clean_and_enrich_data(df):
    """
    1) Conversion de la date + création de features temporelles
    2) Conversion numérique des colonnes sélectionnées
    3) Suppression des lignes sans colonnes critiques
    4) Calcul d'agrégats historiques pour le cheval
    5) Imputation (remplacement de NaN) dans les colonnes agrégées
    """

    # ===================
    # A) Convertir la colonne date + extraire jour, mois, année
    # ===================
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])  # Supprime les lignes sans date

    df['day_of_week'] = df['date'].dt.dayofweek
    df['month']       = df['date'].dt.month
    df['year']        = df['date'].dt.year

    # ===================
    # B) Conversion en float/int pour les colonnes numériques
    # ===================
    numeric_cols = [
        'nombre_de_partants', 'allocation', 'temperature',
        'vent_vitesse', 'poids', 'classement',
        'vitessemax_kmh', 'temps_officiel',
        'derniers600m', 'derniers200m', 'derniers100m',
        'distance_reelle', 'distance_vainqueur'
    ]

    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)          # convertit en string
            .str.replace(' ', '') # retire espaces
        )
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # ===================
    # C) Supprimer lignes sans colonnes "critiques"
    # ===================
    critical_cols = [
        'hippodrome', 'style', 'race_discipline',
        'nombre_de_partants', 'allocation', 'terrain',
        'temperature', 'ciel', 'vent_vitesse', 'vent_direction',
        'cheval', 'classement'
    ]
    df = df.dropna(subset=critical_cols)

    # ===================
    # D) Calcul d'agrégats historiques pour le cheval
    # ===================
    df['horse_avg_classement'] = df.groupby('cheval')['classement'].transform('mean')
    df['horse_std_classement'] = df.groupby('cheval')['classement'].transform('std')
    df['horse_races'] = df.groupby('cheval')['classement'].transform('count')
    df['horse_podium_rate'] = df.groupby('cheval')['classement'].transform(lambda x: (x <= 3).mean())
    df['horse_avg_vmax'] = df.groupby('cheval')['vitessemax_kmh'].transform('mean')

    # ===================
    # E) Imputation : remplacer les NaN dans les agrégats
    # ===================

    # 1) Pour 'horse_races', on met 0 si NaN
    df['horse_races'] = df['horse_races'].fillna(0)

    # 2) Les autres, on choisit la médiane
    agg_cols = [
        'horse_avg_classement', 'horse_std_classement',
        'horse_podium_rate', 'horse_avg_vmax'
    ]
    for col in agg_cols:
        median_val = df[col].median()
        df[col] = df[col].fillna(median_val)

    # ===================
    # (Optionnel) Imputation pour autres colonnes
    # ===================
    # Exemple : On laisse tel quel ici, 
    # sinon on pourrait remplir la médiane / 0 :
    # for col in numeric_cols:
    #     med = df[col].median()
    #     df[col] = df[col].fillna(med)

    df = df.reset_index(drop=True)
    return df

def main():
    db_name = "courses.db"
    print("=== 1) Chargement et jointure (races + results + tracking) ===")
    df_raw = load_merged_data(db_name)
    print(f"Forme initiale : {df_raw.shape} (lignes, colonnes)")

    print("=== 2) Nettoyage, enrichissement, imputation ===")
    df_clean = clean_and_enrich_data(df_raw)
    print(f"Forme après nettoyage : {df_clean.shape}")

    # Sauvegarde du DataFrame final
    output_csv = "final_deeplearning_dataset_with_tracking.csv"
    df_clean.to_csv(output_csv, index=False)
    print(f"Fichier généré : {output_csv}")

    # Aperçu
    print(df_clean.head(100))

if __name__ == "__main__":
    main()
