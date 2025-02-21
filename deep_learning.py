import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lightgbm import LGBMRanker
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_curve, auc

# --- 1. Chargement et préparation des données ---
df = pd.read_csv("/content/Donn_es_Nettoy_es.csv")

# Convertir la date en datetime
df['date'] = pd.to_datetime(df['date'])

# Créer la cible binaire : 1 si le cheval a gagné (classement == 1), 0 sinon
df['is_winner'] = (df['classement'] == 1).astype(int)

# --- 2. Création de nouvelles features ---
df['ratio_poids_partants'] = df['poids'] / df['nombre_de_partants']
df['allocation_par_partant'] = df['allocation'] / df['nombre_de_partants']
df['ratio_podium_races'] = df['horse_podium_rate'] / (df['horse_races'] + 1)  # évite division par 0
df['vitesse_par_partant'] = df['horse_avg_vmax'] / df['nombre_de_partants']

# --- 3. Sélection des features ---
numeric_features = [
    'nombre_de_partants', 'allocation', 'temperature', 'vent_vitesse', 'poids',
    'horse_avg_classement', 'horse_std_classement', 'horse_races',
    'horse_podium_rate', 'horse_avg_vmax', 'day_of_week', 'month', 'year',
    'ratio_poids_partants', 'allocation_par_partant', 'ratio_podium_races', 'vitesse_par_partant'
]
categorical_features = [
    'hippodrome', 'style', 'race_discipline', 'terrain', 'ciel', 'vent_direction'
]

group_col = 'race_id'
target = 'is_winner'

X = df[numeric_features + categorical_features]
y = df[target]
groups = df[group_col]

# --- 4. Prétraitement : standardisation et encodage ---
numeric_transformer = Pipeline(steps=[
    ('scaler', StandardScaler())
])
categorical_transformer = Pipeline(steps=[
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ]
)

X_preprocessed = preprocessor.fit_transform(X)

# --- 5. Split par course (GroupShuffleSplit) ---
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X_preprocessed, y, groups=groups))

X_train, X_test = X_preprocessed[train_idx], X_preprocessed[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
groups_train, groups_test = groups.iloc[train_idx], groups.iloc[test_idx]

# --- 6. Entraînement du modèle de Ranking ---
# Utilisation de LGBMRanker avec l'objectif 'lambdarank'
ranker = LGBMRanker(
    objective='lambdarank',
    metric='ndcg',
    boosting_type='gbdt',
    learning_rate=0.001,
    num_leaves=50,
    n_estimators=10000,
    random_state=42
)

# Pour le ranking, il faut spécifier la taille de chaque groupe (chaque course)
train_group = groups_train.value_counts().sort_index().values
test_group = groups_test.value_counts().sort_index().values

ranker.fit(
    X_train, y_train,
    group=train_group,
    eval_set=[(X_test, y_test)],
    eval_group=[test_group],
)

# --- 7. Évaluation par course ---
# Prédire la probabilité d'être gagnant sur le set test
y_pred_proba = ranker.predict(X_test)

# Reconstruction d'un DataFrame d'évaluation incluant le groupement
test_df = pd.DataFrame({
    'race_id': groups_test.values,
    'y_true': y_test.values,
    'pred_proba': y_pred_proba
})

# Fonction pour vérifier si le cheval avec la plus forte probabilité est bien le vrai gagnant
def check_correct_winner(group):
    idx_max = group['pred_proba'].idxmax()
    return 1 if group.loc[idx_max, 'y_true'] == 1 else 0

winner_accuracy = test_df.groupby('race_id', group_keys=False).apply(check_correct_winner).mean()
print(f"Taux de réussite pour prédire le vainqueur (top-1) par course : {winner_accuracy:.3f}")

# --- 8. Analyse des erreurs : Calcul et visualisation de l'écart (gap) ---
def compute_error_gap(group):
    # Probabilité prédite pour le cheval sélectionné
    idx_max = group['pred_proba'].idxmax()
    pred_top = group.loc[idx_max, 'pred_proba']
    # Probabilité prédite pour le vrai gagnant (il doit y avoir une seule ligne avec y_true==1)
    true_winner = group[group['y_true'] == 1]
    if not true_winner.empty:
        true_prob = true_winner['pred_proba'].values[0]
    else:
        true_prob = np.nan
    return pred_top - true_prob

# Calculer l'écart pour chaque course
error_gaps = test_df.groupby('race_id').apply(compute_error_gap)

# Filtrer uniquement les courses mal évaluées (écart > 0 signifie que le modèle a préféré un autre cheval)
misclassified_gaps = error_gaps[error_gaps > 0]

plt.figure(figsize=(10, 6))
sns.histplot(misclassified_gaps, bins=30, kde=True, color="orange")
plt.xlabel("Écart de prédiction (Gap)")
plt.ylabel("Nombre de courses")
plt.title("Distribution de l'écart de prédiction pour les courses mal évaluées")
plt.show()

# --- 9. Autres visualisations ---

# Histogramme des probabilités prédites pour les gagnants et non-gagnants
plt.figure(figsize=(12, 5))
sns.histplot(test_df[test_df['y_true'] == 1]['pred_proba'], label="Gagnants", color="green", bins=50, kde=True)
sns.histplot(test_df[test_df['y_true'] == 0]['pred_proba'], label="Non-gagnants", color="red", bins=50, kde=True)
plt.xlabel("Probabilité prédite")
plt.ylabel("Nombre de chevaux")
plt.legend()
plt.title("Distribution des probabilités prédites")
plt.show()

# Courbe ROC
fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
roc_auc = auc(fpr, tpr)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='grey', linestyle='--')
plt.xlabel('Taux de faux positifs')
plt.ylabel('Taux de vrais positifs')
plt.title('Courbe ROC')
plt.legend(loc="lower right")
plt.show()

# Comparaison sous forme de barplot : Pourcentage de courses correctement vs. mal prédites
correct_preds = test_df.groupby('race_id', group_keys=False).apply(check_correct_winner)
plt.figure(figsize=(6, 4))
sns.barplot(x=['Mauvaises Prédictions', 'Bonnes Prédictions'],
            y=[(1 - correct_preds.mean()), correct_preds.mean()],
            palette="Blues_d")
plt.ylabel("Proportion")
plt.title("Précision de la prédiction du vainqueur par course")
plt.show()
