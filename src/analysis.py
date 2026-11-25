"""Module de fusion NAV/marché, calcul des primes/décotes et dynamique de correction j+1."""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_TYPE_ETF = {
    "SPY": "Actions américaines",
    "SPEM": "Actions émergentes",
    "SPIB": "Obligations investment grade",
    "SPHY": "Obligations high yield",
}

DEFAULT_CLASSE_ETF = {
    "SPY": "Actions",
    "SPEM": "Actions",
    "SPIB": "Obligations",
    "SPHY": "Obligations",
}


def merge_nav_and_prices(
    nav: dict[str, pd.DataFrame],
    prix: dict[str, pd.DataFrame],
    etfs: list[str],
    type_etf: dict[str, str] | None = None,
    classe_etf: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Fusionne les NAV et les prix de clôture sur les dates communes.

    Ajuste rétroactivement la NAV de SPEM pour le split 2:1 survenu le 16/10/2017
    et calcule la prime/décote relative, l'écart absolu et la moyenne mobile 30j.
    """
    type_map = type_etf or DEFAULT_TYPE_ETF
    classe_map = classe_etf or DEFAULT_CLASSE_ETF
    tableaux: list[pd.DataFrame] = []

    for ticker in etfs:
        nav_merge = nav[ticker.lower()][["Date", "NAV"]].copy()

        # Ajustement du split 2:1 sur SPEM (16/10/2017) absent de l'historique brut SSGA
        if ticker == "SPEM":
            nav_merge.loc[nav_merge["Date"] < pd.Timestamp("2017-10-16"), "NAV"] /= 2

        prix_merge = prix[ticker].reindex(columns=["Date", "Close", "Volume"]).copy()
        jointure = pd.merge(nav_merge, prix_merge, on="Date", how="inner")
        jointure = jointure.sort_values("Date").reset_index(drop=True)

        jointure["ETF"] = ticker
        jointure["Type"] = type_map[ticker]
        jointure["Classe"] = classe_map[ticker]
        jointure["Prime_decote_pct"] = (
            (jointure["Close"] - jointure["NAV"]) / jointure["NAV"] * 100
        )
        jointure["Abs_prime_decote_pct"] = jointure["Prime_decote_pct"].abs()
        jointure["Prime_decote_moyenne_30j"] = (
            jointure["Prime_decote_pct"].rolling(30, min_periods=5).mean()
        )
        tableaux.append(jointure)

    donnees = pd.concat(tableaux, ignore_index=True)
    return donnees.sort_values(["ETF", "Date"]).reset_index(drop=True)


def compute_spread_statistics(
    donnees: pd.DataFrame,
    thresholds: tuple[float, ...] = (0.25, 0.5, 1.0),
) -> pd.DataFrame:
    """Calcule les statistiques descriptives et fréquences de dépassement de seuils par ETF."""
    stats = (
        donnees.groupby(["ETF", "Classe", "Type"])
        .agg(
            Nombre_observations=("Date", "size"),
            Prime_decote_moyenne_pct=("Prime_decote_pct", "mean"),
            Prime_decote_mediane_pct=("Prime_decote_pct", "median"),
            Ecart_absolu_moyen_pct=("Abs_prime_decote_pct", "mean"),
            Ecart_absolu_max_pct=("Abs_prime_decote_pct", "max"),
        )
        .reset_index()
    )

    for seuil in thresholds:
        depassement = donnees.groupby("ETF")["Abs_prime_decote_pct"].apply(
            lambda s: (s > seuil).mean() * 100
        )
        stats[f"Jours_au_dessus_{seuil}pct"] = stats["ETF"].map(depassement)

    return stats


def compute_next_day_correction(
    donnees: pd.DataFrame,
    seuil_ecart: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Évalue si les écarts importants (>= seuil_ecart) se résorbent dès le lendemain.

    Utilise `groupby('ETF').shift(-1)` pour éviter toute fuite entre actifs
    et exclut la dernière observation de chaque ETF (qui n'a pas de lendemain).
    """
    df = donnees.sort_values(["ETF", "Date"]).copy()
    ecart_lendemain = df.groupby("ETF")["Abs_prime_decote_pct"].shift(-1)

    df["Variation_abs_1j"] = ecart_lendemain - df["Abs_prime_decote_pct"]
    df["Correction_lendemain"] = np.where(
        ecart_lendemain.notna(),
        df["Variation_abs_1j"] < 0,
        np.nan,
    )

    donnees_ecarts_importants = df[
        (df["Abs_prime_decote_pct"] >= seuil_ecart) & (ecart_lendemain.notna())
    ].copy()

    donnees_ecarts_importants["Ecart_abs_1j"] = (
        donnees_ecarts_importants["Abs_prime_decote_pct"]
        + donnees_ecarts_importants["Variation_abs_1j"]
    )

    vitesse_correction = (
        donnees_ecarts_importants.groupby(["ETF", "Classe", "Type"])
        .agg(
            Nb_dates=("Correction_lendemain", "count"),
            Taux_correction_pct=("Correction_lendemain", lambda x: x.mean() * 100),
            Variation_abs_moyenne_1j=("Variation_abs_1j", "mean"),
        )
        .reset_index()
    )

    return donnees_ecarts_importants, vitesse_correction


def add_market_regimes(
    donnees: pd.DataFrame,
    vix: pd.DataFrame,
) -> pd.DataFrame:
    """Ajoute les régimes de volatilité (VIX) et de liquidité (quartiles par ETF)."""
    df = donnees.merge(vix, on="Date", how="left")
    df["Regime_volatilite"] = np.select(
        [df["VIX"] < 15, df["VIX"] >= 30],
        ["Faible", "Forte"],
        default="Intermédiaire",
    )

    groupes_regimes = []
    for _, groupe in df.groupby("ETF", sort=False):
        groupe = groupe.copy()
        vol_q25, vol_q75 = groupe["Volume"].quantile([0.25, 0.75])
        groupe["Regime_liquidite"] = np.select(
            [groupe["Volume"] <= vol_q25, groupe["Volume"] >= vol_q75],
            ["Faible", "Forte"],
            default="Intermédiaire",
        )
        groupes_regimes.append(groupe)

    return (
        pd.concat(groupes_regimes, ignore_index=True)
        .sort_values(["ETF", "Date"])
        .reset_index(drop=True)
    )


def _summarize_regime(donnees: pd.DataFrame, regime_col: str) -> pd.DataFrame:
    """Agrège les écarts entre régimes faible et fort pour une dimension donnée."""
    return (
        donnees[donnees[regime_col].isin(["Faible", "Forte"])]
        .groupby(["Type", regime_col])
        .agg(
            Nb_jours=("Date", "size"),
            Prime_moyenne_pct=("Prime_decote_pct", "mean"),
            Ecart_absolu_moyen_pct=("Abs_prime_decote_pct", "mean"),
        )
        .reset_index()
    )


def analyze_market_regimes(
    donnees: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calcule les statistiques d'écarts selon les régimes de volatilité et de liquidité."""
    comparaison_volatilite = _summarize_regime(donnees, "Regime_volatilite")
    comparaison_liquidite = _summarize_regime(donnees, "Regime_liquidite")
    return comparaison_volatilite, comparaison_liquidite
