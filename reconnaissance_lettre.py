import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.utils import to_categorical
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from PyQt5.QtWidgets import QApplication, QFileDialog

def choisir_fichier():
    app = QApplication([])
    fichier, _ = QFileDialog.getOpenFileName(None, "Choisir un fichier CSV", "", "CSV Files (*.csv)")
    return fichier

# Fonction de traitement des CSV
def traiter_csv(chemin_fichier):
    df = pd.read_csv(chemin_fichier, header=None, dtype=str)
    df = df.dropna(how="all")  # Suppression des lignes vides
    df = df.apply(pd.to_numeric, errors='coerce')  # Conversion en valeurs numériques
    vecteur = df.to_numpy().flatten()
    vecteur = np.nan_to_num(vecteur, nan=0.0)  # Remplacement des NaN par 0
    return vecteur

# Chargement des données
def charger_donnees(repertoire):
    X, y = [], []
    for dossier_lettre in os.listdir(repertoire):
        chemin_dossier = os.path.join(repertoire, dossier_lettre)
        if os.path.isdir(chemin_dossier):
            for fichier in os.listdir(chemin_dossier):
                if fichier.endswith('.csv'):
                    chemin_fichier = os.path.join(chemin_dossier, fichier)
                    vecteur = traiter_csv(chemin_fichier)
                    X.append(vecteur)
                    y.append(dossier_lettre)
    if not X:
        raise ValueError("Aucune donnée valide trouvée dans le dossier.")
    taille_max = max(len(vecteur) for vecteur in X)
    print(f"Taille maximale détectée : {taille_max}")
    X = [np.pad(vecteur, (0, taille_max - len(vecteur)), mode='constant') for vecteur in X]
    joblib.dump(taille_max, 'taille_max.pkl')
    return np.array(X, dtype=np.float32), np.array(y)

# Entraînement du modèle ANN
def entrainer_modele():
    X, y = charger_donnees("Lettres")
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    y = to_categorical(y)
    joblib.dump(label_encoder, 'label_encoder.pkl')
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    joblib.dump(scaler, 'scaler.pkl')
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    modele = Sequential([
        Input(shape=(X_train.shape[1],)),  # Utilisation de l'objet Input pour la première couche
        Dense(128, activation='relu'),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dropout(0.3),
        Dense(y_train.shape[1], activation='softmax')
    ])
    
    modele.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    
    # Surveillance de l'accuracy dans EarlyStopping
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    
    modele.fit(
        X_train, y_train,
        epochs=50,
        batch_size=16,
        validation_data=(X_test, y_test),
        callbacks=[early_stopping]
    )
    
    loss, acc = modele.evaluate(X_test, y_test)
    print(f"Précision du modèle : {acc*100:.2f}%")
    
    modele.save('modele_lettres.keras')
    print("Modèle ANN entraîné et sauvegardé avec succès !")

# Prédiction d'une lettre
def predire_lettre():
    fichier_csv = choisir_fichier()
    if not fichier_csv:
        print("Aucun fichier sélectionné.")
        return
    vecteur = traiter_csv(fichier_csv)
    taille_max = joblib.load('taille_max.pkl')
    vecteur = np.pad(vecteur, (0, max(0, taille_max - len(vecteur))), mode='constant')
    modele = load_model('modele_lettres.keras')
    scaler = joblib.load('scaler.pkl')
    label_encoder = joblib.load('label_encoder.pkl')
    vecteur_normalise = scaler.transform([vecteur])
    prediction = modele.predict(vecteur_normalise)
    classe_predite = np.argmax(prediction)
    lettre_predite = label_encoder.inverse_transform([classe_predite])[0]
    print(f"Lettre prédite : {lettre_predite}")

# Menu principal
def menu_principal():
    while True:
        print("\n1. Entraîner le modèle")
        print("2. Prédire une lettre avec un nouveau CSV")
        print("3. Quitter")
        choix = input("Choisissez une option : ")
        if choix == '1':
            entrainer_modele()
        elif choix == '2':
            predire_lettre()
        elif choix == '3':
            print("Au revoir !")
            break
        else:
            print("Choix invalide, réessayez.")

# Exécution du script
if __name__ == "__main__":
    menu_principal()
