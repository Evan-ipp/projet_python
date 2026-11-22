%pip install openpyxl
import pandas as pd

url = "https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-{}.xlsx"

#On importe les 4 Net Asset Values (NAV) de : S&P500, Emerging Markets, Investment Grade Bonds, High Yield Bonds
tickers = ["spy", "spem", "spib", sphy"]
nav = {}
for ticker in tickers : 
  nav[ticker] = pd.read_excel(url.format(ticker), header=3, usecols = "A:D").dropna(axis=1, how="all")

#On commence par nettoyer le dataframe au niveau des dates : conversion, valeurs manquantes, valeurs en double
for ticker in tickers : 
  nav[ticker]["Date"] = pd.to_datetime(nav[ticker]["Date"], format="%d-%b-%Y", errors="coerce")
  dates_manquantes = nav[ticker]["Date"].isna().sum()
  print(f"{ticker.upper()} - dates invalides ou manquantes :", dates_manquantes)
  nav[ticker] = nav[ticker].dropna(subset=["Date"]).reset_index(drop=True)
  nav[ticker]=nav[ticker].drop_suplicates(subset=["Date]).sort_values("Date").reste_index(drop=True)
																									

  

                                                                                
  
                                                                                
                                                                                    
