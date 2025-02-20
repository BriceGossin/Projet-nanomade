import serial
import threading
import csv
import os
import datetime

# Configuration du port série (remplace "COM9" par le bon port)
ser = serial.Serial("COM9", baudrate=430000, timeout=1)

# Fichier CSV pour enregistrer les données
csv_file = "sensor_responses.csv"

# Fonction pour enregistrer les réponses dans un fichier CSV avec un timestamp
def save_to_csv(data):
    try:
        # Vérifier si le fichier existe pour ajouter un en-tête si nécessaire
        file_exists = os.path.exists(csv_file)

        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)

            # Ajouter un en-tête si le fichier est créé pour la première fois
            if not file_exists:
                writer.writerow(["Timestamp", "M_F_1", "M_F_2", "M_F_3", "M_F_4", "M_F_5", "M_F_6", "M_F_7", "M_F_8", 
                                 "U_F_1", "U_F_2", "U_F_3", "U_F_4", "U_F_5", "U_F_6", "U_F_7", "U_F_8", 
                                 "M_C_1", "M_C_2", "M_C_3", "M_C_4", "M_C_5", "M_C_6", "M_C_7", "M_C_8", 
                                 "U_C_1", "U_C_2", "U_C_3", "U_C_4", "U_C_5", "U_C_6", "U_C_7", "U_C_8"])
                print(f"✅ Fichier CSV '{csv_file}' créé avec un en-tête.")

            # Obtenir le timestamp actuel avec correction
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]  # Millisecondes correctes

            # Diviser la ligne de données en une liste de valeurs et ajouter le timestamp
            row = [timestamp] + data.split()
            writer.writerow(row)  # Enregistrer chaque valeur dans une colonne du CSV

       
    except Exception as e:
        print(f"⚠️ Erreur lors de l'enregistrement dans le fichier CSV: {e}")

def read_from_sensor():
    """Lit et affiche les données en continu avec timestamp corrigé."""
    while True:
        try:
            data = ser.readline().decode().strip()
            if data:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3] 
                print(f"💬 [{timestamp}] Capteur: {data}")
                
                # Enregistrer toutes les réponses avec timestamp crrigé
                save_to_csv(data)
        except Exception as e:
            print(f"⚠️ Erreur de lecture: {e}")
            break

# Démarrer un thread pour lire en continu les données du capteur
thread = threading.Thread(target=read_from_sensor, daemon=True)
thread.start()



try:
    while True:
        user_input = input("Commande > ").strip()
        
        if user_input.lower() == "exit":
            print("👋 Fermeture de la connexion.")
            break

        ser.write((user_input + "\n").encode())  # Envoyer la commande
except KeyboardInterrupt:
    print("\n🛑 Arrêt du programme.")

finally:
    ser.close()
    print("🔌 Connexion série fermée.")
