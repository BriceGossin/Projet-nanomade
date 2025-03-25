import numpy as np
import pandas as pd
import os
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
import joblib
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

# 📂 Dossiers à adapter
train_folder = "Lettres"
SEQ_LENGTH = 50
NB_FEATURES = 8
BATCH_SIZE = 256
EPOCHS = 100

# 🔤 Mapping classes → lettres
lettres = sorted(os.listdir(train_folder))
classe_to_lettre = {i: lettre for i, lettre in enumerate(lettres)}
lettre_to_classe = {lettre: i for i, lettre in classe_to_lettre.items()}
joblib.dump(classe_to_lettre, "lettres.pkl")
#print("✅ Mapping classe → lettre :", classe_to_lettre)

# 🔄 Charger et séquencer les données
def charger_donnees(folder):
    X_data, Y_data = [], []
    for lettre in lettres:
        dossier_lettre = os.path.join(folder, lettre)
        for fichier in os.listdir(dossier_lettre):
            if fichier.endswith(".csv"):
                path = os.path.join(dossier_lettre, fichier)
                df = pd.read_csv(path, header=0).dropna(how='all')
                data = df.to_numpy()

                # Séquences glissantes
                if len(data) >= SEQ_LENGTH:
                    for i in range(len(data) - SEQ_LENGTH + 1):
                        seq = data[i:i+SEQ_LENGTH]
                        if seq.shape == (SEQ_LENGTH, NB_FEATURES):
                            X_data.append(seq)
                            Y_data.append(lettre_to_classe[lettre])
    return np.array(X_data, dtype=np.float32), np.array(Y_data, dtype=np.int32)


# 📊 Export Excel
def exporter_resultats_excel(history):
    df = pd.DataFrame(history)
    df.to_excel("historique_entrainement.xlsx", index=False)
    print("📈 Historique exporté → historique_entrainement.xlsx")

# 🧠 Entraînement modèle
def entrainer_modele():
    print("🔄 Chargement des données...")
    X, Y = charger_donnees(train_folder)
    Y_cat = to_categorical(Y, num_classes=len(classe_to_lettre))
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y_cat, test_size=0.2, random_state=42)

    model = Sequential([
        Input(shape=(SEQ_LENGTH, NB_FEATURES)),
        LSTM(64, activation='tanh'),
        Dropout(0.3),
        Dense(len(classe_to_lettre), activation='softmax')
    ])
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)
    ]

    print("🚀 Entraînement...")
    history = model.fit(
        X_train, Y_train,
        validation_data=(X_test, Y_test),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks
    )
    model.save("model_lstm.keras")
    print("✅ Modèle sauvegardé → model_lstm.keras")
    exporter_resultats_excel(history.history)
    afficher_message("✅ Entraînement terminé et modèle sauvegardé.")


# 📊 Export prédictions Excel (avec virgules, forcées en texte)
def exporter_prediction_excel(fichier_csv, moyenne, lettre_pred):
    excel_path = "resultats_predictions.xlsx"
    
    try:
        df_exist = pd.read_excel(excel_path, dtype=str)
    except FileNotFoundError:
        df_exist = pd.DataFrame()

    # Créer ligne avec moyennes converties en chaînes avec virgule
    nouvelle_ligne = {"Fichier": os.path.basename(fichier_csv)}
    for i, val in enumerate(moyenne):
        val_str = f"{val:.4f}".replace('.', ',')  # Forcer la virgule
        nouvelle_ligne[f"Classe_{i}"] = val_str  # Stocker en str
    nouvelle_ligne["Lettre_predite"] = lettre_pred

    # Ajouter à l'existant
    df_nouveau = pd.DataFrame([nouvelle_ligne])
    df_final = pd.concat([df_exist, df_nouveau], ignore_index=True)

    # Forcer tout en texte pour garder les virgules
    for col in df_final.columns:
        df_final[col] = df_final[col].astype(str)

    # Exporter sans convertir les nombres
    df_final.to_excel(excel_path, index=False)
    print(f"📥 Résultat avec virgules → {excel_path}")



# 🔮 Prédiction CSV (filtrage confiance > 90%)
def predire_csv(csv_path):
    modele = load_model("model_lstm.keras")
    classe_to_lettre = joblib.load("lettres.pkl")

    df = pd.read_csv(csv_path, header=0).dropna(how='all')
    data = df.to_numpy()

    # Padding si nécessaire
    if data.shape[0] < SEQ_LENGTH:
        pad = np.zeros((SEQ_LENGTH - data.shape[0], NB_FEATURES))
        data = np.vstack([data, pad])

    # Génération des séquences
    sequences = [data[i:i+SEQ_LENGTH] for i in range(len(data) - SEQ_LENGTH + 1)]
    if not sequences:
        sequences = [data[:SEQ_LENGTH]]
    sequences = np.array(sequences).astype(np.float32)

    # Prédiction pour chaque séquence
    predictions = modele.predict(sequences)

    # 🔍 Filtrage : garder uniquement les séquences avec une confiance > 90%
    predictions_filtrees = []
    for pred in predictions:
        confiance_max = np.max(pred)
        if confiance_max >= 0.98:
            predictions_filtrees.append(pred)

    if predictions_filtrees:
        moyenne = np.mean(predictions_filtrees, axis=0)
        classe_pred = np.argmax(moyenne)
        lettre_pred = classe_to_lettre.get(classe_pred, f"Inconnue ({classe_pred})")
    else:
        print("⚠️ Aucune séquence avec confiance > 90% détectée.")
        moyenne = np.zeros(len(classe_to_lettre))
        lettre_pred = "Inconnue"

    print(f"🔍 Lettre prédite : {lettre_pred}")
    afficher_message(f"🔮 Lettre prédite : {lettre_pred}")

    # ✅ Export vers Excel (moyenne des confiantes)
    exporter_prediction_excel(csv_path, moyenne, lettre_pred)
    return lettre_pred




# 🪟 Interface Qt – Message
def afficher_message(message):
    app = QApplication.instance() or QApplication([])
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle("Information")
    msg.exec_()

# 📂 Interface Qt – Sélection fichier
def choisir_fichier():
    app = QApplication.instance() or QApplication([])
    fichier, _ = QFileDialog.getOpenFileName(None, "Choisir un fichier CSV", "", "CSV Files (*.csv)")
    return fichier

# 📜 Menu principal
def menu():
    while True:
        print("\n🧭 Menu :")
        print("1. Entraîner le modèle")
        print("2. Prédire une lettre à partir d’un CSV")
        print("3. Quitter")
        choix = input("👉 Choisissez une option : ")

        if choix == '1':
            entrainer_modele()
        elif choix == '2':
            if not os.path.exists("model_lstm.keras"):
                print("⚠️ Modèle introuvable. Lancement de l'entraînement.")
                entrainer_modele()
            fichier = choisir_fichier()
            if fichier:
                predire_csv(fichier)
            else:
                print("❌ Aucun fichier sélectionné.")
        elif choix == '3':
            print("👋 À bientôt !")
            break
        else:
            print("❌ Option invalide.")

# ▶️ Lancement
if __name__ == "__main__":
    menu()
