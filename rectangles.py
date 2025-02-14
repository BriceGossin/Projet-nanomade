import sys
import csv
import os
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QGraphicsScene, QGraphicsView,
    QGraphicsRectItem, QGraphicsTextItem, QLabel, QVBoxLayout, QWidget,
    QPushButton, QHBoxLayout
)
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtCore import Qt, QTimer


class Rectangles(QWidget):
    def __init__(self, csv_file):
        super().__init__()

        self.setWindowTitle("Calibration Viewer")
        self.setGeometry(100, 100, 800, 500)

        # Layout principal
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)
        #self.setCentralWidget(self.main_widget)
        self.setLayout(self.layout)


        # Scène graphique
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.layout.addWidget(self.view)

        # Labels
        self.iteration_label = QLabel("Itération: 0")
        self.layout.addWidget(self.iteration_label)

        self.speed_label = QLabel("Vitesse: 20 ms")
        self.layout.addWidget(self.speed_label)

        # Boutons de contrôle
        self.button_layout = QHBoxLayout()
        self.play_pause_button = QPushButton("▶ Play")
        self.slower_button = QPushButton("🐢 Ralentir")
        self.faster_button = QPushButton("⚡ Accélérer")
        self.prev_button = QPushButton("⬅ Précédent")
        self.next_button = QPushButton("➡ Suivant")
        self.reverse_button = QPushButton("Inverser lecture", self)
        self.reverse_button.clicked.connect(self.toggle_direction)

        self.button_layout.addWidget(self.prev_button)
        self.button_layout.addWidget(self.play_pause_button)
        self.button_layout.addWidget(self.next_button)
        self.button_layout.addWidget(self.slower_button)
        self.button_layout.addWidget(self.faster_button)
        self.button_layout.addWidget(self.reverse_button)

        self.layout.addLayout(self.button_layout)

        # Charger les données CSV
        self.csv_file = csv_file
        self.headers, self.data_rows, self.presence_rows = self.load_calibration_data(csv_file)

        
        if self.headers:
            self.rect_items = self.create_rectangles()
            self.current_row_index = 0
            self.reverse_order = False #Pour inverser l'ordre de lecture
            self.display_row(0)

            # Timer pour lecture automatique
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next_line)
            self.speed = 20  # Intervalle initial: 20ms
            self.is_playing = True
            self.timer.start(self.speed)

        # Connexions des boutons
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.slower_button.clicked.connect(self.slow_down)
        self.faster_button.clicked.connect(self.speed_up)
        self.prev_button.clicked.connect(self.prev_line)
        self.next_button.clicked.connect(self.next_line)

    def load_calibration_data(self, csv_file):
        """Charge les données en liant correctement les colonnes filtrées avec leurs valeurs de présence."""
        try:
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.reader(file) 
                rows = [row for row in reader if row]  # Filtrer les lignes vides

                if len(rows) < 2:
                    print("⚠️ Le fichier CSV ne contient pas assez de lignes.")
                    return None, None, None

                headers = rows[0][1:34]  # Ignorer la première colonne (timestamps)
                base_values = rows[1][1:17]  # Valeurs de calibration
                presence_rows = [list(map(int, row[17:34])) for row in rows[1:] if all(cell.isdigit() for cell in row[17:34])]
                
                # Filtrer les colonnes avec calibration à 1000
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
                        numeric_row = [int(row[i + 1]) for i in valid_indices]  # +1 pour ignorer la première colonne
                        presence_row = [int(row[i + 17]) for i in valid_indices]  # +17 pour aller chercher la bonne colonne de présence
                        data_rows.append(numeric_row)
                        filtered_presence_rows.append(presence_row)
                    except ValueError:
                        continue  # Ignorer les lignes contenant du texte

                return filtered_headers, data_rows, filtered_presence_rows
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture du fichier CSV: {e}")
            return None, None, None


        

    def create_rectangles(self):
        """Crée les rectangles et les stocke pour mise à jour dynamique."""
        rect_items = []
        rect_width = 75
        rect_height = 150
        spacing = 20
        x_offset = 10
        y_offset = 50
        row_limit = 4
        count = 0

        for key in self.headers:
            if count >= row_limit:
                x_offset = 10
                y_offset += rect_height + spacing
                count = 0

            rect = QGraphicsRectItem(x_offset + 20, y_offset, rect_width, rect_height)
            rect.setBrush(QBrush(QColor(100, 200, 250)))  # Bleu par défaut
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

            rect_items.append((rect, text, value_text, presence_text))  # Ajout de presence_text

            x_offset += rect_width + spacing
            count += 1

        return rect_items

    def display_row(self, row_index):
        """Met à jour les valeurs affichées dans les rectangles et ajoute un contour si présence détectée (1)."""
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

            # Changer la couleur en fonction de la valeur (1650 = vert, 1750 = rouge)
            color = self.get_color(values[i])
            rect.setBrush(QBrush(color))

            # 🔵 Ajout d'un contour BLEU ÉPAIS si presence_values[i] == 1
            if presence_values[i] == 1:
                rect.setPen(QPen(QColor(0, 0, 255), 6))  # Bordure BLEUE de 6px d'épaisseur
                rect.setZValue(1)  # Mettre en avant le rectangle
            else:
                rect.setPen(QPen(Qt.GlobalColor.transparent))  # Pas de bordure

            # 🔄 Corriger le problème des valeurs qui disparaissent :
            value_text.setZValue(2)  # Le texte est toujours au premier plan
            presence_text.setZValue(2)
            text.setZValue(2)

        self.iteration_label.setText(f"Itération: {row_index + 1}")


    def get_color(self, value):
        """Définit une couleur en fonction de la valeur (1650 = vert, 1700 = orange, 1750 = rouge)."""
        min_value, mid_value, max_value = 1650, 1700, 1750
        value = max(min_value, min(max_value, value))  # Clamp entre 1650 et 1750

        if value <= mid_value:  # Transition vert → orange
            ratio = (value - min_value) / (mid_value - min_value)
            red = int(255 * ratio)
            green = 255  # Vert reste à 255 jusqu'à mi-chemin
        else:  # Transition orange → rouge
            ratio = (value - mid_value) / (max_value - mid_value)
            red = 255
            green = int(255 * (1 - ratio))  # Le vert diminue progressivement

        return QColor(red, green, 0)  # Code couleur en RGB


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

"""if __name__ == "__main__":
    app = QApplication(sys.argv)
    file_path = os.path.join(os.path.dirname(__file__), "sensor_responses.csv")

    if os.path.exists(file_path):
        window = Rectangles(file_path)
        window.show()
        sys.exit(app.exec())
    else:
        print("⚠️ Fichier CSV introuvable !")"""
