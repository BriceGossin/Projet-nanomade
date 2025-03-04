import os
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# Fenêtre de sélection de fichier
def choisir_csv():
    Tk().withdraw()  # On cache la fenêtre principale de Tkinter
    fichier = askopenfilename(filetypes=[("Fichiers CSV", "*.csv")], title="Choisir un fichier CSV")
    return fichier

# Charger et traiter un fichier CSV
def charger_et_traiter_csv(fichier_csv):
    df = pd.read_csv(fichier_csv, on_bad_lines='skip')
    df = df.iloc[:, :17]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d %H:%M:%S,%f', errors='coerce')
    df = df.dropna(subset=['Timestamp'])
    df = df.apply(pd.to_numeric, errors='coerce')

    colonnes_a_garder = []
    for col in df.columns[1:17]:
        premiere_valeur = df[col].iloc[0]
        if premiere_valeur != 1000 and any(df[col] != 3299):
            colonnes_a_garder.append(col)

    df_filtre = df[['Timestamp'] + colonnes_a_garder]

    index_fin_calibration = 0
    for i in range(len(df) - 1, -1, -1):
        if df.iloc[i].isna().any():
            index_fin_calibration = i + 1
            break

    df_filtre = df_filtre.iloc[index_fin_calibration:]
    return df_filtre, colonnes_a_garder

# Tracer le graphique
def tracer_graphique(df_filtre, colonnes_a_garder, fichier_csv):
    ax.clear()
    for col in colonnes_a_garder:
        ax.plot(df_filtre['Timestamp'], df_filtre[col], label=col)
    ax.set_xlabel('Temps')
    ax.set_ylabel('Valeurs')
    ax.set_title(f'Évolution des valeurs - {os.path.basename(fichier_csv)}')
    ax.legend()
    plt.xticks(rotation=45)
    ax.grid(True)
    plt.draw()

# Naviguer dans les fichiers
def naviguer(event):
    global index_fichier
    if event.key == 'right':
        index_fichier = (index_fichier + 1) % len(liste_fichiers)
    elif event.key == 'left':
        index_fichier = (index_fichier - 1) % len(liste_fichiers)

    fichier_suivant = os.path.join(repertoire, liste_fichiers[index_fichier])
    df_filtre, colonnes_a_garder = charger_et_traiter_csv(fichier_suivant)
    tracer_graphique(df_filtre, colonnes_a_garder, fichier_suivant)

# Sélection du fichier initial
fichier_csv = choisir_csv()
if not fichier_csv:
    print("Aucun fichier sélectionné.")
    exit()

repertoire = os.path.dirname(fichier_csv)
liste_fichiers = [f for f in os.listdir(repertoire) if f.endswith('.csv')]
liste_fichiers.sort()
index_fichier = liste_fichiers.index(os.path.basename(fichier_csv))

# Création du graphique
fig, ax = plt.subplots(figsize=(10, 6))
df_filtre, colonnes_a_garder = charger_et_traiter_csv(fichier_csv)
tracer_graphique(df_filtre, colonnes_a_garder, fichier_csv)
fig.canvas.mpl_connect('key_press_event', naviguer)
plt.tight_layout()
plt.show()
