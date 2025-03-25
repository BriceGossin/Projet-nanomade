import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from PyQt5.QtWidgets import QApplication, QFileDialog

def choisir_fichier():
    app = QApplication([])
    fichier, _ = QFileDialog.getOpenFileName(None, "Choisir un fichier CSV", "", "CSV Files (*.csv)")
    return fichier

def traiter_csv(chemin_fichier):
    df = pd.read_csv(chemin_fichier, header=None, dtype=str)
    df = df.dropna(how="all")
    df = df.apply(pd.to_numeric, errors='coerce')
    vecteur = df.to_numpy().flatten()
    vecteur = np.nan_to_num(vecteur, nan=0.0)
    return vecteur

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
    joblib.dump(taille_max, os.path.join(os.getcwd(), 'taille_max.pkl'))
    return np.array(X, dtype=np.float32), np.array(y)

# Fonction pour exporter l'historique d'entraînement vers Excel
def exporter_resultats_excel(historique):
    data = {
        'epoch': list(range(1, len(historique['loss']) + 1)),
        'accuracy': historique['accuracy'],
        'loss': historique['loss'],
        'val_accuracy': historique['val_accuracy'],
        'val_loss': historique['val_loss']
    }
    df = pd.DataFrame(data)

    # Conversion des flottants en chaînes avec virgules comme séparateurs décimaux
    df = df.applymap(lambda x: f"{x:.6f}".replace('.', ',') if isinstance(x, float) else x)

    df.to_excel('resultats_entrainement.xlsx', index=False)
    print("Résultats d'entraînement exportés vers 'resultats_entrainement.xlsx'")

def entrainer_modele():
    X, y = charger_donnees("Lettres")
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    y = to_categorical(y)
    joblib.dump(label_encoder, os.path.join(os.getcwd(), 'label_encoder.pkl'))
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    joblib.dump(scaler, os.path.join(os.getcwd(), 'scaler.pkl'))
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    modele = Sequential([
        Input(shape=(X_train.shape[1],)),
        Dense(256, activation='relu'),
        Dropout(0.2),
        Dense(128, activation='relu', kernel_regularizer=l2(0.001)),
        Dropout(0.2),
        Dense(64, activation='relu'),
        Dense(y_train.shape[1], activation='softmax')
    ])

    modele.compile(optimizer=Adam(learning_rate=0.0005), loss='categorical_crossentropy', metrics=['accuracy'])
    
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)
    
    history = modele.fit(
        X_train, y_train,
        epochs=50,
        batch_size=16,
        validation_data=(X_test, y_test),
        callbacks=[early_stopping, reduce_lr]
    )
    
    # Export des résultats
    exporter_resultats_excel(history.history)

    loss, acc = modele.evaluate(X_test, y_test)
    print(f"Précision du modèle : {acc*100:.2f}%")
    
    modele.save('modele_lettres.keras')
    print("Modèle ANN entraîné et sauvegardé avec succès !")


# Export prédictions Excel (avec virgules, forcées en texte)
def exporter_prediction_excel(fichier_csv, moyenne, lettre_pred):
    excel_path = "resultats_predictions.xlsx"
    
    try:
        df_exist = pd.read_excel(excel_path, dtype=str)
    except FileNotFoundError:
        df_exist = pd.DataFrame()

    # Créer ligne avec moyennes converties en chaînes avec virgule
    nouvelle_ligne = {"Fichier": os.path.basename(fichier_csv)}
    moyenne = moyenne.flatten()  # Pour éviter [[...]]
    for i, val in enumerate(moyenne):
        val_str = f"{val:.4f}".replace('.', ',')
        nouvelle_ligne[f"Classe_{i}"] = val_str
    nouvelle_ligne["Lettre_predite"] = lettre_pred

    df_nouveau = pd.DataFrame([nouvelle_ligne])
    df_final = pd.concat([df_exist, df_nouveau], ignore_index=True)

    for col in df_final.columns:
        df_final[col] = df_final[col].astype(str)

    df_final.to_excel(excel_path, index=False)
    print("Résultat sauvegardé sous Excel")

    
    
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
    print (f"Prédiction : {prediction}")
    
    classe_predite = np.argmax(prediction)
    lettre_predite = label_encoder.inverse_transform([classe_predite])[0]
    exporter_prediction_excel(fichier_csv, prediction, lettre_predite)
    print(f"Lettre prédite : {lettre_predite}")

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

if __name__ == "__main__":
    menu_principal()
