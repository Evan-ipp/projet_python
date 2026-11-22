#Récupération des données de NAVs 

import pandas as pd

url = "https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-{}.xlsx"

#On importe les 4 Net Asset Values (NAV) de : S&P500, Emerging Markets, Investment Grade Bonds, High Yield Bonds
tickers = ["spy", "spem", "spib", "sphy"]
nav = {}
for ticker in tickers : 
  nav[ticker] = pd.read_excel(url.format(ticker), header=3, usecols = "A:D").dropna(axis=1, how="all")

#On commence par nettoyer le dataframe au niveau des dates : conversion, valeurs manquantes, valeurs en double
for ticker in tickers : 
  nav[ticker]["Date"] = pd.to_datetime(nav[ticker]["Date"], format="%d-%b-%Y", errors="coerce")
  dates_manquantes = nav[ticker]["Date"].isna().sum()
  print(f"{ticker.upper()} - dates invalides ou manquantes :", dates_manquantes)
  nav[ticker] = nav[ticker].dropna(subset=["Date"]).reset_index(drop=True)
  nav[ticker]=nav[ticker].drop_duplicates(subset=["Date"]).sort_values("Date").reset_index(drop=True)

#Puis on nettoie les données de NAV : retire les valeurs manquantes et / ou négatives
#On retire les données plutôt que de les remplacer car les écarts entre NAVs et ETFs donc créer des données donnerait lieu à des écarts artificiellement grands
for ticker in tickers : 
  nav[ticker]["NAV"] = pd.to_numeric(nav[ticker]["NAV"], errors= "coerce")
  nbre_lignes_avant = len(nav[ticker])
  nav[ticker]=nav[ticker].dropna(subset=["NAV"])
  nav[ticker]= nav[ticker][nav[ticker]["NAV"]>0]
  nav[ticker]=nav[ticker].reset_index(drop=True)
  print("Nombre lignes supprimées car NAV manquante ou négative :", nbre_lignes_avant - len(nav[ticker]))
  print("Valeurs NAV manquantes après nettoyage :", nav[ticker]["NAV"].isna().sum())
  print(nav[ticker].head())

#Afficher la première et dernière date pour chaque NAV : ce sera utile pour merge plus tard
for ticker in tickers :
  nav[ticker] = nav[ticker].sort_values("Date").reset_index(drop=True)
  print(ticker.upper())
  print("Première date :", nav[ticker]["Date"].iloc[0])
  print("Dernière date :", nav[ticker]["Date"].iloc[-1])
  print("Nombre d'observations :", len(nav[ticker]))
