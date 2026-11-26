# Analyse des écarts Prix de Marché vs NAV des ETF

## Problématique

Ce projet étudie la formation, les déterminants de marché et la résorption des écarts (primes et décotes) entre le prix de marché (`Close`) et la valeur nette des actifs (`NAV`) de quatre ETF gérés par **State Street (SSGA)** :
* `SPY` — Actions américaines (S&P 500)
* `SPEM` — Actions émergentes
* `SPIB` — Obligations *Investment Grade*
* `SPHY` — Obligations *High Yield*

L'analyse s'articule en cinq étapes :
1. Collecte et nettoyage des historiques de NAV (SSGA).
2. Collecte et nettoyage des prix de clôture et volumes (Yahoo Finance).
3. Fusion des séries, ajustement du split 2:1 sur `SPEM` (16/10/2017) et statistiques descriptives des primes/décotes.
4. Comparaison des écarts selon les régimes de volatilité (`^VIX`) et de liquidité (quartiles de volume par ETF).
5. Mesure de la correction des écarts importants (`|Prime/Décote_t| ≥ 0,25 %`) dès la séance suivante (`t+1`).

## Structure du dépôt

```text
.
├── Projet_Python_S1.ipynb   # Notebook principal (analyse, équations, interprétations, graphiques)
├── Main.py                  # Script d'exécution complet en ligne de commande
├── requirements.txt         # Dépendances Python pour la reproductibilité
├── README.md                # Documentation du projet et guide d'exécution
├── .gitignore               # Fichiers temporaires et caches exclus de Git
└── src/                     # Code modulaire et documenté
    ├── __init__.py
    ├── data_loader.py       # Ingestion SSGA (Excel), Yahoo Finance (ETF & VIX) + nettoyage
    ├── analysis.py          # Fusion, split SPEM 2:1, régimes VIX/liquidité, stats & dynamique t+1
    └── visualization.py     # Graphiques Matplotlib (séries temporelles, régimes, scatter t+1)
```

## Sources de données (accès public et reproductible)

Aucune donnée locale privée ni gros fichier n'est stocké dans le dépôt Git : le pipeline télécharge automatiquement les séries à jour lors de l'exécution.
* **NAV historiques** : fichiers Excel publics publiés par State Street Global Advisors (`https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-{ticker}.xlsx`).
* **Cours de clôture et volumes des ETF** : API Yahoo Finance via `yfinance`.
* **Indice de volatilité (`^VIX`)** : API Yahoo Finance via `yfinance`.

## Exécution du projet (Local ou SSPCloud)

### Option 1 : Sur le SSPCloud (Onyxia)
1. Ouvrir un service **Jupyter-Python** (ou **VSCode-Python**) sur [datalab.sspcloud.fr](https://datalab.sspcloud.fr).
2. Dans le terminal du service, cloner le dépôt et se placer dans le dossier :
```bash
git clone https://github.com/Evan-ipp/projet_python.git
cd projet_python
```
3. Installer les dépendances :
```bash
pip install -r requirements.txt
```
4. Ouvrir `Projet_Python_S1.ipynb` dans JupyterLab et cliquer sur **Run All**, ou exécuter directement le script en ligne de commande :
```bash
python Main.py
```

### Option 2 : En local
1. Cloner le dépôt et créer (optionnel mais recommandé) un environnement virtuel :
```bash
git clone https://github.com/Evan-ipp/projet_python.git
cd projet_python
python -m venv .venv
source .venv/bin/activate   # Sur Windows : .venv\Scripts\activate
```
2. Installer les dépendances :
```bash
pip install -r requirements.txt
```
3. Lancer le notebook ou le script principal :
```bash
jupyter notebook Projet_Python_S1.ipynb
```
*(Ou en script : `python Main.py`.)*
