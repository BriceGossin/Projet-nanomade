import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.utils import to_categorical
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

# 📂 Définition du dossier contenant les données
DATASET_PATH = "Lettres/"
letters = sorted([d for d in os.listdir(DATASET_PATH) if os.path.isdir(os.path.join(DATASET_PATH, d))])

# 🔹 Paramètres
SEQUENCE_LENGTH = 50  # Nombre de lignes par séquence
FEATURES = 32  # Nombre total de colonnes utilisées (M_F_1 à U_C_8)

X, Y = [], []
scaler = StandardScaler()

# 🔍 Fonction de chargement et nettoyage des données
def load_clean_data(file_path):
    try:
        df = pd.read_csv(file_path, header=0)
        df = df.iloc[:, 1:]  # Supprimer la colonne Timestamp
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        
        if len(df) >= SEQUENCE_LENGTH:
            df = df.iloc[:SEQUENCE_LENGTH]
        else:
            padding = np.zeros((SEQUENCE_LENGTH - len(df), FEATURES))
            df = np.vstack([df.values, padding])
        
        return df
    except Exception as e:
        print(f"Erreur lors du chargement de {file_path} : {e}")
        return None

# 🔄 Chargement des données
def load_dataset():
    for label, letter in enumerate(letters):
        letter_path = os.path.join(DATASET_PATH, letter)
        for file in os.listdir(letter_path):
            if not file.endswith(".csv"):  # Ignore les fichiers non CSV
                continue
            file_path = os.path.join(letter_path, file)
            cleaned_data = load_clean_data(file_path)
            if cleaned_data is not None:
                X.append(cleaned_data)
                Y.append(label)

load_dataset()

# Conversion en numpy arrays
X = np.array(X).astype(np.float32)
Y = to_categorical(Y, num_classes=len(letters))
X = scaler.fit_transform(X.reshape(-1, FEATURES)).reshape(-1, SEQUENCE_LENGTH, FEATURES)

print("✅ Données chargées et prétraitées !")

# 🔥 Définition du modèle LSTM
model = Sequential([
    LSTM(64, activation='tanh', return_sequences=True, input_shape=(SEQUENCE_LENGTH, FEATURES)),
    Dropout(0.2),
    LSTM(32, activation='tanh'),
    Dropout(0.2),
    Dense(len(letters), activation='softmax')
])

# ⚙️ Compilation du modèle
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# 🏋️ Entraînement du modèle
model.fit(X, Y, epochs=20, batch_size=16, validation_split=0.2)

# Sauvegarde du modèle
model.save("lstm_letter_recognition.h5")
print("✅ Modèle entraîné et sauvegardé !")

# Charger le modèle entraîné
model = tf.keras.models.load_model("lstm_letter_recognition.h5")

def predict_letter(file_path):
    data = load_clean_data(file_path)
    if data is None:
        return "Données invalides !"
    # Convertir en numpy array avant reshape
    data = data.to_numpy()  # Convertit le DataFrame en numpy.ndarray
    data = scaler.transform(data.reshape(-1, FEATURES)).reshape(-1, SEQUENCE_LENGTH, FEATURES)

    data = np.array(data).reshape(-1, SEQUENCE_LENGTH, FEATURES)  # Assurez-vous que SEQUENCE_LENGTH et FEATURES sont bien définis
    prediction = model.predict(data)

    predicted_letter = letters[np.argmax(prediction)]
    return f"🔠 Lettre prédite : {predicted_letter}"

# 🖥️ Interface graphique Qt
app = QApplication([])
def open_file_dialog():
    file_path, _ = QFileDialog.getOpenFileName(None, "Sélectionner un fichier CSV", "", "CSV Files (*.csv)")
    if file_path:
        prediction = predict_letter(file_path)
        QMessageBox.information(None, "Résultat de la prédiction", prediction)

open_file_dialog()
app.exec()