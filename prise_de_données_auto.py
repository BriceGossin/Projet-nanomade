import serial
import threading
import csv
import os
import datetime
import time
import tkinter as tk
from tkinter import filedialog

# Configuration du port série (remplace "COM9" par le bon port)
ser = serial.Serial("COM9", baudrate=430000, timeout=1)

# Définir 'i' comme une variable globale
i = 0

def choose_save_directory():
    """Ouvre une boîte de dialogue pour choisir le répertoire où enregistrer les fichiers CSV."""
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale de Tkinter
    directory = filedialog.askdirectory(title="Choisir le répertoire pour enregistrer les fichiers")
    return directory

def create_csv_file(directory):
    """Crée un fichier CSV unique basé sur le timestamp actuel dans le répertoire choisi."""
    if not directory:  # Si l'utilisateur annule, on ne continue pas
        print("⚠️ Aucun répertoire choisi. Arrêt du programme.")
        exit()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(directory, f"sensor_data_{timestamp}.csv")
    
    # Créer le fichier CSV et écrire l'en-tête
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([ 
            "Timestamp", "M_F_1", "M_F_2", "M_F_3", "M_F_4", "M_F_5", "M_F_6", "M_F_7", "M_F_8",
            "U_F_1", "U_F_2", "U_F_3", "U_F_4", "U_F_5", "U_F_6", "U_F_7", "U_F_8",
            "M_C_1", "M_C_2", "M_C_3", "M_C_4", "M_C_5", "M_C_6", "M_C_7", "M_C_8",
            "U_C_1", "U_C_2", "U_C_3", "U_C_4", "U_C_5", "U_C_6", "U_C_7", "U_C_8"
        ])
    return filename

def save_to_csv(filename, data):
    """Enregistre les données dans le fichier CSV avec le bon format."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        values = data.split()
        
        # S'assurer que chaque ligne a bien 33 colonnes
        while len(values) < 32:
            values.append("")
        
        row = [timestamp] + values[:32]  # Limiter à 32 colonnes au cas où
        
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(row)
    except Exception as e:
        print(f"⚠️ Erreur lors de l'enregistrement : {e}")

def send_calibration_commands():
    """Envoie les commandes de calibration au capteur."""
    for command in ["K\n", "GD\n", "CC\n"]:
        ser.write(command.encode())
        time.sleep(1)  # Petite pause pour éviter d'envoyer trop vite
    
    # Envoyer la commande pour démarrer la prise de mesures
    ser.write("R\n".encode())
    time.sleep(0.5)
    
def discard_last_line():
    """Lis et ignore la dernière ligne envoyée après la commande 'S\n'."""
    try:
        data = ser.readline().decode().strip()
        print(f"⚠️ Ignorée : {data}")  # Affiche la ligne ignorée pour debug
    except Exception as e:
        print(f"⚠️ Erreur lors de la lecture de la dernière ligne à ignorer : {e}")

def read_from_sensor(filename, duration=5):
    """Lit et enregistre les données du capteur pendant 'duration' secondes."""
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            data = ser.readline().decode().strip()
            if data:
                print(f"💬 Capteur: {data}")
                save_to_csv(filename, data)
        except Exception as e:
            print(f"⚠️ Erreur de lecture: {e}")
            break
    
    # Envoyer la commande pour arrêter la prise de mesures
    ser.write("S\n".encode())
    time.sleep(0.5)
    discard_last_line()

def main():
    """Boucle principale qui enchaîne les sessions de 10s."""
    global i  # Indique que nous utilisons la variable globale 'i'
    try:
        directory = choose_save_directory()  # Demande à l'utilisateur où enregistrer les fichiers
        while True:
            print(f"🔄 Session {i}")
            i += 1  # Incrémente la variable 'i'
            csv_file = create_csv_file(directory)  # Crée le fichier dans le répertoire choisi
            send_calibration_commands()
            read_from_sensor(csv_file, duration=5)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du programme.")
    finally:
        ser.close()
        print("🔌 Connexion série fermée.")

if __name__ == "__main__":
    main()
