from PySide6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy
from PySide6.QtGui import QPixmap, QDesktopServices
from PySide6.QtCore import Qt, QUrl
import os

class Accueil(QWidget):
    def __init__(self):
        super().__init__()

        # --- Texte avec liens ---
        self.label_text = QLabel(
            '<h1>Interface projet Nanomade</h1>'
            '<p>&nbsp;</p>'
            '<p>Ce projet a été réalisé à l\'aide du kit Touch and Force de <b>Nanomade</b>, '
            'trouvable à cette adresse : <a href="https://www.nanomade.com/fr/produit/demo-kit-touchforce/">Site officiel de Nanomade</a>.</p>'
            '<p>&nbsp;</p>'
            '<p>L\'installation d\'un pilote est nécessaire pour la prise en main des capteurs. <br>'
            'Vous le trouverez avec son protocole d\'installation dans ce document : '
            '<a href="open_driver">Installation du driver</a>.</p>'  
            '<p>Vous pourrez trouver ici des informations sur les commandes utilisées par le capteur : '
            '<a href="open_commandes">Commandes</a>.</p>'
            '<p>Pour plus de détails, vous pouvez vous référer au <a href="open_manuel">Manuel utilisateur</a> ainsi qu\'à la '
            '<a href="open_datasheet">Datasheet</a>.</p>'
            '<p>&nbsp;</p>'
            '<p>Cliquez sur <b>Acquisition de données</b> pour utiliser les capteurs et en recueillir des données.</p>'
            '<p>Cliquez sur <b>Visualisation de données</b> pour revoir une acquisition et y naviguer.</p>'
            '<p>Cliquez sur <b>Visualisation de csv</b> pour voir le contenu d\'une acquisition sous forme de tableau ou de graphe.</p>'
            '<p>&nbsp;</p>'
        )
        self.label_text.setOpenExternalLinks(False)  # Désactive les liens automatiques pour qu'on les gère nous-mêmes
        self.label_text.linkActivated.connect(self.open_document)  # Connecte tous les liens à la fonction unique

        self.label_text.setStyleSheet("font-size: 15px;")
        self.label_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # --- Images en haut à droite ---
        self.univ_label = QLabel(self)
        pixmap_univ = QPixmap(r"Images/Universite_Orleans.png")  
        self.univ_label.setPixmap(pixmap_univ)
        self.univ_label.setScaledContents(True)
        self.univ_label.setMaximumSize(150, 100) 
        
        self.polytech_label = QLabel(self)
        pixmap_polytech = QPixmap(r"Images/cropped-logo_reseau_Polytech.png")  
        self.polytech_label.setPixmap(pixmap_polytech)
        self.polytech_label.setScaledContents(True)
        self.polytech_label.setMaximumSize(150, 100)

        # --- Layout pour les images (aligné à droite) ---
        image_layout = QHBoxLayout()
        image_layout.addStretch()
        image_layout.addWidget(self.polytech_label)
        image_layout.addWidget(self.univ_label)

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(image_layout)  
        main_layout.addWidget(self.label_text, alignment=Qt.AlignLeft)  
        main_layout.addStretch()  

        self.setLayout(main_layout)

    def open_document(self, link):
        """Ouvre un fichier PDF en fonction du lien cliqué"""
        file_mapping = {
            "open_driver": "pdf/DRIVER_INSTALLATION.pdf",
            "open_commandes": "pdf/COMMUNICATION_COMMANDS.pdf",
            "open_manuel": "pdf/USER_MANUAL.pdf",
            "open_datasheet": "pdf/TECHNICAL_DATA_SHEET.pdf"
        }

        if link in file_mapping:
            pdf_full_path = os.path.abspath(file_mapping[link])  # Convertir en chemin absolu
            if os.path.exists(pdf_full_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_full_path))
            else:
                print(f"Erreur : fichier {pdf_full_path} introuvable.")
