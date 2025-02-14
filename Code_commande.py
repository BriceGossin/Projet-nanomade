import sys
import serial
import threading
import csv
import os
import datetime
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QHBoxLayout

class SerialWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Terminal Série")

        # Layout principal
        self.layout = QVBoxLayout(self)

        # Sélection du port série
        self.port_label = QLabel("Port COM :")
        self.port_dropdown = QLineEdit("COM9")  # Par défaut COM9 (modifiable)
        self.layout.addWidget(self.port_label)
        self.layout.addWidget(self.port_dropdown)

        # Zone d'affichage des messages reçus
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.layout.addWidget(self.output_display)

        # Champ de saisie pour envoyer des commandes
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Entrez une commande...")
        self.layout.addWidget(self.command_input)

        # Bouton d'envoi
        self.send_button = QPushButton("Envoyer")
        self.send_button.clicked.connect(self.send_command)
        self.layout.addWidget(self.send_button)

        # Bouton pour démarrer/arrêter la connexion
        self.connect_button = QPushButton("Se connecter")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.layout.addWidget(self.connect_button)

        # Variables pour la communication série
        self.ser = None
        self.is_connected = False
        self.read_thread = None  # Thread de lecture

        # Fichier CSV pour stocker les réponses
        self.csv_file = "sensor_responses.csv"
        self.init_csv_file()

    def init_csv_file(self):
        """Crée le fichier CSV et ajoute un en-tête si nécessaire."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Timestamp", "M_F_1", "M_F_2", "M_F_3", "M_F_4", "M_F_5", "M_F_6", "M_F_7", "M_F_8",
                    "U_F_1", "U_F_2", "U_F_3", "U_F_4", "U_F_5", "U_F_6", "U_F_7", "U_F_8",
                    "M_C_1", "M_C_2", "M_C_3", "M_C_4", "M_C_5", "M_C_6", "M_C_7", "M_C_8",
                    "U_C_1", "U_C_2", "U_C_3", "U_C_4", "U_C_5", "U_C_6", "U_C_7", "U_C_8"
                ])
                print(f"✅ Fichier CSV '{self.csv_file}' créé avec un en-tête.")

    def toggle_connection(self):
        """Se connecte ou se déconnecte du port série."""
        if self.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """Établit la connexion avec le port série et démarre la lecture."""
        port_name = self.port_dropdown.text().strip()

        try:
            self.ser = serial.Serial(port_name, baudrate=430000, timeout=1)
            self.is_connected = True
            self.connect_button.setText("Déconnexion")
            self.output_display.append(f"✅ Connecté à {port_name}")

            # Démarrer le thread de lecture
            self.read_thread = threading.Thread(target=self.read_from_sensor, daemon=True)
            self.read_thread.start()

        except serial.SerialException:
            self.output_display.append(f"❌ Impossible de se connecter à {port_name}")

    def disconnect_serial(self):
        """Ferme la connexion série."""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.is_connected = False
        self.connect_button.setText("Se connecter")
        self.output_display.append("🔌 Déconnecté")

    def send_command(self):
        """Envoie une commande au capteur."""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            self.output_display.append("⚠️ Pas de connexion active !")
            return

        command = self.command_input.text().strip()
        if command:
            self.ser.write((command + "\r\n").encode())  # Envoi avec \r\n
            self.output_display.append(f"📤 Envoyé : {command}")
            self.command_input.clear()

    def read_from_sensor(self):
        """Lit et enregistre les données en continu."""
        while self.is_connected and self.ser and self.ser.is_open:
            try:
                data = self.ser.readline().decode().strip()
                if data:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                    self.output_display.append(f"📥 [{timestamp}] Reçu : {data}")

                    # Enregistrer dans le CSV
                    self.save_to_csv(timestamp, data)
            except Exception as e:
                self.output_display.append(f"⚠️ Erreur de lecture : {e}")
                break

    def save_to_csv(self, timestamp, data):
        """Enregistre les réponses du capteur dans un fichier CSV."""
        try:
            with open(self.csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                values = data.split()

                # Vérifier si c'est une ligne spéciale
                if len(values) < 8:  # Pas assez de valeurs, c'est une ligne spéciale
                    writer.writerow([timestamp] + values + ["" for _ in range(31 - len(values))])
                else:  # Données de capteur normales
                    row = [timestamp] + values + ["" for _ in range(31 - len(values))]
                    writer.writerow(row)

        except Exception as e:
            self.output_display.append(f"⚠️ Erreur lors de l'enregistrement CSV : {e}")
