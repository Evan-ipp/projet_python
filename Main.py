"""Script principal d'exécution de l'analyse ETF (NAV vs Prix de marché)."""

from src.analysis import (
    add_market_regimes,
    analyze_market_regimes,
    compute_next_day_correction,
    compute_spread_statistics,
    merge_nav_and_prices,
)
from src.data_loader import (
    fetch_and_clean_nav,
    fetch_and_clean_prices,
    fetch_and_clean_vix,
)
from src.visualization import (
    plot_daily_spreads,
    plot_next_day_correction,
    plot_regime_comparisons,
)

ETFS = ["SPY", "SPEM", "SPIB", "SPHY"]
START_DATE = "2012-06-19"
END_DATE = "2026-10-15"


def main() -> None:
    """Exécute le pipeline complet de collecte, analyse et visualisation."""
    nav = fetch_and_clean_nav([t.lower() for t in ETFS])
    prix = fetch_and_clean_prices(ETFS, start_date=START_DATE, end_date=END_DATE)

    donnees = merge_nav_and_prices(nav, prix, ETFS)
    stats = compute_spread_statistics(donnees)
    print("\n--- Statistiques des écarts ---")
    print(stats.round(4))

    plot_daily_spreads(donnees)

    vix = fetch_and_clean_vix(donnees["Date"].min(), donnees["Date"].max())
    donnees = add_market_regimes(donnees, vix)
    comparaison_volatilite, comparaison_liquidite = analyze_market_regimes(donnees)
    print("\n--- Comparaison selon la volatilité ---")
    print(comparaison_volatilite.round(4))
    print("\n--- Comparaison selon la liquidité ---")
    print(comparaison_liquidite.round(4))

    plot_regime_comparisons(donnees)

    donnees_ecarts_importants, vitesse_correction = compute_next_day_correction(
        donnees, seuil_ecart=0.25
    )
    print("\n--- Vitesse de correction le lendemain (écarts >= 0.25%) ---")
    print(vitesse_correction.round(4))

    plot_next_day_correction(donnees_ecarts_importants)


if __name__ == "__main__":
    main()
