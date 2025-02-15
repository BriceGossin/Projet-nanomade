import sys
import os
import csv
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

class CSVViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Visualisation de CSV")
        self.setGeometry(100, 100, 800, 600)

        # Layout principal
        layout = QVBoxLayout()

        # Zone de sélection (bouton + menu déroulant)
        selection_layout = QHBoxLayout()
                
         # Label pour afficher le fichier sélectionné
        self.label = QLabel("📂 Sélectionnez un fichier CSV")
        self.label.setStyleSheet("font-size : 16px;")
        
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
        layout.addLayout(selection_layout)
        
        # Label "Suggestions"
        self.suggestions_label = QLabel("📌 Suggestions :")
        self.suggestions_label.setStyleSheet("font-size: 12px;")
        #self.suggestions_label.setStyleSheet("QToolTip { color: black; background-color: #FFFFE0; border: 1px solid black; }")
        #self.suggestions_label.setToolTip("Les fichiers listés ici sont les CSV présents dans le répertoire courant.")
        #self.suggestions_label.setContentsMargins(350, 0, 0, 0) 
        layout.addWidget(self.suggestions_label, alignment=Qt.AlignLeft)

        
        # Liste des fichiers CSV disponibles dans le répertoire courant (plus basse et moins longue)
        self.suggestions_list = QListWidget()
        self.suggestions_list.setFixedHeight(100)  # Hauteur légèrement réduite
        
        # Ajustement de la largeur pour s'étendre avec la fenêtre
        self.suggestions_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.suggestions_list.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 5px; padding: 5px;"
            "background-color: #f9f9f9; font-size: 14px;"
        )
        self.suggestions_list.setToolTip("Cliquez sur un fichier pour l'afficher.")
        self.suggestions_list.itemClicked.connect(self.load_selected_csv)

        # Ajout de la liste avec un stretch pour s'adapter à l'espace
        layout.addWidget(self.suggestions_list, stretch=0)

        self.populate_suggestions()


        
        
        # Menu déroulant pour naviguer dans les séries du CSV
        self.label_series = QLabel("Sélectionnez une série de données dans le fichier : ")
        self.suggestions_label.setStyleSheet("font-size: 14px; color : white")
        layout.addWidget(self.label_series, alignment=Qt.AlignCenter)
        
        self.series_dropdown = QComboBox()
        self.series_dropdown.setFixedSize(200, 30)
        self.series_dropdown.setStyleSheet("border-radius: 5px; padding: 3px;")
        #self.series_dropdown.setToolTip("Sélectionnez une série de données dans le fichier CSV.")
        self.series_dropdown.currentIndexChanged.connect(self.load_selected_series)
        layout.addWidget(self.series_dropdown, alignment=Qt.AlignCenter)

        
        
        # Table pour afficher le contenu du CSV
        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)

        self.setLayout(layout)

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
        """Charge le fichier sélectionné dans la liste."""
        file_name = item.text().replace("📄 ", "")  # Retire l'icône devant
        if file_name.startswith("⚠️"):
            return  # Éviter de charger un message d'erreur

        file_path = os.path.abspath(file_name)
        self.label.setText(f"📄 Fichier sélectionné : {file_name}")
        self.load_csv(file_path)

    
    def load_csv(self, filename):
        """Charge le contenu du CSV dans la table avec des colonnes ajustées."""
        self.current_file = filename
        self.series_dropdown.clear()
        self.series_data = []

        try:
            with open(filename, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                data = list(reader)

                # Ajoute l'option "Fichier entier" dans le menu déroulant
                self.series_dropdown.addItem("Fichier entier")

                # Détection des séries en cherchant les lignes de calibration
                current_series = []
                previous_row = None  # Variable pour garder la ligne précédente
                 # Liste des en-têtes à ignorer (basée sur les noms des colonnes)
                headers = ["Timestamp", "M_F_1", "M_F_2", "M_F_3", "M_F_4", "M_F_5", "M_F_6", "M_F_7", "M_F_8", 
                       "U_F_1", "U_F_2", "U_F_3", "U_F_4", "U_F_5", "U_F_6", "U_F_7", "U_F_8", 
                       "M_C_1", "M_C_2", "M_C_3", "M_C_4", "M_C_5", "M_C_6", "M_C_7", "M_C_8", 
                       "U_C_1", "U_C_2", "U_C_3", "U_C_4", "U_C_5", "U_C_6", "U_C_7", "U_C_8"]
                for row in data:
                    # Ignore les lignes d'en-têtes (lignes avec les noms des colonnes)
                    if row and row[0] in headers:
                        continue

                    # Si une ligne contient des mots-clés 'ADC', 'GAIN', etc. et qu'il y a une ligne précédente (calibration)
                    if len(row) > 4 and any(val.isalpha() for val in row[1:5]):  # Vérifie si c'est une ligne de texte
                        # Si une série est déjà en cours et que la ligne contient des données de calibration
                        if previous_row:  # Ajouter la ligne de calibration à la série
                            current_series.insert(0, previous_row)  # Ajouter au début de la série
                        if current_series:
                            self.series_data.append(current_series)
                        current_series = []

                    current_series.append(row)
                    previous_row = row  # Sauvegarder la ligne actuelle comme la précédente

                # Ajouter la dernière série (si elle existe)
                if previous_row:  # Pour s'assurer que la dernière ligne de calibration est bien ajoutée
                    current_series.insert(0, previous_row)
                if current_series:
                    self.series_data.append(current_series)

                # Ajouter les séries détectées au menu déroulant
                for i in range(len(self.series_data)):
                    self.series_dropdown.addItem(f"Série {i+1}")

                # Charger par défaut "Fichier entier"
                self.load_selected_series(0)  # Le fichier entier (index 0) est affiché par défaut

                # Afficher l'intégralité du fichier dans la table
                if data:
                    self.tableWidget.setRowCount(len(data))
                    self.tableWidget.setColumnCount(len(data[0]))

                    for row_idx, row in enumerate(data):
                        for col_idx, cell in enumerate(row):
                            self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(cell))

                    # Ajuste la largeur des colonnes
                    for col in range(self.tableWidget.columnCount()):
                        self.tableWidget.setColumnWidth(col, 75)

                    # Ajuste la première colonne à 150 pixels
                    self.tableWidget.setColumnWidth(0, 150)

                    # Permet d'étirer la dernière colonne pour un affichage optimal
                    self.tableWidget.horizontalHeader().setStretchLastSection(True)

        except Exception as e:
            self.label.setText(f"🚨 Erreur : {e}")

        
        

    def load_selected_series(self, index):
        """Affiche la série de données sélectionnée dans la table."""
        if not self.series_data or index < 0 or index >= len(self.series_data):
            return

        series = self.series_data[index]
        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(series))
        self.tableWidget.setColumnCount(len(series[0]))

        for row_idx, row in enumerate(series):
            for col_idx, cell in enumerate(row):
                self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(cell))

        self.tableWidget.setColumnWidth(0, 150)  # Ajuste la première colonne
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

