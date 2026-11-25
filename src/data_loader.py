"""Module d'ingestion et de nettoyage des données de NAV (SSGA) et de marché (Yahoo Finance)."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

DEFAULT_SSGA_URL = (
    "https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-{}.xlsx"
)


def _flatten_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplatit le MultiIndex de colonnes renvoyé par les versions récentes de yfinance."""
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_and_clean_nav(
    tickers: list[str],
    url_template: str = DEFAULT_SSGA_URL,
    verbose: bool = True,
) -> dict[str, pd.DataFrame]:
    """Télécharge et nettoie les historiques de NAV depuis State Street (SSGA).

    Les observations avec dates invalides/doublons ou NAV manquante/non positive
    sont supprimées plutôt qu'imputées afin d'éviter des écarts artificiels.
    """
    nav: dict[str, pd.DataFrame] = {}

    for raw_ticker in tickers:
        ticker = raw_ticker.lower()
        df = pd.read_excel(
            url_template.format(ticker),
            header=3,
            usecols="A:D",
        ).dropna(axis=1, how="all")

        df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%Y", errors="coerce")
        invalid_dates = int(df["Date"].isna().sum())
        df = (
            df.dropna(subset=["Date"])
            .drop_duplicates(subset=["Date"])
            .sort_values("Date")
            .reset_index(drop=True)
        )

        df["NAV"] = pd.to_numeric(df["NAV"], errors="coerce")
        rows_before = len(df)
        df = df.dropna(subset=["NAV"])
        df = df[df["NAV"] > 0].sort_values("Date").reset_index(drop=True)
        dropped_nav = rows_before - len(df)

        if verbose and not df.empty:
            print(
                f"{ticker.upper()} (NAV) | dates invalides: {invalid_dates} | "
                f"NAV invalides supprimées: {dropped_nav} | "
                f"période: {df['Date'].iloc[0].date()} -> {df['Date'].iloc[-1].date()} "
                f"({len(df)} obs.)"
            )

        nav[ticker] = df

    return nav


def fetch_and_clean_prices(
    etfs: list[str],
    start_date: str = "2012-06-19",
    end_date: str = "2026-10-15",
    verbose: bool = True,
) -> dict[str, pd.DataFrame]:
    """Télécharge et nettoie les prix de clôture et volumes via Yahoo Finance.

    L'argument `auto_adjust=False` conserve le prix de clôture historique réel
    (non ajusté des dividendes) afin de le comparer fidèlement à la NAV publiée.
    """
    prix: dict[str, pd.DataFrame] = {}

    for ticker in etfs:
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
        )
        df = _flatten_yfinance_columns(df)

        df.index = pd.to_datetime(df.index, errors="coerce")
        invalid_dates = int(df.index.isna().sum())
        df = df[df.index.notna()].copy()
        df.index.name = "Date"

        rows_before = len(df)
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna(subset=["Close"])
        df = df[df["Close"] >= 0].sort_index().reset_index()
        dropped_close = rows_before - len(df)

        if verbose and not df.empty:
            print(
                f"{ticker} (Prix) | dates invalides: {invalid_dates} | "
                f"Close invalides supprimés: {dropped_close} | "
                f"période: {df['Date'].iloc[0].date()} -> {df['Date'].iloc[-1].date()} "
                f"({len(df)} obs.)"
            )

        prix[ticker] = df

    return prix


def fetch_and_clean_vix(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    """Télécharge et nettoie l'indice VIX (borne end inclusive via +1 jour)."""
    vix = yf.download(
        "^VIX",
        start=start_date,
        end=end_date + pd.Timedelta(days=1),
        auto_adjust=False,
        progress=False,
    )
    vix = _flatten_yfinance_columns(vix)
    vix = vix.reset_index().rename(columns={"Close": "VIX"})
    vix["Date"] = pd.to_datetime(vix["Date"], errors="coerce")
    return vix[["Date", "VIX"]].dropna().drop_duplicates("Date")
