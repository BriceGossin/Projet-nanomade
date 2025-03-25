import os
import numpy as np
import pandas as pd
import joblib


# 📌 Paramètres
input_base_folder = "C:\\Users\\brice\\OneDrive\\Documents\\5A GPSE\\Projet nanomade\\Code alternatif\\Nettoyage csv"
seq_length = 10  # Nombre de timestamps dans une séquence

# 🔄 Parcourir chaque dossier de lettre (ex: A, B, C)
X_data, Y_data = [], []
letters = sorted(os.listdir(input_base_folder))  # Ex: ["A", "B", "C"]

for letter_index, letter_folder in enumerate(letters):
    letter_path = os.path.join(input_base_folder, letter_folder)
    
    if not os.path.isdir(letter_path):
        continue  # Ignore les fichiers, on ne garde que les dossiers

    print(f"📂 Traitement du dossier {letter_folder}...")

    # Parcourir tous les fichiers CSV du dossier
    csv_files = [f for f in os.listdir(letter_path) if f.lower().endswith(".csv")]  # 🔹 Vérifie l'extension en minuscule
    
    for file in csv_files:
        file_path = os.path.join(letter_path, file)
        
        # 🔍 Vérifier si le fichier est bien un CSV et n'est pas vide
        if not file.lower().endswith(".csv"):
            print(f"⚠️ Fichier ignoré (pas un CSV) : {file_path}")
            continue
        
        if os.path.getsize(file_path) == 0:
            print(f"⚠️ Fichier vide ignoré : {file_path}")
            continue
        
        try:
            # Charger les données
            df = pd.read_csv(file_path)
            
            # Vérifier si le fichier est bien formaté (éviter les fichiers corrompus)
            if df.shape[1] == 0:
                print(f"⚠️ Fichier corrompu ignoré : {file_path}")
                continue
            
            data = df.to_numpy()

            # Vérifier si le fichier contient assez de données
            if len(data) > seq_length:
                for i in range(len(data) - seq_length):
                    X_data.append(data[i:i+seq_length])   # Séquence de 10 timestamps
                    Y_data.append(letter_index)  # Classe associée (0=A, 1=B, 2=C...)

        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier {file_path} : {e}")

# Convertir en tableaux NumPy
X_data = np.array(X_data)
Y_data = np.array(Y_data)

# Sauvegarde des fichiers pour le LSTM
output_folder = input_base_folder  # On enregistre dans le même dossier que les données traitées
np.save(os.path.join(output_folder, "X_train.npy"), X_data)
np.save(os.path.join(output_folder, "Y_train.npy"), Y_data)

joblib.dump(letters, os.path.join(output_folder, "lettres.pkl"))

print(f"✅ Séquences générées et enregistrées : {X_data.shape} pour X, {Y_data.shape} pour Y")
