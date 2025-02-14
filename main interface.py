import sys
import os
from PySide6.QtWidgets import *
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QProcess
from rectangles import Rectangles  # Import direct au lieu d'utiliser subprocess
from app import CSVViewer
from Code_commande import SerialWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Interface projet nanomade")
        screen_geometry = QApplication.primaryScreen().geometry()

        self.resize(screen_geometry.width(), screen_geometry.height()-80)  # Adapte à toute la taille de l'écran
        self.move(0, 0)  # Place la fenêtre en haut à gauche

        # Palette de couleurs sombre
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(40, 40, 40))  # Fond sombre
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # Texte clair
        #dark_palette.setColor(QPalette.Base, QColor(55, 55, 55))  # Zone de texte sombre
        dark_palette.setColor(QPalette.AlternateBase, QColor(70, 70, 70))  # Arrière-plan alterné
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))  # Texte info tooltip clair
        dark_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))  # Texte tooltip sombre
        dark_palette.setColor(QPalette.Button, QColor(60, 60, 60))  # Boutons gris foncé
        #dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # Texte des boutons clair
        dark_palette.setColor(QPalette.Link, QColor(0, 162, 232))  # Liens en bleu clair
        QApplication.setPalette(dark_palette)

        # Widget principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal
        self.main_layout = QHBoxLayout(self.central_widget)

        # Création du menu latéral
        self.menu_widget = QFrame()
        self.menu_widget.setStyleSheet("""
            background-color: #2c3e50; 
            border-right: 2px solid #34495e;
        """)
        self.menu_width = int(self.width() * 0.25)  # 25% de la largeur de la fenêtre
        self.menu_widget.setFixedWidth(self.menu_width)
        self.menu_layout = QVBoxLayout(self.menu_widget)

        # Bouton pour afficher/masquer le menu
        self.toggle_button = QPushButton("☰")
        self.toggle_button.setFixedSize(QSize(40, 40))
        self.toggle_button.setStyleSheet("""
            background-color: #34495e; 
            color: white; 
            font-size: 20px;
            border-radius: 5px;
        """)
        self.toggle_button.clicked.connect(self.toggle_menu)

        # Boutons du menu
        self.btn_home = QPushButton("Accueil")
        self.btn_command= QPushButton ("Acquisition de données")
        self.btn_rectangle = QPushButton("Visualisation de données")
        self.btn_csv_viz = QPushButton("Visualisation de csv")
        self.btn_settings = QPushButton("Paramètres")

        # Style des boutons
        self.button_style = """
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
        """

        # Appliquer le style aux boutons
        for btn in [self.btn_home, self.btn_command, self.btn_rectangle, self.btn_csv_viz, self.btn_settings]:
            btn.setFixedHeight(40)
            btn.setStyleSheet(self.button_style)
            self.menu_layout.addWidget(btn)

        self.menu_layout.addStretch()

        # Ajouter le menu à la fenêtre
        self.main_layout.addWidget(self.menu_widget)
        self.main_layout.addWidget(self.toggle_button, alignment=Qt.AlignmentFlag.AlignTop)

        # Zone centrale unique
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.main_layout.addWidget(self.content_area)

        # Zone d'affichage des logs du programme
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("""
            background-color: #2c3e50;
            color: #ecf0f1;
            font-size: 14px;
            border: 1px solid #34495e;
            border-radius: 5px;
            padding: 10px;
        """)
        self.content_layout.addWidget(self.output_display)

        # Animation du menu
        self.animation = QPropertyAnimation(self.menu_widget, b"minimumWidth")
        self.animation.setDuration(300)
        self.is_menu_visible = True

        # Connexions des boutons
        self.btn_home.clicked.connect(self.reset_page)  # Connexion du bouton Accueil
        self.btn_command.clicked.connect(self.launch_live_command)
        self.btn_rectangle.clicked.connect(self.launch_rectangle)
        self.btn_csv_viz.clicked.connect(self.launch_csv)

        # Processus
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.update_output)
        self.process.readyReadStandardError.connect(self.update_output)

    def toggle_menu(self):
        menu_width = int(self.width() * 0.25)  # 25% de la largeur de la fenêtre
        if self.is_menu_visible:
            self.animation.setStartValue(menu_width)
            self.animation.setEndValue(0)
            self.animation.start()
            self.animation.finished.connect(self.hide_menu_once)
        else:
            self.menu_widget.setVisible(True)
            self.animation.setStartValue(0)
            self.animation.setEndValue(menu_width)
            self.animation.start()
        self.is_menu_visible = not self.is_menu_visible

    def hide_menu_once(self):
        if not self.is_menu_visible:
            self.menu_widget.setVisible(False)
        self.animation.finished.disconnect(self.hide_menu_once)  # Empêcher l'exécution répétée

    def launch_rectangle(self):
        self.clear_content()  # Supprime le contenu précédent

        # Supprimer output_display si il est déjà présent
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget == self.output_display:
                widget.hide()  # Cache output_display
                widget.lower()  # Le met en arrière-plan
                
        file_path = "sensor_responses.csv"  # Chemin vers le fichier CSV

        if os.path.exists(file_path):
            self.rectangles_widget = Rectangles(file_path)  # Instancie la classe Rectangles
            self.content_layout.addWidget(self.rectangles_widget)  # L'ajoute à la zone centrale
        else:
            self.content_layout.addWidget(QLabel("⚠️ Fichier CSV introuvable !"))

    def launch_csv(self):
        self.clear_content()  # Supprime le contenu précédent

        # Supprimer output_display si il est déjà présent
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget == self.output_display:
                widget.hide()  # Cache output_display
                widget.lower()  # Le met en arrière-plan
        
        file_path = "sensor_responses.csv"  

        if os.path.exists(file_path):
            self.csv_widget = CSVViewer(file_path)  # On utilise CSVViewer au lieu de MainWindow
            self.content_layout.addWidget(self.csv_widget)  
        else:
            self.content_layout.addWidget(QLabel("⚠️ Fichier CSV introuvable !"))
            
            
    def launch_live_command(self):
            self.clear_content()  # Supprime le contenu précédent

            # Supprimer output_display si il est déjà présent
            for i in reversed(range(self.content_layout.count())):
                widget = self.content_layout.itemAt(i).widget()
                if widget == self.output_display:
                    widget.hide()  # Cache output_display
                    widget.lower()  # Le met en arrière-plan
            
            """Lance l'interface de communication série."""
            self.clear_content()  # Supprime le contenu précédent

            # Création du widget série
            self.serial_widget = SerialWidget()
            self.content_layout.addWidget(self.serial_widget)  # L'ajoute à la zone centrale
            

    def reset_page(self):
        """Réinitialiser l'interface et revenir à l'état initial (accueil)."""
        self.clear_content()  # Supprimer tout le contenu précédent
        self.content_layout.addWidget(self.output_display)  # Réafficher output_display

    def update_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()
        if output:
            self.output_display.append(output)
        if error:
            self.output_display.append(f"<span style='color:red;'>{error}</span>")

    def clear_content(self):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
