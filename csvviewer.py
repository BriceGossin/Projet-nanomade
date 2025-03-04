import sys
import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from datetime import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

class CSVViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Visualisation de CSV")
        self.setGeometry(100, 100, 800, 600)

        self.show_graph = False  # Indique si l'affichage actuel est un graphe
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
        
        self.graph_or_csv_btn = QPushButton("Graphe")
        self.graph_or_csv_btn.setFixedSize(120, 30)
        self.graph_or_csv_btn.setStyleSheet(
            "background-color: #6B5; color: white; font-weight: bold; border-radius: 5px; padding: 3px;"
        )
        self.graph_or_csv_btn.clicked.connect(self.toggle_graph_view)
        layout.addWidget(self.graph_or_csv_btn, alignment=Qt.AlignCenter)

        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)

        # 📊 Widget pour afficher le graphe
        self.graphWidget = QWidget()
        self.graphLayout = QVBoxLayout(self.graphWidget)
        self.canvas = FigureCanvas(plt.figure())  # Création d'un canvas pour Matplotlib
        self.graphLayout.addWidget(self.canvas)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        


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
        """Charge le CSV et segmente en séries de données correctement, avec date/heure dans les titres."""
        self.current_file = filename
        self.series_dropdown.clear()
        self.series_data = []
        self.global_headers = []  # Stocker les en-têtes du CSV

        try:
            with open(filename, newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                data = list(reader)

                if not data:
                    return

                # Stocker la première ligne comme en-têtes
                self.global_headers = data[0]  
                data = data[1:]  # Supprimer la première ligne des données

                self.series_dropdown.addItem("Fichier entier")
                self.series_data.append(data)

                current_series = []
                collecting = False
                series_titles = []

                for i, row in enumerate(data):
                    if not row:
                        continue  

                    is_calibration = all(cell.replace('.', '', 1).isdigit() if cell else True for cell in row[1:])
                    is_gain = any(key in row for key in ["ADC", "GAIN", "VALUE"])
                    is_threshold = any(key in row for key in ["CAPA", "THRESHOLD"])

                    if is_calibration and i < len(data) - 2:
                        next_row = data[i + 1]
                        next_next_row = data[i + 2]

                        is_next_gain = any(key in next_row for key in ["ADC", "GAIN", "VALUE"])
                        is_next_threshold = any(key in next_next_row for key in ["CAPA", "THRESHOLD"])

                        if is_next_gain and is_next_threshold:
                            # ✅ Fermer la série précédente avant d'en commencer une nouvelle
                            if collecting and current_series:
                                self.series_data.append(current_series)
                                series_titles.append(self.extract_timestamp(current_series[0]))
                            
                            # ✅ Réinitialiser la série et collecter la calibration
                            current_series = [row, next_row, next_next_row]
                            collecting = True
                            continue  

                    if collecting:
                        current_series.append(row)  

                # ✅ Ajouter la dernière série détectée
                if collecting and current_series:
                    self.series_data.append(current_series)
                    series_titles.append(self.extract_timestamp(current_series[0]))

                for i, title in enumerate(series_titles):
                    self.series_dropdown.addItem(f"Série {i+1} : {title}")

                self.load_selected_series(0)

        except Exception as e:
            self.label.setText(f"🚨 Erreur : {e}")




    def extract_timestamp(self, row):
        """Extrait la date et l'heure du premier timestamp et les formate en 'JJ/MM HHhMM'."""
        try:
            timestamp = row[0]  # Le timestamp est dans la première colonne
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S,%f")  # Convertir en objet datetime
            return dt.strftime("%d/%m %Hh%M")  # Format : 24/04 19h35
        except Exception:
            return "??/?? ??:??"  # Si problème, affiche un placeholder





        
        

    def load_selected_series(self, index):
        """Affiche la série de données sélectionnée dans la table en utilisant les en-têtes globales."""
        if not self.series_data or index < 0 or index >= len(self.series_data):
            return

        series = self.series_data[index]
        
        if not series:
            return

        # Utiliser les en-têtes globales
        headers = self.global_headers  
        data_rows = series  # Garde toutes les lignes (pas d'en-têtes à retirer ici)

        self.tableWidget.clear()
        self.tableWidget.setRowCount(len(data_rows))
        self.tableWidget.setColumnCount(len(headers))

        self.tableWidget.setHorizontalHeaderLabels(headers)  

        for row_idx, row in enumerate(data_rows):
            for col_idx, cell in enumerate(row):
                self.tableWidget.setItem(row_idx, col_idx, QTableWidgetItem(cell))

        self.tableWidget.setColumnWidth(0, 150)  
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        
        
    def plot_graph(self):
        """Affiche un graphe de la série sélectionnée dans le widget de l'interface"""
        if not hasattr(self, "current_file") or not self.current_file:
            QMessageBox.warning(self, "Avertissement", "Aucun fichier CSV sélectionné.")
            return

        try:
            df = pd.read_csv(self.current_file, on_bad_lines='skip')

            if df.empty:
                QMessageBox.warning(self, "Erreur", "Le fichier CSV est vide ou corrompu.")
                return

            if 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d %H:%M:%S,%f', errors='coerce')
                df = df.dropna()


            colonnes_a_garder = []
            for col in df.columns[1:17]:
                premiere_valeur = df[col].iloc[0]
                if premiere_valeur != 1000 and any(df[col] != 3299):
                    colonnes_a_garder.append(col)
                    
            df_filtre = df[['Timestamp'] + colonnes_a_garder]
            
            #Supprimer les valeurs de calibration
            index_fin_calibration = 0
            if df.isna().any().any():  # Vérifie s'il y a des NaN
                index_fin_calibration = df.dropna().index[0]  # Premier index non-NaN
                df_filtre = df_filtre.iloc[index_fin_calibration:]


            


            # Effacer le graphique précédent
            self.canvas.figure.clear()

            # Tracer le nouveau graphique
            ax = self.canvas.figure.add_subplot(111)
            for col in colonnes_a_garder:
                ax.plot(df_filtre['Timestamp'], df_filtre[col], label=col)

            ax.set_xlabel("Temps")
            ax.set_ylabel("Valeurs")
            ax.set_title(f"Évolution des valeurs - {os.path.basename(self.current_file)}")
            ax.legend()
            ax.grid(True)
            
            
            ax.set_ylim(1400, 2100)
            ax.set_yticks(range(1400, 2100, 100))  # Affiche les valeurs de 1500 à 2000 avec un pas de 100
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: int(x)))  # Force l'affichage des valeurs en y 

            self.canvas.draw()  # Mettre à jour l'affichage

        except Exception as e:
            print(self, "Erreur", f"Une erreur est survenue : {e}")


    def toggle_graph_view(self):
        """Bascule entre l'affichage du tableau et du graphe."""
        self.show_graph = not self.show_graph
        if self.show_graph:
            self.layout().replaceWidget(self.tableWidget, self.graphWidget)
            self.tableWidget.hide()
            self.graphWidget.show()
            self.graph_or_csv_btn.setText("Tableau")
            self.plot_graph()
            
            self.layout().addWidget(self.toolbar) #On ajoute la barre d'outils de matplotlib
        else:
            self.layout().replaceWidget(self.graphWidget, self.tableWidget)
            self.graphWidget.hide()
            self.tableWidget.show()
            self.graph_or_csv_btn.setText("Graphe")
            
            self.layout().removeWidget(self.toolbar) #On l'enlève en mode tableau
            #self.toolbar.deleteLater()

            
            



