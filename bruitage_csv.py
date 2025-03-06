import os
import numpy as np
import pandas as pd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QSlider, QComboBox
from PyQt6.QtCore import Qt 




class NoiseAdderApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Ajout de bruit aux fichiers CSV")
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        # Bouton pour choisir le dossier source
        self.btn_select_input = QPushButton("Sélectionner le dossier source", self)
        self.btn_select_input.clicked.connect(self.select_input_folder)
        layout.addWidget(self.btn_select_input)

        # Label pour afficher le dossier source sélectionné
        self.label_input_folder = QLabel("Dossier source : Non sélectionné")
        layout.addWidget(self.label_input_folder)

        # Bouton pour choisir le dossier de sortie
        self.btn_select_output = QPushButton("Sélectionner le dossier de sortie", self)
        self.btn_select_output.clicked.connect(self.select_output_folder)
        layout.addWidget(self.btn_select_output)

        # Label pour afficher le dossier de sortie sélectionné
        self.label_output_folder = QLabel("Dossier de sortie : Non sélectionné")
        layout.addWidget(self.label_output_folder)

        # Sélecteur du type de bruit
        self.noise_type_selector = QComboBox(self)
        self.noise_type_selector.addItems(["gaussian", "uniform"])
        layout.addWidget(self.noise_type_selector)

        # Slider pour ajuster le niveau de bruit
        self.noise_level_slider = QSlider()
        self.noise_level_slider.setMinimum(1)
        self.noise_level_slider.setMaximum(20)
        self.noise_level_slider.setValue(5)
        self.noise_level_slider.setOrientation(Qt.Orientation.Horizontal)
        layout.addWidget(QLabel("Niveau de bruit :"))
        layout.addWidget(self.noise_level_slider)

        # Bouton pour démarrer le bruitage
        self.btn_process = QPushButton("Lancer le bruitage", self)
        self.btn_process.clicked.connect(self.process_files)
        layout.addWidget(self.btn_process)

        self.setLayout(layout)

        self.input_folder = None
        self.output_folder = None

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier source")
        if folder:
            self.input_folder = folder
            self.label_input_folder.setText(f"Dossier source : {folder}")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de sortie")
        if folder:
            self.output_folder = folder
            self.label_output_folder.setText(f"Dossier de sortie : {folder}")

    def add_noise(data, noise_level, noise_type="gaussian"):
        """Ajoute du bruit aux données numériques uniquement."""
        
        # Convertir en float, en ignorant les erreurs pour éviter les valeurs non numériques
        data_numeric = pd.to_numeric(data, errors='coerce')

        # Vérifier que la colonne contient bien des nombres (NaN signifie qu'il y avait du texte)
        if data_numeric.isna().all():
            return data  # Si toute la colonne est du texte, on la garde inchangée

        # Générer du bruit selon le type choisi
        if noise_type == "gaussian":
            noise = np.random.normal(loc=0, scale=noise_level, size=data_numeric.shape)
        elif noise_type == "uniform":
            noise = np.random.uniform(low=-noise_level, high=noise_level, size=data_numeric.shape)
        else:
            raise ValueError("Type de bruit inconnu. Choisissez 'gaussian' ou 'uniform'.")

        # Ajouter le bruit aux données numériques uniquement
        return np.where(data_numeric.notna(), data_numeric + noise, data)
    
    def process_files(self):
        """Charge les fichiers CSV, applique du bruit et sauvegarde les nouvelles versions."""

        noise_level = self.noise_level_slider.value() / 100  # Niveau de bruit normalisé
        noise_type = self.noise_type_combo.currentText().lower()

        for file_path in self.files:
            df = pd.read_csv(file_path, delimiter=",", header=None)

            # Filtrer les colonnes contenant des nombres uniquement
            df_numeric = df.apply(pd.to_numeric, errors='coerce')

            # Appliquer le bruit uniquement sur les colonnes numériques
            noisy_data = df_numeric.apply(lambda col: add_noise(col, noise_level, noise_type) if col.notna().any() else col)

            # Sauvegarder en CSV
            noisy_file_path = file_path.replace(".csv", "_noisy.csv")
            noisy_data.to_csv(noisy_file_path, index=False, header=False)


if __name__ == "__main__":
    app = QApplication([])
    window = NoiseAdderApp()
    window.show()
    app.exec()
