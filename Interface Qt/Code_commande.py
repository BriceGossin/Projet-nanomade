from PySide6.QtWidgets import *
from PySide6.QtGui import QFont, QColor, QBrush, QPen, QShortcut, QKeySequence, QPalette
from PySide6.QtCore import Qt, QTimer, QPointF
import serial
import serial.tools.list_ports
import threading
import csv
import os
import datetime
import time

class FullscreenWindow(QMainWindow):
        """Fenêtre plein écran pour afficher QGraphicsView avec sortie via Échap."""
        def __init__(self, graphics_view):
            super().__init__()
            self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.setWindowState(Qt.WindowFullScreen)

            # 🖼️ Déplacer la vue graphique dans cette fenêtre plein écran
            self.setCentralWidget(graphics_view)

        def keyPressEvent(self, event):
            """Quitter le plein écran avec Échap."""
            if event.key() == Qt.Key_Escape:
                self.close()  # Ferme la fenêtre plein écran pour revenir au mode normal


class SerialWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Terminal Série")

        # Layout principal
        self.layout = QVBoxLayout(self)

        self.sensor_presence=[]
        self.sensor_data=[]
        self.headers= []
        self.calibrated = False
        self.k_response = None  # Déclaration globale
        
       

        # Création du GroupBox pour l'option d'enregistrement
        self.save_group = QGroupBox("Enregistrement")
        self.save_group.setStyleSheet("QGroupBox::title { color: white; font-weight: bold; }")
        self.save_layout = QVBoxLayout()
        self.save_group.setLayout(self.save_layout)

        # Création du label et de la checkbox
        self.save_label = QLabel("Enregistrer en csv : ")
        self.save_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.save_checkbox = QCheckBox("")
        self.save_checkbox.setStyleSheet("padding: 5px;")
        self.save_checkbox.toggled.connect(self.choose_save_location)

        # Layout horizontal pour aligner le label et la checkbox
        self.label_checkbox_layout = QHBoxLayout()
        self.label_checkbox_layout.addWidget(self.save_label)
        self.label_checkbox_layout.addWidget(self.save_checkbox)
        self.label_checkbox_layout.addStretch()  # Pour pousser la checkbox à gauche

        # Ajout du layout horizontal au layout principal du GroupBox
        self.save_layout.addLayout(self.label_checkbox_layout)

        # Section Connexion
        self.connection_group = QGroupBox("Connexion")
        self.connection_group.setStyleSheet("QGroupBox::title { color: white; font-weight: bold; }")
        self.connection_layout = QHBoxLayout()
        self.connection_group.setLayout(self.connection_layout)

        self.port_label = QLabel("Port COM :")
        self.port_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.port_dropdown = QComboBox()
        self.port_dropdown.setFixedWidth(150)
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

        
        
        # Section Envoi Manuel
        self.send_group = QGroupBox("Envoi Manuel")
        self.send_group.setStyleSheet("QGroupBox::title { color: white; font-weight: bold; }")
        self.send_layout = QHBoxLayout()
        self.send_group.setLayout(self.send_layout)

        # Champ de saisie pour envoyer des commandes
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Entrez une commande...")
        self.command_input.setFixedWidth(200)

        # Bouton d'envoi
        self.send_button = QPushButton("Envoyer")
        self.send_button.setFixedWidth(100)
        self.send_button.setStyleSheet("background-color: #28A745; color: white; padding: 5px; border-radius: 5px;")
        self.send_button.clicked.connect(self.send_command)
        self.command_input.returnPressed.connect(self.send_command)


        # Ajout au layout horizontal
        self.send_layout.addWidget(self.command_input)
        self.send_layout.addWidget(self.send_button)

        # Création d'un layout horizontal pour aligner, Enregistrement, Calibration, Appareillage et Envoi Manuel
        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.save_group)
        self.top_layout.addWidget(self.connection_group)
        self.top_layout.addWidget(self.send_group)

        # Ajout du layout horizontal à la fenêtre principale
        self.layout.addLayout(self.top_layout)
        
        
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
        self.calibration_controls_layout.addWidget(QLabel("Gain de force :"))
        self.calibration_controls_layout.addWidget(self.gain_dropdown)
        self.calibration_controls_layout.addWidget(QLabel("Limite de force :"))
        self.calibration_controls_layout.addWidget(self.limit_dropdown)
        self.calibration_controls_layout.addWidget(self.validate_button)

        # Création du groupe Output
        self.output_group = QGroupBox("Output")
        self.output_group.setStyleSheet("QGroupBox::title { color: white; font-weight: bold; }")
        self.output_group.setFixedHeight(75)
        self.output_layout = QVBoxLayout()
        self.output_group.setLayout(self.output_layout)  # Correction ici


        # Zone d'affichage des messages reçus
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        #self.output_display.setStyleSheet("margin-top: 10px;")
        self.output_display.setFixedHeight(40)

        self.output_layout.addWidget(self.output_display)

        # Ajout du layout horizontal au layout principal de calibration
        self.calibration_layout.addLayout(self.calibration_controls_layout)

        # Création d'un layout horizontal pour aligner Calibration et Output Display
        self.top_layout = QHBoxLayout()
        self.top_layout.addWidget(self.calibration_group)
        self.top_layout.addWidget(self.output_group)  # Correction ici
        

        # Ajout du layout horizontal à la fenêtre principale
        self.layout.addLayout(self.top_layout)



        # Variables pour la communication série
        self.ser = None
        self.is_connected = False
        self.read_thread = None  # Thread de lecture

        """ # Fichier CSV pour stocker les réponses
        self.csv_file = "sensor_responses.csv"
        self.init_csv_file()
        """
        
        
        
       # 🔹 Ajout de la partie graphique (Rectangles)
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        self.layout.addWidget(self.graphics_view)

        # 📉 Vecteurs invisibles par défaut
        self.vectors_visible = False
        self.vectors = []  # Liste pour stocker les références aux QGraphicsLineItem
        self.vector_start = None  # Pour enregistrer le point de départ du vecteur
        
        
        
        self.rect_items = []  # Stocke les rectangles
        self.create_rectangles()  # Crée les rectangles initiaux

        # Timer pour la mise à jour des rectangles en live
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_rectangles)
        
       
        # 🔴 Bouton Afficher/Cacher Vecteurs
        self.toggle_vectors_button = QPushButton("Afficher/Cacher Vecteurs", self.graphics_view)
        self.toggle_vectors_button.setFixedSize(160, 40)
        self.toggle_vectors_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E88E5;
            }
        """)
        self.toggle_vectors_button.move(
            20,  # Positionné à gauche
            self.graphics_view.height() - self.toggle_vectors_button.height() - 20
        )
        self.toggle_vectors_button.raise_()
        self.toggle_vectors_button.clicked.connect(self.toggle_vectors)

        # 🔄 Bouton Réinitialiser Vecteurs
        self.reset_vectors_button = QPushButton("Réinitialiser Vecteurs", self.graphics_view)
        self.reset_vectors_button.setFixedSize(160, 40)
        self.reset_vectors_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        self.reset_vectors_button.move(
            20,
            self.graphics_view.height() - self.toggle_vectors_button.height() - self.reset_vectors_button.height() - 40
        )
        self.reset_vectors_button.raise_()
        self.reset_vectors_button.clicked.connect(self.reset_vectors)


        # 🔲 Bouton plein écran en bas à droite
        self.fullscreen_button = QPushButton("🖵 Plein écran", self.graphics_view)
        self.fullscreen_button.setFixedSize(120, 40)
        self.fullscreen_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # ➡️ Positionnement en bas à droite
        self.fullscreen_button.move(
            self.graphics_view.width() - self.fullscreen_button.width() - 20,
            self.graphics_view.height() - self.fullscreen_button.height() - 20
        )
        self.fullscreen_button.raise_()  # S'assurer que le bouton reste au-dessus de la scène

        # 🔗 Connexion du bouton à la fonction de basculement plein écran
        self.fullscreen_button.clicked.connect(self.toggle_graphics_fullscreen)

        # 📏 Mise à jour de la position en cas de redimensionnement
        self.graphics_view.resizeEvent = self.update_button_position



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
        """Établit la connexion avec le port série et récupère la réponse K."""
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

            # Lecture de la réponse après 'K'
            self.k_response = self.ser.readline().decode().strip()  
            #self.output_display.append(f"📥 Réponse reçue : {self.k_response}") 
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            self.save_to_csv(timestamp, None, None, self.k_response) 

            # Vérifier si la réponse est valide
            if not self.k_response:
                self.output_display.append("⚠️ Aucune réponse du capteur !")
                return

            self.calibrated = True  # Activation du flag de calibration

            

            self.read_thread = threading.Thread(target=self.read_from_sensor, daemon=True)
            self.read_thread.start()
            self.update_timer.start(5)  # Mise à jour toutes les 20 ms
            
            # Lancer la mise à jour après réception de la réponse K
            self.update_timer.timeout.connect(self.create_rectangles)

            
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
        self.update_timer.stop()  # Arrêter la mise à jour des rectangles


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
                #self.output_display.append(f"📥 Reçu : {response}")
                
                """# Récupération du timestamp actuel
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                # Préparation des valeurs à enregistrer
                values = [""] * 32  # On initialise une liste de 32 éléments vides
                presence_values = [""] * 8  # Liste vide pour les valeurs de présence

                # Appel de save_to_csv avec tous les paramètres requis
                self.save_to_csv(timestamp, values, presence_values, response)"""
                break
            time.sleep(0.1)  # Petit délai pour éviter de bloquer la boucle inutilement

        # Envoi de la limite
        limit_command = f"{limit_value}\n"
        self.ser.write(limit_command.encode())
        self.output_display.append(f"📤 Envoyé : {limit_command.strip()}")


    def read_from_sensor(self):
        """Lit et stocke les données du capteur en continu, en filtrant les valeurs inactives."""
        while self.is_connected and self.ser and self.ser.is_open:
            try:
                data = self.ser.readline().decode().strip()
                if data:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
                    #self.output_display.append(f"📥 [{timestamp}] Reçu : {data}")
                    
                    # Définition des headers selon la trame
                    headers = [
                        "MF1", "MF2", "MF3", "MF4", "MF8", "MF7", "MF6", "MF5",
                        "UF1", "UF2", "UF3", "UF4", "UF5", "UF6", "UF7", "UF8"
                    ]
                    
                    # Filtrer uniquement les headers des capteurs actifs
                    active_headers = []
                    

                   


                    # Extraction des valeurs analogiques
                    values = data.split()
                    if len(values) > 17:  # Limite à 17 valeurs max
                        values = values[:17]

                    # Conversion en int avec gestion des valeurs non numériques
                    values = [int(v) if v.isdigit() else 1000 for v in values]
                    
                    # Extraction des valeurs de présence (indices 16 à 33)
                    presence_values = data.split()[16:33]
                    presence_values = [int(v) if v in ('0', '1') else 0 for v in presence_values]
                    
                    # Réorganisation des valeurs par groupes de 4. Nécessaire pour avoir les électrodes dans le bon ordre 
                    reorganized_values = []
                    presence_reorganized_values = []
                    
                    for i in range(0, len(values), 4):
                        group = values[i:i+4]
                        presence_group= presence_values[i:i+4]
                        # Inverser seulement le deuxième groupe (i = 4 car 2ème groupe commence à l'indice 4)
                        if i == 4:
                            group.reverse()
                            presence_group.reverse()
                        reorganized_values.extend(group)
                        presence_reorganized_values.extend(presence_group)

                    
                    

                    # Association des valeurs avec les headers
                    sensor_data = []
                    sensor_presence = {}
                    for h, v, p in zip(headers, reorganized_values, presence_reorganized_values):
                        if v not in (1000, 3299):  # Filtrage des valeurs inactives
                            sensor_data.append(f"{h}: {v}")
                            sensor_presence[h] = p  # 0 ou 1 pour la présence
                            active_headers.append(h)

                            
                    self.headers=active_headers
                    
                    
                    # Mise à jour des capteurs actifs et des présences
                    self.sensor_data = sensor_data
                    self.sensor_presence = sensor_presence  # Stockage des présences dans un dict

                    #print("🔍 sensor_data :", self.sensor_data)
                    #print("🔍 sensor_presence :", self.sensor_presence)
                    
                    #Enregistrement dans le csv
                    
                    #self.save_to_csv(timestamp, reorganized_values, presence_reorganized_values, self.k_response)
                    self.save_to_csv(timestamp, reorganized_values, presence_reorganized_values, data)

            except Exception as e:
                self.output_display.append(f"⚠️ Erreur de lecture : {e}")
                break





    def create_rectangles(self):
        """Crée des rectangles pour afficher les capteurs actifs avec les bons headers et valeurs,
        et trace des vecteurs entre eux en fonction des valeurs de présence, sans jamais les effacer."""

        # ⚡ Initialisation une seule fois des rectangles, vecteurs et boutons
        if not hasattr(self, 'rect_items'):
            self.rect_items = []
            self.vectors = []
            self.vector_start = None

            # 🎨 Création de la vue graphique
            self.scene = QGraphicsScene()
            self.view = QGraphicsView(self.scene)

        rect_width = 75
        rect_height = 150
        spacing = 20
        x_offset = 10
        y_offset = 50
        row_limit = 4
        count = 0

        matrix_headers = [f"MF{i}" for i in range(1, 5)] + [f"MF{i}" for i in range(8, 4, -1)]
        has_matrix_sensors = all(header in self.headers for header in matrix_headers)

        if has_matrix_sensors:
            bg_width = (rect_width + spacing) * 4 + 50
            bg_height = (rect_height + spacing) * 2 + 50
            background_rect = QGraphicsRectItem(-20, 20, bg_width, bg_height)
            background_rect.setBrush(QBrush(QColor(180, 180, 180)))  # Fond gris clair
            background_rect.setZValue(-1)
            self.scene.addItem(background_rect)
            bg_bottom = 20 + bg_height
        else:
            bg_bottom = 50

        existing_items = {header.toPlainText(): (rect, value_text, header) for rect, value_text, header in self.rect_items}

        for sensor_info in self.sensor_data:
            try:
                key, value = sensor_info.split(": ")
                value = int(value)
            except ValueError:
                continue

            if count >= row_limit:
                x_offset = 10
                y_offset += rect_height + spacing
                count = 0

            if has_matrix_sensors and key not in matrix_headers:
                y_offset = bg_bottom + 30

            if key in existing_items:
                rect, value_text, header_text = existing_items[key]
                rect.setBrush(QBrush(self.get_color(value)))
                value_text.setPlainText(f"{value}")
                value_text.setPos(x_offset + rect_width / 4, y_offset + rect_height / 2)
                header_text.setPos(x_offset - 15 + rect_width / 2, y_offset + rect_height / 4)
                rect.setRect(x_offset, y_offset, rect_width, rect_height)
            else:
                rect = QGraphicsRectItem(x_offset, y_offset, rect_width, rect_height)
                rect.setBrush(QBrush(self.get_color(value)))
                self.scene.addItem(rect)

                value_text = QGraphicsTextItem(f"{value}")
                value_text.setDefaultTextColor(Qt.GlobalColor.black)
                value_text.setFont(QFont("Arial", 10))
                value_text.setPos(x_offset + rect_width / 4, y_offset + rect_height / 2)
                self.scene.addItem(value_text)

                header_text = QGraphicsTextItem(key)
                header_text.setDefaultTextColor(Qt.GlobalColor.black)
                header_text.setFont(QFont("Arial", 10, QFont.Bold))
                header_text.setPos(x_offset - 15 + rect_width / 2, y_offset + rect_height / 4)
                self.scene.addItem(header_text)

                self.rect_items.append((rect, value_text, header_text))

            if key in self.sensor_presence and self.sensor_presence[key] == 1:
                rect.setPen(QPen(QColor(0, 0, 255), 5))
                rect.setZValue(1)

                center_x = x_offset + rect_width / 2
                center_y = y_offset + rect_height / 2
                current_point = QPointF(center_x, center_y)

                if self.vector_start:
                    vector = QGraphicsLineItem(
                        self.vector_start.x(), self.vector_start.y(),
                        current_point.x(), current_point.y()
                    )

                    # 🟥 Par défaut, les vecteurs sont transparents
                    transparent_pen = QPen(Qt.GlobalColor.transparent)
                    transparent_pen.setWidth(3)
                    vector.setPen(transparent_pen)
                    vector.setZValue(3)

                    self.vectors.append(vector)
                    self.vector_start = None
                else:
                    self.vector_start = current_point
            else:
                rect.setPen(QPen(Qt.GlobalColor.transparent))

            value_text.setZValue(2)
            header_text.setZValue(2)

            x_offset += rect_width + spacing
            count += 1

        # 📌 Mise à jour de la visibilité des vecteurs
        if self.vectors_visible:
            for vector in self.vectors:
                red_pen = QPen(QColor(255, 0, 0))  # 🔴 Rouge vif
                red_pen.setWidth(3)
                vector.setPen(red_pen)
                if vector.scene() is None:  # Si le vecteur n'est pas déjà dans la scène
                    self.scene.addItem(vector)
        else:
            for vector in self.vectors:
                transparent_pen = QPen(Qt.GlobalColor.transparent)
                transparent_pen.setWidth(3)
                vector.setPen(transparent_pen)

        self.scene.update()


 









    def update_rectangles(self):
        """Met à jour les rectangles avec les valeurs du capteur en temps réel, en gardant la correspondance correcte."""
        if not hasattr(self, 'sensor_values') or not self.calibrated or not self.rect_items:
            return

        # Vérification que le nombre de capteurs actifs correspond bien
        if len(self.rect_items) != len(self.sensor_values):
            print(f"⚠️ Désalignement détecté ! rect_items: {len(self.rect_items)}, sensor_values: {len(self.sensor_values)}")
            return

        for i, (rect, value_text, header_text) in enumerate(self.rect_items):
            if i >= len(self.sensor_values):
                break  # Sécurité pour éviter l'IndexError

            value = self.sensor_values[i]  # Assure-toi que l'indice correspond

            # Mise à jour de la couleur selon la valeur
            color = self.get_color(value)
            rect.setBrush(QBrush(color))

            # Mise à jour de la valeur affichée
            value_text.setPlainText(f"{value:.1f}")  # Arrondi à 1 décimale

            # Garder le texte visible
            value_text.setZValue(2)
            header_text.setZValue(2)

        self.scene.update()  # Rafraîchir la scène après mise à jour



    def get_color(self, value):
        """Définit une couleur avec une transition fluide."""
        min_value, mid_value, max_value = 1650, 1700, 1750
        value = max(min_value, min(max_value, value))

        if value <= mid_value:
            ratio = (value - min_value) / (mid_value - min_value)
            red = int(255 * ratio)
            green = 255
        else:
            ratio = (value - mid_value) / (max_value - mid_value)
            red = 255
            green = int(255 * (1 - ratio))

        return QColor(red, green, 0)
    
    

    def save_to_csv(self, timestamp, values=None, presence_values=None, response=None):
        """Enregistre directement les réponses reçues dans le fichier CSV sous forme simplifiée."""
        ligne = [timestamp]
        
        # Si une réponse est fournie, la découper en parties pour les écrire dans le CSV
        if response:
            # Découpage par espace pour obtenir chaque élément du message
            elements = response.split()
            ligne.extend(elements)
        
        # Compléter avec des champs vides jusqu'à 32 colonnes pour garder un format fixe
        while len(ligne) < 33:
            ligne.append("")

        # Écriture dans le fichier CSV
        try:
            with open(self.csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(ligne)
                #print(f"Données enregistrées : {ligne}")
        except Exception as e:
            #self.output_display.append(f"⚠️ Erreur de sauvegarde CSV : {e}")
            #print(f"⚠️ Erreur de sauvegarde CSV : {e}")
            return 0

    def choose_save_location(self, state): 
        """Ouvre une boîte de dialogue pour choisir l'emplacement en mode clair et force le format CSV."""
        
        if state:  # Si la case est cochée
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            
            # Nom de fichier par défaut avec extension CSV
            default_name = "enregistrement_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
            
            # Création de la boîte de dialogue de sauvegarde
            file_dialog = QFileDialog(self, 
                                    "Choisir l'emplacement du fichier", 
                                    default_name, 
                                    "Fichiers CSV (*.csv);;Tous les fichiers (*)",
                                    options=options)
                                    
            file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            
            # 🍋 Applique la palette claire uniquement à cette boîte de dialogue
            file_dialog.setPalette(self.get_light_palette())
            
            # Affichage de la boîte de dialogue
            if file_dialog.exec_():
                file_path = file_dialog.selectedFiles()[0]  # Récupère le chemin du fichier
                
                if file_path:
                    # Vérification et ajout de l'extension .csv si l'utilisateur ne l'a pas ajoutée
                    if not file_path.endswith(".csv"):
                        file_path += ".csv"
                        
                    self.csv_file = file_path  # Mise à jour du chemin du fichier
                    self.output_display.append(f"📁 Fichier enregistré à : {self.csv_file}")
                    self.init_csv_file()

                
    def get_light_palette(self):
        """Renvoie une palette claire pour les fenêtres contextuelles."""
        light_palette = QPalette()
        light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
        light_palette.setColor(QPalette.AlternateBase, QColor(230, 230, 230))
        light_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
        light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
        light_palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        light_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        return light_palette

                
                
    def toggle_graphics_fullscreen(self):
        """Bascule le QGraphicsView en mode plein écran ou normal."""
        if hasattr(self, 'fullscreen_window') and self.fullscreen_window.isVisible():
            # ⬅️ Sortie du mode plein écran
            
            # Fermer la fenêtre plein écran
            self.fullscreen_window.close()
            
            # Réintégrer le graphics_view à son index d'origine
            self.layout.insertWidget(self.original_index, self.graphics_view)
            
            # Réactiver les barres de défilement
            self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            self.fullscreen_button.setText("🖵 Plein écran")

        else:
            # 🔀 Passage en mode plein écran
            
            # Mémorisation de l'index d'origine du graphics_view
            self.original_index = self.layout.indexOf(self.graphics_view)
            
            # Retrait temporaire du graphics_view du layout
            self.layout.removeWidget(self.graphics_view)
            
            # Création de la fenêtre plein écran
            self.fullscreen_window = QMainWindow()
            self.fullscreen_window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.fullscreen_window.setWindowState(Qt.WindowFullScreen)
            self.fullscreen_window.setCentralWidget(self.graphics_view)
            
            # Désactiver les barres de défilement en plein écran
            self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # ⌨️ Ajout du raccourci Échap pour quitter le plein écran
            esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self.fullscreen_window)
            esc_shortcut.activated.connect(self.toggle_graphics_fullscreen)
            
            self.fullscreen_window.show()
            self.fullscreen_button.setText("❌ Quitter plein écran")




    def update_button_position(self, event):
        """Met à jour la position du bouton plein écran lors du redimensionnement."""
        self.fullscreen_button.move(
            self.graphics_view.width() - self.fullscreen_button.width() - 20,
            self.graphics_view.height() - self.fullscreen_button.height() - 20
        )
        QGraphicsView.resizeEvent(self.graphics_view, event)
        
        
        
    def toggle_vectors(self):
        # 🔄 Inversion de l'état de visibilité
        self.vectors_visible = not self.vectors_visible

        # 🔘 Mise à jour du texte du bouton
        if self.vectors_visible:
            self.toggle_vectors_button.setText("Cacher Vecteurs")
        else:
            self.toggle_vectors_button.setText("Afficher Vecteurs")

        # 🔄 Mise à jour de la scène
        self.scene.update()


    def reset_vectors(self):
        """Réinitialiser tous les vecteurs"""
        for vector in self.vectors:
            self.scene.removeItem(vector)
        self.vectors.clear()
        self.vector_start = None

        
    


