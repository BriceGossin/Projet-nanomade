import sys
import os
import csv
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFileDialog, QListWidget
)

class CSVViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Visualisation de CSV")
        self.setGeometry(100, 100, 800, 600)

        # Layout principal
        layout = QVBoxLayout()

        # Bouton pour sélectionner un fichier CSV
        self.select_file_button = QPushButton("🔍 Rechercher un fichier CSV")
        self.select_file_button.setStyleSheet("background-color: #007BFF; color: white; font-weight: bold; padding: 5px; border-radius: 5px;")
        self.select_file_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.select_file_button)

        # Label pour afficher le fichier sélectionné
        self.label = QLabel("📂 Sélectionnez un fichier CSV")
        layout.addWidget(self.label)

        # Liste des fichiers CSV disponibles dans le répertoire courant
        self.suggestions_list = QListWidget()
        self.suggestions_list.itemClicked.connect(self.load_selected_csv)
        layout.addWidget(self.suggestions_list)
        self.populate_suggestions()

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
        """Liste les fichiers CSV dans le répertoire courant et les affiche en suggestions."""
        self.suggestions_list.clear()
        csv_files = [f for f in os.listdir() if f.endswith(".csv")]
        if csv_files:
            self.suggestions_list.addItems(csv_files)
        else:
            self.suggestions_list.addItem("⚠️ Aucun fichier CSV trouvé")

    def load_selected_csv(self, item):
        """Charge le fichier sélectionné dans la liste."""
        file_name = item.text()
        if file_name.startswith("⚠️"):
            return  # Éviter de charger un message d'erreur

        file_path = os.path.abspath(file_name)
        self.label.setText(f"📄 Fichier sélectionné : {file_name}")
        self.load_csv(file_path)

    def load_csv(self, filename):
        """Charge le contenu du CSV dans la table avec des colonnes plus larges."""
        try:
            with open(filename, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                data = list(reader)

                if data:
                    self.tableWidget.setRowCount(len(data))
                    self.tableWidget.setColumnCount(len(data[0]))

                    for row_idx, row in enumerate(data):
                        for col_idx, cell in enumerate(row):
                            self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(cell))

                    # 🔹 Ajuste la largeur des colonnes à 150 pixels
                    for col in range(self.tableWidget.columnCount()):
                        self.tableWidget.setColumnWidth(col, 75)
                    
                    self.tableWidget.setColumnWidth(0, 150)  # Ajuste la première colonne à 200 pixels

                    # 🔹 Permet d'étirer la dernière colonne pour un affichage optimal
                    self.tableWidget.horizontalHeader().setStretchLastSection(True)

        except Exception as e:
            self.label.setText(f"🚨 Erreur : {e}")

