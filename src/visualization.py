"""Module de visualisation des primes/décotes quotidiennes et de leur correction à j+1."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd


def plot_daily_spreads(donnees: pd.DataFrame, show: bool = True):
    """Affiche l'évolution quotidienne de la prime/décote pour chaque ETF (grille 2x2)."""
    plt.style.use("ggplot")
    fig, axes = plt.subplots(2, 2, figsize=(15, 9))
    axes = axes.flatten()

    for ax, (ticker, groupe) in zip(axes, donnees.groupby("ETF", sort=False)):
        groupe = groupe.sort_values("Date")
        ax.plot(groupe["Date"], groupe["Prime_decote_pct"], linewidth=0.8)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(f"Prime/décote de {ticker}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Écart (%)")
        ax.grid(True)

    fig.suptitle("Évolution de la prime/décote par ETF", fontsize=16)
    plt.tight_layout()
    if show:
        plt.show()
    return fig


def plot_next_day_correction(donnees_ecarts_importants: pd.DataFrame, show: bool = True):
    """Trace l'écart absolu à j+1 en fonction de l'écart à j pour les écarts importants.

    Points sous la diagonale (y < x) : l'écart diminue le lendemain (correction).
    Points au-dessus de la diagonale (y > x) : l'écart s'aggrave le lendemain.
    """
    plt.style.use("ggplot")
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    axes = axes.flatten()

    for ax, (ticker, groupe) in zip(axes, donnees_ecarts_importants.groupby("ETF")):
        ax.scatter(
            groupe["Abs_prime_decote_pct"],
            groupe["Ecart_abs_1j"],
            alpha=0.35,
            s=12,
        )
        valeur_max = max(
            groupe["Abs_prime_decote_pct"].max(),
            groupe["Ecart_abs_1j"].max(),
        )
        # Bissectrice y = x (absence de changement entre j et j+1)
        ax.plot([0, valeur_max], [0, valeur_max], color="black", linestyle="--")
        ax.set_title(f"Correction des écarts : {ticker}")
        ax.set_xlabel("Écart absolu aujourd'hui (%)")
        ax.set_ylabel("Écart absolu le lendemain (%)")
        ax.grid(True)

    fig.suptitle("Évolution des écarts importants entre deux séances", fontsize=15)
    plt.tight_layout()
    if show:
        plt.show()
    return fig


def plot_regime_comparisons(donnees: pd.DataFrame, show: bool = True):
    """Trace la comparaison de l'écart absolu moyen selon la volatilité et la liquidité."""
    plt.style.use("ggplot")

    graph_volatilite = (
        donnees[donnees["Regime_volatilite"].isin(["Faible", "Forte"])]
        .groupby(["ETF", "Regime_volatilite"])["Abs_prime_decote_pct"]
        .mean()
        .unstack()
        .reindex(columns=["Faible", "Forte"])
    )
    graph_liquidite = (
        donnees[donnees["Regime_liquidite"].isin(["Faible", "Forte"])]
        .groupby(["ETF", "Regime_liquidite"])["Abs_prime_decote_pct"]
        .mean()
        .unstack()
        .reindex(columns=["Faible", "Forte"])
    )

    # Visualisation : comparaison entre volatilité faible/forte et liquidité faible/forte
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, table, title, legend_title in (
        (axes[0], graph_volatilite, "Écart absolu moyen selon la volatilité", "Volatilité"),
        (axes[1], graph_liquidite, "Écart absolu moyen selon la liquidité", "Liquidité"),
    ):
        table.plot(kind="bar", ax=ax, color=["blue", "red"])
        ax.set_title(title)
        ax.set_xlabel("ETF")
        ax.set_ylabel("Écart absolu moyen (%)")
        ax.legend(title=legend_title)
        ax.grid(axis="y")

    plt.tight_layout()
    if show:
        plt.show()
    return fig
