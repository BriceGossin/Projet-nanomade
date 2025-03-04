import sys
import csv
import os
from PySide6.QtWidgets import *
from PySide6.QtGui import QBrush, QColor, QPen, QFont, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QTimer
from Code_commande import FullscreenWindow


class Rectangles(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Calibration Viewer")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background-color: #f4f4f4;")  # Fond clair et moderne

        self.headers = []  # ✅ Initialisation vide pour éviter l'erreur
        self.data_rows = []
        self.presence_rows = []
        self.csv_file = None  # Stockera le chemin du fichier une fois sélectionné
        self.speed = 20  # ✅ Définit une vitesse par défaut de 1 seconde
        self.reverse_order = False  # ✅ Ajout de reverse_order
        
        # 📌 Layout principal
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        
        
        # Zone de sélection (bouton + menu déroulant)
        selection_layout = QHBoxLayout()
                
         # Label pour afficher le fichier sélectionné
        self.label = QLabel("📂 Sélectionnez un fichier CSV")
        self.label.setStyleSheet("font-size: 16px; background-color: transparent;")
       

        
        selection_layout.addWidget(self.label, alignment=Qt.AlignLeft)
        
        # Bouton pour sélectionner un fichier CSV 
        self.select_file_button = QPushButton("📂 Rechercher")
        self.select_file_button.setFixedSize(120, 30)
        self.select_file_button.setStyleSheet(
            "background-color: #5A9; color: white; font-weight: bold; "
            "border-radius: 5px; padding: 3px;"
        )
        selection_layout.addWidget(self.select_file_button)

       
        
        self.select_file_button.clicked.connect(self.open_file_dialog)
        selection_layout.addWidget(self.select_file_button, alignment=Qt.AlignCenter)

        
        # Ajout du layout de sélection à l'interface
        self.layout.addLayout(selection_layout)
        
        
        # Label "Suggestions"
        self.suggestions_label = QLabel("📌 Suggestions :")
        self.suggestions_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        self.layout.addWidget(self.suggestions_label, alignment=Qt.AlignLeft)

        # Liste des fichiers CSV disponibles dans le répertoire courant (plus basse et moins longue)
        self.suggestions_list = QListWidget()
        self.suggestions_list.setFixedHeight(100)
        
        # Ajustement de la largeur pour s'étendre avec la fenêtre
        self.suggestions_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.suggestions_list.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 5px; padding: 5px;"
            "background-color: #f9f9f9; font-size: 14px;"
        )
        self.suggestions_list.setToolTip("Cliquez sur un fichier pour l'afficher.")
        self.suggestions_list.itemClicked.connect(self.load_selected_csv)

        # Ajout de la liste avec un stretch pour s'adapter à l'espace
        self.layout.addWidget(self.suggestions_list, stretch=0)

        self.populate_suggestions()
        
        """self.series_data = {}  # Stocke les différentes séries de données
        self.global_headers = []  # Stockera les en-têtes globales

        # Menu déroulant pour naviguer dans les séries du CSV
        
        self.label_series = QLabel("Sélectionnez une série de données dans le fichier : ")
        self.suggestions_label.setStyleSheet("font-size: 14px; color : white")
        self.layout.addWidget(self.label_series, alignment=Qt.AlignCenter)
        
        self.series_dropdown = QComboBox()
        self.series_dropdown.setFixedSize(200, 30)
        self.series_dropdown.setStyleSheet("border-radius: 5px; padding: 3px;")
        #self.series_dropdown.setToolTip("Sélectionnez une série de données dans le fichier CSV.")
        #self.series_dropdown.currentIndexChanged.connect(self.load_selected_series)
        self.layout.addWidget(self.series_dropdown, alignment=Qt.AlignCenter)
        
        """

        # 🎨 Scène graphique
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.view.setStyleSheet("border: none;")  # Supprimer les bordures
        self.layout.addWidget(self.view)
        
         # 🔲 Bouton plein écran en bas à droite
        self.fullscreen_button = QPushButton("🖵 Plein écran", self.view)
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
            self.view.width() - self.fullscreen_button.width() - 20,
            self.view.height() - self.fullscreen_button.height() - 20
        )
        self.fullscreen_button.raise_()  # S'assurer que le bouton reste au-dessus de la scène

        # 🔗 Connexion du bouton à la fonction de basculement plein écran
        self.fullscreen_button.clicked.connect(self.toggle_graphics_fullscreen)

        # 📏 Mise à jour de la position en cas de redimensionnement
        self.view.resizeEvent = self.update_button_position

        # 🔹 Labels améliorés
        self.iteration_label = QLabel("Itération: 0")
        self.speed_label = QLabel("Vitesse: 20 ms")

        for lbl in [self.iteration_label, self.speed_label]:
            lbl.setFont(QFont("Arial", 10))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #333; padding: 5px;")
            self.layout.addWidget(lbl)

        # 🎛️ Boutons de contrôle avec icônes
        self.button_layout = QHBoxLayout()
        self.play_pause_button = QPushButton("▶ Play")
        self.slower_button = QPushButton("🐢 Ralentir")
        self.faster_button = QPushButton("⚡ Accélérer")
        self.prev_button = QPushButton("⬅ Précédent")
        self.next_button = QPushButton("➡ Suivant")
        self.reverse_button = QPushButton("🔄 Inverser")

        buttons = [
            self.prev_button, self.play_pause_button, self.next_button, 
            self.slower_button, self.faster_button, self.reverse_button
        ]

        for btn in buttons:
            btn.setFont(QFont("Arial", 10, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078D7; color: white; border-radius: 5px;
                    padding: 8px; border: none;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
            """)
            self.button_layout.addWidget(btn)

        self.layout.addLayout(self.button_layout)

       
        if self.headers:
            self.rect_items = self.create_rectangles()
            self.current_row_index = 0
            self.reverse_order = False
            self.display_row(0)

            # ⏳ Timer pour lecture automatique
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next_line)
            self.speed = 20
            self.is_playing = True
            self.timer.start(self.speed)

        # Connexions des boutons
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.slower_button.clicked.connect(self.slow_down)
        self.faster_button.clicked.connect(self.speed_up)
        self.prev_button.clicked.connect(self.prev_line)
        self.next_button.clicked.connect(self.next_line)
        self.reverse_button.clicked.connect(self.toggle_direction)


    def open_file_dialog(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier CSV."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier CSV", "", "Fichiers CSV (*.csv)")
        if file_path:
            self.label.setText(f"📄 Fichier sélectionné : {os.path.basename(file_path)}")
            self.load_csv(file_path)

    def populate_suggestions(self):
        """Liste les fichiers CSV dans le répertoire courant et les affiche joliment."""
        self.suggestions_list.clear()
        csv_files = [f for f in os.listdir() if f.endswith(".csv")]

        if csv_files:
            for file in csv_files:
                self.suggestions_list.addItem(f"📄 {file}")
        else:
            self.suggestions_list.addItem("⚠️ Aucun fichier CSV trouvé")
            
    def load_selected_csv(self, item):
        """Charge un fichier CSV sélectionné depuis la liste des suggestions."""
        file_name = item.text().strip()  # Supprime les espaces blancs
        file_name = file_name.replace("📄 ", "")  # 🔥 Enlève l'icône ajoutée pour l'affichage

        if os.path.exists(file_name):  # Vérifie si le fichier existe
            self.label.setText(f"📄 Fichier sélectionné : {file_name}")
            self.csv_file = os.path.abspath(file_name)  # Convertit en chemin absolu
            self.load_csv(self.csv_file)  # Charge le fichier CSV
        else:
            QMessageBox.warning(self, "Erreur", f"Le fichier '{file_name}' est introuvable.")


            
            
    def load_csv(self, csv_file):
        """Charge les données et met à jour l'affichage."""
        self.csv_file = csv_file
        self.headers, self.data_rows, self.presence_rows = self.load_calibration_data(csv_file)

        if self.headers:
            self.scene.clear()
            self.rect_items = self.create_rectangles()
            self.current_row_index = 0
            self.display_row(0)

            # Initialiser le timer après le chargement des données
            if not hasattr(self, 'timer'):  # Vérifier si timer existe
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.next_line)
            
            self.timer.start(self.speed)
            self.is_playing = True
        else:
            print("⚠️ Erreur de lecture : les données n'ont pas été chargées correctement.")
    
    def load_calibration_data(self, csv_file):
        """Charge les données CSV et filtre les capteurs avec calibration à 1000."""
        try:
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = [row for row in reader if row]

                if len(rows) < 2:
                    return None, None, None

                headers = rows[0][1:34]
                base_values = rows[1][1:17]
                # 🔄 Réorganisation des colonnes 5 à 9
                # Ordre souhaité : 1, 2, 3, 4, 5, 9, 8, 7, 6, 10, 11, 12, 13, 14, 15, 16, 17

                # 1. Conserver les colonnes 1 à 4
                reorganized_values = base_values[:4]
                reorganized_headers = headers[:4]
                # 2. Inverser les colonnes 5 à 9
                reorganized_values += base_values[4:8][::-1]
                reorganized_headers += headers[4:8][::-1]
                # 3. Ajouter le reste normalement
                reorganized_values += base_values[8:]
                reorganized_headers += headers[8:]
                
                base_values = reorganized_values
                headers = reorganized_headers
                
                presence_rows = [list(map(int, row[17:34])) for row in rows[1:] if all(cell.isdigit() for cell in row[17:34])]

                filtered_headers = []
                valid_indices = []

                for i, value in enumerate(base_values):
                    if int(value) != 1000:
                        filtered_headers.append(headers[i])
                        valid_indices.append(i)

                data_rows = []
                filtered_presence_rows = []

                for row in rows[1:]:
                    try:
                        # 🔹 Extraction des valeurs numériques et de présence
                        numeric_row = [int(row[i + 1]) for i in valid_indices]
                        presence_row = [int(row[i + 17]) for i in valid_indices]

                        # 🔄 Réorganisation des colonnes 5 à 9
                        # Ordre souhaité : 1, 2, 3, 4, 5, 9, 8, 7, 6, 10, ...
                        # 1. Conserver les colonnes 1 à 4
                        reorganized_numeric = numeric_row[:4]
                        reorganized_presence = presence_row[:4]

                        # 2. Inverser les colonnes 5 à 9
                        reorganized_numeric += numeric_row[4:8][::-1]
                        reorganized_presence += presence_row[4:8][::-1]

                        # 3. Ajouter le reste normalement
                        reorganized_numeric += numeric_row[8:]
                        reorganized_presence += presence_row[8:]

                        # 🔄 Ajout des lignes réorganisées aux listes
                        data_rows.append(reorganized_numeric)
                        filtered_presence_rows.append(reorganized_presence)

                    except ValueError:
                        continue


                return filtered_headers, data_rows, filtered_presence_rows
        except Exception as e:
            print(f"⚠️ Erreur de lecture : {e}")
            return None, None, None

        

    def create_rectangles(self):
        """Crée les rectangles et ajuste leur placement si des capteurs supplémentaires sont détectés."""
        rect_items = []
        rect_width = 75
        rect_height = 150
        spacing = 20
        x_offset = 10
        y_offset = 50
        row_limit = 4
        count = 0

        # Vérifier si les 8 capteurs matriciels sont présents
        matrix_headers = [f"M_F_{i}" for i in range(1, 5)]+[f"M_F_{i}" for i in range(8, 4, -1)]
        has_matrix_sensors = all(sensor in self.headers for sensor in matrix_headers)
        #print(self.headers)
        #print(has_matrix_sensors)

        # Si 8 capteurs matriciels sont détectés, ajouter un fond gris
        if has_matrix_sensors:
            bg_width = (rect_width + spacing) * 4 + 50
            bg_height = (rect_height + spacing) * 2 + 50
            background_rect = QGraphicsRectItem(0, 20, bg_width, bg_height)
            background_rect.setBrush(QBrush(QColor(180, 180, 180)))  # Fond gris
            background_rect.setZValue(-1)  # Mettre le fond en arrière-plan
            self.scene.addItem(background_rect)
            bg_bottom = 20 + bg_height  # Calculer la position du bas du fond gris
        else:
            bg_bottom = 50  # Si pas de fond gris, on garde l'offset normal

        # Placement des capteurs
        for i, key in enumerate(self.headers):
            if count >= row_limit:
                x_offset = 10
                y_offset += rect_height + spacing
                count = 0

            # Si c'est un capteur supplémentaire, le placer 30px en dessous du fond
            if has_matrix_sensors and key not in matrix_headers:
                y_offset = bg_bottom + 30

            rect = QGraphicsRectItem(x_offset + 20, y_offset, rect_width, rect_height)
            rect.setBrush(QBrush(QColor(100, 200, 250)))  # Bleu par défaut
            rect.setPen(QPen(Qt.GlobalColor.transparent))  # Pas de bordure par défaut
            self.scene.addItem(rect)

            text = QGraphicsTextItem(key)
            text.setDefaultTextColor(Qt.GlobalColor.black)
            text.setPos(x_offset + rect_width / 2, y_offset + rect_height / 4)
            self.scene.addItem(text)

            value_text = QGraphicsTextItem("")
            value_text.setDefaultTextColor(Qt.GlobalColor.black)
            value_text.setPos(x_offset + 20 + rect_width / 4, y_offset + rect_height / 2)
            self.scene.addItem(value_text)

            presence_text = QGraphicsTextItem("")
            presence_text.setDefaultTextColor(Qt.GlobalColor.black)
            presence_text.setPos(x_offset + 30 + rect_width / 4, y_offset + 25 + rect_height / 2)
            self.scene.addItem(presence_text)

            rect_items.append((rect, text, value_text, presence_text))

            x_offset += rect_width + spacing
            count += 1

        return rect_items

    def display_row(self, row_index):
        """Met à jour les valeurs affichées dans les rectangles et ajoute un contour si présence détectée."""
        if row_index >= len(self.data_rows):
            self.timer.stop()
            return

        values = self.data_rows[row_index]
        presence_values = self.presence_rows[row_index]  # Les valeurs de présence associées aux colonnes filtrées

        for i, (rect, text, value_text, presence_text) in enumerate(self.rect_items):
            if i >= len(values):
                continue

            value_text.setPlainText(str(values[i]))
            presence_text.setPlainText(str(presence_values[i]))

            # Changer la couleur en fonction de la valeur
            color = self.get_color(values[i])
            rect.setBrush(QBrush(color))

            # Réduction de l'épaisseur de la bordure si presence détectée (5px au lieu de 8px)
            if presence_values[i] == 1:
                rect.setPen(QPen(QColor(0, 0, 255), 5))  # Bordure BLEUE de 5px d'épaisseur
                rect.setZValue(1)  # Mettre en avant le rectangle
            else:
                rect.setPen(QPen(Qt.GlobalColor.transparent))  # Pas de bordure

            value_text.setZValue(2)  # Garder le texte visible
            presence_text.setZValue(2)
            text.setZValue(2)

        self.iteration_label.setText(f"Itération: {row_index + 1}")





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


    def next_line(self):
        """Passe à la ligne suivante en fonction du sens de lecture."""
        if self.reverse_order:
            self.current_row_index -= 1
            if self.current_row_index < 0:
                self.current_row_index = len(self.data_rows) - 1  # Retour au dernier élément
        else:
            self.current_row_index += 1
            if self.current_row_index >= len(self.data_rows):
                self.current_row_index = 0  # Retour au début

        self.display_row(self.current_row_index)


    def prev_line(self):
        """Revient à la ligne précédente."""
        if self.current_row_index > 0:
            self.current_row_index -= 1
            self.display_row(self.current_row_index)

    def toggle_play_pause(self):
        """Joue ou met en pause la lecture."""
        if self.is_playing:
            self.timer.stop()
            self.play_pause_button.setText("▶ Play")
        else:
            self.timer.start(self.speed)
            self.play_pause_button.setText("⏸ Pause")

        self.is_playing = not self.is_playing

    def slow_down(self):
        """Ralentit la lecture."""
        self.speed = min(200, self.speed + 10)
        self.timer.setInterval(self.speed)
        self.speed_label.setText(f"Vitesse: {self.speed} ms")

    def speed_up(self):
        """Accélère la lecture."""
        self.speed = max(5, self.speed - 10)
        self.timer.setInterval(self.speed)
        self.speed_label.setText(f"Vitesse: {self.speed} ms")
        
    def toggle_direction(self):
        """Inverse le sens de lecture."""
        self.reverse_order = not self.reverse_order
        direction_text = "Lecture inversée" if self.reverse_order else "Lecture normale"
        self.reverse_button.setText(f"Inverser Lecture ({direction_text})")

        
    def toggle_graphics_fullscreen(self):
        """Bascule le QGraphicsView en mode plein écran ou normal."""
        if hasattr(self, 'fullscreen_window') and self.fullscreen_window.isVisible():
            # ⬅️ Sortie du mode plein écran
            
            # Fermer la fenêtre plein écran
            self.fullscreen_window.close()
            
            # Réintégrer le graphics_view à son index d'origine
            self.layout.insertWidget(self.original_index, self.view)
            
            # Réactiver les barres de défilement
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            self.fullscreen_button.setText("🖵 Plein écran")

        else:
            # 🔀 Passage en mode plein écran
            
            # Mémorisation de l'index d'origine du graphics_view
            self.original_index = self.layout.indexOf(self.view)
            
            # Retrait temporaire du graphics_view du layout
            self.layout.removeWidget(self.view)
            
            # Création de la fenêtre plein écran
            self.fullscreen_window = QMainWindow()
            self.fullscreen_window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.fullscreen_window.setWindowState(Qt.WindowFullScreen)
            self.fullscreen_window.setCentralWidget(self.view)
            
            # Désactiver les barres de défilement en plein écran
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # ⌨️ Ajout du raccourci Échap pour quitter le plein écran
            esc_shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self.fullscreen_window)
            esc_shortcut.activated.connect(self.toggle_graphics_fullscreen)
            
            self.fullscreen_window.show()
            self.fullscreen_button.setText("❌ Quitter plein écran")




    def update_button_position(self, event):
        """Met à jour la position du bouton plein écran lors du redimensionnement."""
        self.fullscreen_button.move(
            self.view.width() - self.fullscreen_button.width() - 20,
            self.view.height() - self.fullscreen_button.height() - 20
        )
        QGraphicsView.resizeEvent(self.view, event)
        
        
"""if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_path = os.path.join(os.path.dirname(__file__), "sensor_responses.csv")

    if os.path.exists(file_path):
        window = Rectangles(file_path)
        window.show()
        sys.exit(app.exec())
    else:
        print("⚠️ Fichier CSV introuvable !")"""