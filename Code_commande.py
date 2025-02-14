import sys
import serial
import serial.tools.list_ports
import threading
import csv
import os
import datetime
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QComboBox, QPushButton,
    QLabel, QHBoxLayout, QLineEdit, QFrame, QGroupBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class SerialWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Terminal Série")

        # Layout principal
        self.layout = QVBoxLayout(self)

        # Section Connexion
        self.connection_group = QGroupBox("Connexion")
        self.connection_group.setStyleSheet("QGroupBox::title { color: white; font-weight: bold; }")
        self.connection_layout = QHBoxLayout()
        self.connection_group.setLayout(self.connection_layout)

        self.port_label = QLabel("Port COM :")
        self.port_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.port_dropdown = QComboBox()
        self.port_dropdown.setFixedWidth(120)
        self.refresh_ports()
        self.port_dropdown.setStyleSheet("padding: 5px; font-size: 12px;")
        
        self.connect_button = QPushButton("Se connecter")
        self.connect_button.setFixedWidth(120)
        self.connect_button.setStyleSheet("background-color: #007BFF; color: white;font:bold; padding: 5px; border-radius: 5px;")
        self.connect_button.clicked.connect(self.toggle_connection)
        
        self.connection_layout.addWidget(self.port_label)
        self.connection_layout.addWidget(self.port_dropdown)
        self.connection_layout.addWidget(self.connect_button)
        self.connection_layout.addStretch()
        self.layout.addWidget(self.connection_group)

        
        # Section Calibration
        self.calibration_group = QGroupBox("Calibration")
        self.calibration_group.setStyleSheet("QGroupBox::title { color: white; font-weight: bold; }")
        self.calibration_layout = QVBoxLayout()
        self.calibration_group.setLayout(self.calibration_layout)

        # Layout horizontal pour aligner à gauche
        self.calibration_controls_layout = QHBoxLayout()
        self.calibration_controls_layout.setAlignment(Qt.AlignLeft)  # Alignement à gauche

        # Menu déroulant Gain de Force
        self.gain_dropdown = QComboBox()
        self.gain_dropdown.addItems(["GA", "GB", "GC", "GD", "GE", "GF", "GG"])
        self.gain_dropdown.setFixedWidth(80)
        self.gain_dropdown.setStyleSheet("padding: 5px; font-size: 12px;")

        # Menu déroulant Limite de Force
        self.limit_dropdown = QComboBox()
        self.limit_dropdown.addItems(["CA", "CB", "CC", "CD", "CE", "CF", "CG"])
        self.limit_dropdown.setFixedWidth(80)
        self.limit_dropdown.setStyleSheet("padding: 5px; font-size: 12px;")

        # Bouton Valider
        self.validate_button = QPushButton("Valider")
        self.validate_button.setFixedWidth(100)
        self.validate_button.setStyleSheet("background-color: #FF8800; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.validate_button.clicked.connect(self.send_calibration_values)

        # Ajout des widgets dans le layout horizontal
        self.calibration_controls_layout.addWidget(QLabel("Gain:"))
        self.calibration_controls_layout.addWidget(self.gain_dropdown)
        self.calibration_controls_layout.addWidget(QLabel("Limite:"))
        self.calibration_controls_layout.addWidget(self.limit_dropdown)
        self.calibration_controls_layout.addWidget(self.validate_button)

        # Ajout du layout horizontal au layout principal de calibration
        self.calibration_layout.addLayout(self.calibration_controls_layout)

        # Ajout du groupe de calibration à la fenêtre principale
        self.layout.addWidget(self.calibration_group)


        # Zone d'affichage des messages reçus
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("margin-top: 10px;")
        self.layout.addWidget(self.output_display)

        # Champ de saisie pour envoyer des commandes
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Entrez une commande...")
        self.layout.addWidget(self.command_input)

        # Bouton d'envoi
        self.send_button = QPushButton("Envoyer")
        self.send_button.setStyleSheet("background-color: #28A745; color: white; padding: 5px; border-radius: 5px;")
        self.send_button.clicked.connect(self.send_command)
        self.layout.addWidget(self.send_button)

        # Variables pour la communication série
        self.ser = None
        self.is_connected = False
        self.read_thread = None  # Thread de lecture

        # Fichier CSV pour stocker les réponses
        self.csv_file = "sensor_responses.csv"
        self.init_csv_file()

    def refresh_ports(self):
        """Détecte les ports disponibles et met à jour la liste déroulante."""
        self.port_dropdown.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_dropdown.addItem(port.device)
        if self.port_dropdown.count() == 0:
            self.port_dropdown.addItem("Aucun port détecté")

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
    def toggle_connection(self):
        """Se connecte ou se déconnecte du port série."""
        if self.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        """Établit la connexion avec le port série et démarre la lecture."""
        port_name = self.port_dropdown.currentText().strip()
        if port_name == "Aucun port détecté":
            self.output_display.append("⚠️ Aucun port disponible !")
            return
        try:
            self.ser = serial.Serial(port_name, baudrate=430000, timeout=2)
            self.is_connected = True
            self.connect_button.setText("Déconnexion")
            self.connect_button.setStyleSheet("background-color: #DC3545; color: white;font:bold; padding: 5px; border-radius: 5px;")
            self.output_display.append(f"✅ Connecté à {port_name}")
            
            # Envoi du caractère 'K' après connexion
            self.ser.write(b'K\n')
            self.output_display.append("📤 Envoyé : K")

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
        self.connect_button.setStyleSheet("background-color: #007BFF; color: white;font:bold; padding: 5px; border-radius: 5px;")
        self.output_display.append("🔌 Déconnecté")


    def send_command(self):
        """Envoie une commande au capteur."""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            self.output_display.append("⚠️ Pas de connexion active !")
            return
        command = self.command_input.text().strip()
        if command:
            self.ser.write((command + "\r\n").encode())
            self.output_display.append(f"📤 Envoyé : {command}")
            self.command_input.clear()
            
    def send_calibration_values(self):
        """Envoie les valeurs de calibration sélectionnées avec attente de réponse."""
        if not self.is_connected or not self.ser or not self.ser.is_open:
            self.output_display.append("⚠️ Pas de connexion active !")
            return

        gain_value = self.gain_dropdown.currentText()
        limit_value = self.limit_dropdown.currentText()

        # Envoi du gain
        gain_command = f"{gain_value}\n"
        self.ser.write(gain_command.encode())
        self.output_display.append(f"📤 Envoyé : {gain_command.strip()}")

        # Attente d'une réponse du capteur
        start_time = time.time()
        while time.time() - start_time < 2:  # Timeout de 2 secondes
            if self.ser.in_waiting:
                response = self.ser.readline().decode().strip()
                self.output_display.append(f"📥 Reçu : {response}")
                break
            time.sleep(0.1)  # Petit délai pour éviter de bloquer la boucle inutilement

        # Envoi de la limite
        limit_command = f"{limit_value}\n"
        self.ser.write(limit_command.encode())
        self.output_display.append(f"📤 Envoyé : {limit_command.strip()}")

    def read_from_sensor(self):
        """Lit et enregistre les données en continu."""
        while self.is_connected and self.ser and self.ser.is_open:
            try:
                data = self.ser.readline().decode().strip()
                if data:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                    self.output_display.append(f"📥 [{timestamp}] Reçu : {data}")
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
                writer.writerow([timestamp] + values + ["" for _ in range(31 - len(values))])
        except Exception as e:
            self.output_display.append(f"⚠️ Erreur lors de l'enregistrement CSV : {e}")
