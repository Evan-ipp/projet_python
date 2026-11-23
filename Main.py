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



#Importation des prix de cloture et de volume des ETF

import yfinance as yf

etfs = ["SPY", "SPEM", "SPIB", "SPHY"]

prix = {}

#Importation des données yahoo finance et gestion du MultiIndex sur l'api
for ticker in etfs:
  prix[ticker]=yf.download(ticker, start= "2012-06-19", end= "2026-10-15", auto_adjust=False, progress=False)
  if isinstance(prix[ticker].columns, pd.MultiIndex):
    prix[ticker].columns = (prix[ticker].columns.get_level_values(0))

#Nettoyage de la colonne des dates
for ticker in etfs:
  prix[ticker].index = pd.to_datetime(prix[ticker].index, errors="coerce")
  dates_manquantes = prix[ticker].index.isna().sum()
  print(f"{ticker} - dates invalides ou manquantes :", dates_manquantes)
  prix[ticker] = prix[ticker][prix[ticker].index.notna()]
  prix[ticker].index.name = "Date"

#Suppressions des lignes sans prix close, ou avec prix close négatif
for ticker in etfs : 
  nombre_lignes_avant = len(prix[ticker])
  prix[ticker]["Close"] = pd.to_numeric(prix[ticker]["Close"], errors="coerce")
  prix[ticker]=prix[ticker].dropna(subset=["Close"])
  prix[ticker]=prix[ticker][prix[ticker]["Close"]>=0]
  prix[ticker]=prix[ticker].sort_index().reset_index()
  print("Nombre lignes supprimées car Close manquant ou négatif :", nbre_lignes_avant - len(prix[ticker]))
  print("Valeurs Close manquantes après nettoyage :", prix[ticker]["Close"].isna().sum())
  print(prix[ticker][["Close", "Volume"]].head())

#Affichage de la première et dernière date pour chaque ETF : utile pour merge plus tard
for ticker in etfs: 
  prix[ticker] = prix[ticker].sort_values("Date").reset_index(drop=True)
  print(ticker.upper())
  print("Première date :", prix[ticker]["Date"].iloc[0])
  print("Dernière date :", prix[ticker]["Date"].iloc[-1])
  print("Nombre d'observations :", len(prix[ticker]))


#Fusion des NAV et prix de marché : on conserve uniquement les dates communes à la NAV et au prix de clôture.
#on conserve les volumes pour avoir une mesure de la liqudité, pour plus tard

type_etf = {"SPY": "Actions américaines", "SPEM": "Actions émergentes", "SPIB": "Obligations investment grade", "SPHY": "Obligations high yield"}
classe_etf = {"SPY": "Actions", "SPEM": "Actions", "SPIB": "Obligations", "SPHY": "Obligations"}

tableaux = []

for ticker in etfs : 
    nav_merge = nav[ticker.lower()][["Date", "NAV"]].copy()
    # Le split 2:1 sur SPEM survenu le 16/10/2017 est désormais pris en compte.
    if ticker == "SPEM":
       nav_merge.loc[nav_merge["Date"] < pd.Timestamp("2017-10-16"), "NAV"] /= 2
    prix_merge = prix[ticker].reindex(columns=["Date", "Close", "Volume"]).copy()

    jointure = pd.merge(nav_merge,prix_merge, on = "Date", how = "inner")
    print(len(jointure))
    jointure["ETF"] = ticker
    jointure["Type"] = type_etf[ticker]
    jointure["Classe"] = classe_etf[ticker]
    jointure["Prime_decote_pct"] = (jointure["Close"] - jointure["NAV"]) / jointure["NAV"] * 100
    jointure["Abs_prime_decote_pct"] = jointure["Prime_decote_pct"].abs()
    jointure["Prime_decote_moyenne_30j"]= jointure["Prime_decote_pct"].rolling(30, min_periods=5).mean()
    tableaux.append(jointure)

donnees = pd.concat(tableaux, ignore_index = True)
donnees = donnees.sort_values(["ETF", "Date"]).reset_index(drop=True)

Statistiques_ecarts = (donnees.groupby(["ETF", "Classe", "Type"]).agg(
        Nombre_observations=("Date", "size"),
        Prime_decote_moyenne_pct=("Prime_decote_pct", "mean"),
        Prime_decote_mediane_pct=("Prime_decote_pct", "median"),
        Ecart_absolu_moyen_pct=("Abs_prime_decote_pct", "mean"),
        Ecart_absolu_max_pct=("Abs_prime_decote_pct", "max")
    ).reset_index())

#on veut regarder quand est-ce que les écarts NAV-ETF dépassent certains seuils (0.25%, 0.5% et 1%)
for seuil in [0.25, 0.5, 1.0]:
        #calcule la proportion de jours en % pour lesquels on dépasse chaque seuil pour chaque ETF 
        depassement = donnees.groupby("ETF")["Abs_prime_decote_pct"].apply(lambda s: (s > seuil).mean() * 100)
        #On rajoute une colonne dans laquelle on trouve le nbre de jours au dessus de chaque seuil pour chaque ETF dans le dataframe de stats
        Statistiques_ecarts[f"Jours_au_dessus_{str(seuil)}pct"] = Statistiques_ecarts["ETF"].map(depassement)

print(donnees[["ETF", "Date", "Close", "NAV", "Volume", "Prime_decote_pct", "Prime_decote_moyenne_30j"]].head())
print(Statistiques_ecarts.round(4)) 


#On affiche les primes et décôtes quotidiennes
import matplotlib.pyplot as plt

plt.style.use("ggplot")

fig, axes = plt.subplots(2, 2, figsize=(15, 9)) #on veut 4 graphes, 2 en ligne, 2 en colonne
axes = axes.flatten()


for ax, (ticker, groupe) in zip(axes, donnees.groupby("ETF", sort=False)): #cette boucle associe un emplacement de graphique "ax", un ETF "ticker", et les données correspondantes "groupe"
    groupe = groupe.sort_values("Date")

    ax.plot(groupe["Date"], groupe["Prime_decote_pct"], linewidth=0.8)  #trace

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title(f"Prime/décote de {ticker}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Écart (%)")
    ax.grid(True)

fig.suptitle("Évolution de la prime/décote par ETF", fontsize=16) #titre des 4 graphes ensemble
plt.tight_layout()
plt.show()