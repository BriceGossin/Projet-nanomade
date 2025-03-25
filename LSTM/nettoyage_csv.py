import pandas as pd
import os

# Définir les chemins des dossiers
input_folder = ""
output_folder = ""

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(output_folder, exist_ok=True)

# Lister tous les fichiers CSV du dossier d'entrée
csv_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

# Boucle sur chaque fichier CSV
for file in csv_files:
    file_path = os.path.join(input_folder, file)

    # Charger le fichier CSV
    df = pd.read_csv(file_path)

    # Convertir en numérique et supprimer les lignes non valides
    df_cleaned = df.apply(pd.to_numeric, errors='coerce')
    df_cleaned = df_cleaned.dropna(how='all', axis=1)
    df_cleaned = df_cleaned.dropna(how='any')

    # Supprimer la colonne Timestamp si elle existe
    if 'Timestamp' in df_cleaned.columns:
        df_cleaned = df_cleaned.drop(columns=['Timestamp'])

    # Étape 1 : Identifier les colonnes actives en utilisant la ligne de calibration
    colonnes_a_garder = []
    for col in df_cleaned.columns:
        premiere_valeur = df_cleaned[col].iloc[0]  # Prendre la valeur de calibration
        if premiere_valeur != 1000 and any(df_cleaned[col] != 3299):  # Capteur actif
            colonnes_a_garder.append(col)

    # Garder uniquement les colonnes actives
    df_filtered = df_cleaned[colonnes_a_garder]

    # Étape 2 : Ne garder que les 8 premières colonnes après le filtrage
    df_filtered = df_filtered.iloc[:, :8]  # Sélectionne uniquement les 8 premières colonnes

    # Étape 3 : Exclure les valeurs 3299, 1000 et 0 pour la normalisation
    valid_values = df_filtered[(df_filtered != 3299) & (df_filtered != 1000) & (df_filtered != 0)]
    global_max_valid = valid_values.max().max()

    # Appliquer la normalisation avec ce max
    df_global_normalized_corrected = df_filtered / global_max_valid

    # Définir le chemin du fichier de sortie
    output_path = os.path.join(output_folder, file)

    # Sauvegarde du fichier normalisé
    df_global_normalized_corrected.to_csv(output_path, index=False)

    print(f"✅ {file} traité et enregistré sous : {output_path}")

print("🚀 Tous les fichiers ont été traités avec succès !")
