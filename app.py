import sys
import csv
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView

class CSVViewer(QWidget):  # On remplace MainWindow par CSVViewer
    def __init__(self, filename):
        super().__init__()

        layout = QVBoxLayout()
        self.label = QLabel("Données du fichier CSV :")
        layout.addWidget(self.label)

        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget)

        self.setLayout(layout)
        self.load_csv(filename)

    def load_csv(self, filename):
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

                    self.tableWidget.setColumnWidth(0, 200)
                    self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
                    self.tableWidget.horizontalHeader().setStretchLastSection(True)

        except Exception as e:
            self.label.setText(f"Erreur : {e}")


"""if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())"""
