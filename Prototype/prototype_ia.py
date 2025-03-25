import serial
import csv
import os
import datetime
import time
import threading
import pandas as pd
import numpy as np
import joblib
import sys
from tensorflow.keras.models import load_model
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from collections import deque
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
    QPushButton, QVBoxLayout, QWidget, QLabel
)
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interface Capteur - Graphe & Commande")

        # --- Variables ---
        self.ser = serial.Serial("COM9", baudrate=430000, timeout=1)
        self.i = 0
        self.lecture_continue_active = True
        self.running = True
        self.max_length = 250
        self.num_channels_to_plot = 8
        self.data_buffers = [deque([0.0] * self.max_length, maxlen=self.max_length) for _ in range(self.num_channels_to_plot)]
        self.time_buffer = deque([0.0] * self.max_length, maxlen=self.max_length)
        self.lock = threading.Lock()

        # --- Canvas Matplotlib intégré ---
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        self.init_graphe()

        # --- Bouton ---
        self.button = QPushButton("Start Acquisition")
        self.button.clicked.connect(self.start_command)

        # --- Labels de prédiction ---
        self.label_prediction = QLabel("Prédiction en attente...", self)
        self.label_prediction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_prediction.setStyleSheet("font-size: 16px; font-weight: bold; color: black; padding: 10px;")
        self.label_proba = QLabel("Prédiction en attente...", self)
        self.label_proba.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_proba.setStyleSheet("font-size: 16px; font-weight: bold; color: black; padding: 10px;")

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        layout.addWidget(self.label_prediction)  # Ajoute le label après le bouton
        layout.addWidget(self.label_proba)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --- Chargement IA ---
        self.modele = load_model('modele_lettres.keras')
        self.scaler = joblib.load('scaler.pkl')
        self.label_encoder = joblib.load('label_encoder.pkl')
        self.taille_max = joblib.load('taille_max.pkl')

        # --- Threads ---
        threading.Thread(target=self.lecture_continue, daemon=True).start()
        print("▶️ Lecture continue démarrée.")

        # --- Démarrer animation graphique ---
        self.ani = animation.FuncAnimation(self.fig, self.update_plot, interval=50, blit=False)
        self.canvas.draw()

        # --- Calibration initiale ---
        print("🔧 Calibration initiale...")
        self.send_calibration_commands_no_save()
        print("✅ Calibration OK.")


    # --- Graph Init ---
    def init_graphe(self):
        self.lines = []
        for i in range(self.num_channels_to_plot):
            line, = self.ax.plot([], [], label=f"M_F_{i+1}")
            self.lines.append(line)

        self.ax.set_ylim(1500, 2500)
        self.ax.set_xlim(0, 5)
        self.ax.set_title("Capteurs - Temps Réel")
        self.ax.set_xlabel("Temps (s)")
        self.ax.set_ylabel("Valeur")
        self.ax.legend(loc='upper right', ncol=2)

    def update_plot(self, frame):
        with self.lock:
            if len(self.time_buffer) < 2:
                return self.lines
            xdata = list(self.time_buffer)
            xmin = max(0, xdata[-1] - 5)
            xmax = xdata[-1] + 0.01
            self.ax.set_xlim(xmin, xmax)
            for i, line in enumerate(self.lines):
                ydata = list(self.data_buffers[i])
                line.set_data(xdata, ydata)
        self.canvas.draw()
        return self.lines

    # --- CSV/IA Methods ---
    def create_csv_file(self, directory):
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(directory, f"sensor_data_{timestamp}.csv")
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", *[f"{p}_{i}" for p in ["M_F", "U_F", "M_C", "U_C"] for i in range(1, 9)]])
        return filename

    def save_to_csv(self, filename, data):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            values = data.split()
            values += [""] * (32 - len(values))
            row = [timestamp] + values[:32]
            with open(filename, mode='a', newline='') as file:
                csv.writer(file).writerow(row)
        except Exception as e:
            print(f"⚠️ Erreur CSV : {e}")

    def traiter_csv(self, chemin_fichier):
        df = pd.read_csv(chemin_fichier, header=None, dtype=str)
        df = df.dropna(how="all").apply(pd.to_numeric, errors='coerce')
        vecteur = np.nan_to_num(df.to_numpy().flatten(), nan=0.0)
        return vecteur

    def afficher_message(self, message):
        self.label_prediction.setText(message)
        

    
    def predire_depuis_csv(self, fichier_csv):
        vecteur = self.traiter_csv(fichier_csv)
        vecteur = np.pad(vecteur, (0, max(0, self.taille_max - len(vecteur))), mode='constant')
        vecteur_normalise = self.scaler.transform([vecteur])
        prediction = self.modele.predict(vecteur_normalise)[0]  # Récupère directement le tableau 1D

        # Trouver la classe avec la probabilité maximale
        classe_predite = np.argmax(prediction)
        lettre_predite = self.label_encoder.inverse_transform([classe_predite])[0]

        # Afficher la lettre prédite
        self.afficher_message(f"🧠 Lettre prédite : {lettre_predite}")

        # Formater les probabilités
        proba_formatees = "\n".join([
            f"{self.label_encoder.inverse_transform([i])[0]} : {prob*100:.2f}%" 
            for i, prob in enumerate(prediction)
        ])

        # Mettre à jour le label avec un affichage propre
        self.label_proba.setText(f"🔢 **Probabilités :**\n{proba_formatees}")
        return lettre_predite

    # --- Communication Capteur ---
    def send_calibration_commands(self, filename):
        self.ser.reset_input_buffer()
        for command in ["K\n", "GD\n", "CC\n"]:
            print(f"➡️ Envoi commande : {command.strip()}")
            self.ser.write(command.encode())
            time.sleep(0.5)
            start_time = time.time()
            while time.time() - start_time < 1.5:
                try:
                    data = self.ser.readline().decode().strip()
                    if data:
                        print(f"💬 Calibration: {data}")
                        self.save_to_csv(filename, data)
                except Exception as e:
                    print(f"⚠️ Erreur lecture calibration : {e}")
                    break
        self.ser.write("R\n".encode())
        time.sleep(0.5)

    def send_calibration_commands_no_save(self):
        for command in ["K\n", "GD\n", "CC\n"]:
            self.ser.write(command.encode())
            time.sleep(0.1)
            try:
                data = self.ser.readline().decode().strip()
                if data:
                    print(f"💬 Calibration: {data}")
            except Exception as e:
                print(f"⚠️ Erreur lecture calibration: {e}")
        self.ser.write("R\n".encode())
        time.sleep(0.5)

    def discard_last_line(self):
        try:
            data = self.ser.readline().decode().strip()
            print(f"⚠️ Ignorée : {data}")
        except Exception as e:
            print(f"⚠️ Erreur lecture (ignorée) : {e}")

    def lecture_continue(self):
        compteur = 0
        while self.running:  # Utilise le flag pour s’arrêter proprement
            if self.lecture_continue_active:
                try:
                    data = self.ser.readline().decode().strip()
                    if data:
                        print(f"📡 {data}")
                        values = data.split()
                        if len(values) >= self.num_channels_to_plot:
                            try:
                                float_values = [float(v) for v in values[:self.num_channels_to_plot]]
                                with self.lock:
                                    current_time = time.time()
                                    for j in range(self.num_channels_to_plot):
                                        self.data_buffers[j].append(float_values[j])
                                    self.time_buffer.append(current_time)
                            except ValueError:
                                print(f"⚠️ Valeurs non valides : {values}")
                except Exception as e:
                    print(f"⚠️ Lecture continue : {e}")
            else:
                time.sleep(0.05)

            compteur += 1
            if compteur >= 100:
                print("🟢 Thread actif.")
                compteur = 0


    def read_from_sensor(self, filename, max_size_kb=38):
        try:
            while True:
                if os.path.exists(filename):
                    file_size_kb = os.path.getsize(filename) / 1024
                    if file_size_kb >= max_size_kb:
                        print(f"📁 Fichier atteint {file_size_kb:.2f} Ko. Arrêt acquisition.")
                        break
                data = self.ser.readline().decode().strip()
                if data:
                    self.save_to_csv(filename, data)
                    values = data.split()
                    with self.lock:
                        current_time = time.time()
                        try:
                            float_values = [float(v) for v in values[:self.num_channels_to_plot]]
                            for j in range(self.num_channels_to_plot):
                                self.data_buffers[j].append(float_values[j])
                            self.time_buffer.append(current_time)
                        except ValueError:
                            print(f"⚠️ Valeurs non valides : {values}")
        except Exception as e:
            print(f"⚠️ Erreur de lecture: {e}")
        finally:
            self.ser.write("S\n".encode())
            time.sleep(0.5)
            self.discard_last_line()

    def start_acquisition_sequence(self):
        print(f"\n🔴 Début acquisition (session {self.i})...")
        self.i += 1
        self.ser.write("S\n".encode())
        time.sleep(2)
        self.lecture_continue_active = False
        self.discard_last_line()
        self.ser.reset_input_buffer()

        csv_file = self.create_csv_file("enregistrements")
        self.send_calibration_commands(csv_file)
        self.read_from_sensor(csv_file, max_size_kb=38)
        lettre = self.predire_depuis_csv(csv_file)

        self.ser.write("S\n".encode())
        time.sleep(0.5)
        self.discard_last_line()

        print("⏳ Reprise lecture continue dans 1 sec...\n")
        time.sleep(1)
        self.ser.reset_input_buffer()
        self.ser.write("R\n".encode())
        self.lecture_continue_active = True

    def start_command(self):
        threading.Thread(target=self.start_acquisition_sequence, daemon=True).start()

    def closeEvent(self, event):
        print("🛑 Fermeture de l'application...")
        self.running = False  # Stopper le thread proprement
        try:
            self.ser.write("S\n".encode())
            time.sleep(0.5)
            self.ser.close()
            print("🔌 Port série fermé correctement.")
        except Exception as e:
            print(f"⚠️ Erreur à la fermeture : {e}")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

