from game import Game
from sesion_resume import build_montecarlo_matrix, plot_montecarlo, summarize
from collections import Counter

CONFIGS = {
    #"perfect_strategy":            dict(manual=False, counting=False, verbose=False),
    #"counting_conservative_nodev": dict(manual=False, counting=True, deviations=False, spread="conservative", verbose=False),
    #"counting_conservative_dev":   dict(manual=False, counting=True, deviations=True,  spread="conservative", verbose=False),
    #"counting_aggressive_nodev":   dict(manual=False, counting=True, deviations=False, spread="aggressive",   verbose=False),
    "counting_aggressive_dev":     dict(manual=False, counting=True, deviations=True,  spread="aggressive",   verbose=False),
}

N_SESSIONS = 100
ROUNDS_PER_SESSION = 10000
NUM_DECKS = 6

def run_sessions(config: dict, n_sessions: int, rounds_per_session: int) -> list[dict]:
    results = []

    for _ in range(n_sessions):
        game = Game(num_decks=NUM_DECKS, num_players=1, **config, min_bet=0, max_bet=10000000, surrender=True, DAS=True)
        
        player = game.players[0]
        game.simulate(rounds_per_session)
        net_worth = player.net_worth

        wl = Counter("W" if b > a else "L" if b < a else "D" for a, b in zip(net_worth, net_worth[1:]))
        results.append({
            "net_worth": net_worth.copy(),
            "final_net_worth": net_worth[-1],
            "went_negative": player.ruined,
            "wins": wl["W"],
            "losses": wl["L"],
            "draws": wl["D"],
        })

    return results

def main():
    print(f"Running {N_SESSIONS} sessions x {ROUNDS_PER_SESSION} rounds per strategy...\n")

    summaries = {}

    for name, config in CONFIGS.items():
        results = run_sessions(config, N_SESSIONS, ROUNDS_PER_SESSION)
        summaries[name] = summarize(results)

        game = Game(num_decks=NUM_DECKS, num_players=1, **config, min_bet=0, max_bet=10000000, surrender=True, DAS=True)
        matrix = build_montecarlo_matrix(results)
        plot_montecarlo(matrix, name)

    header = f"{'Strategy':<24}{'Mean $':>12}{'Std $':>12}{'Min $':>12}{'Max $':>12}{'Ruin %':>10}{'Win %':>10}{'Median $':>10}"
    print(header)
    print("-" * len(header))

    for name, s in summaries.items():
        print(
            f"{name:<24}"
            f"{s['mean_final_net_worth']:>12}"
            f"{s['std_final_net_worth']:>12}"
            f"{s['min_final_net_worth']:>12}"
            f"{s['max_final_net_worth']:>12}"
            f"{s['risk_of_ruin_pct']:>10}"
            f"{s['win_rate_pct']:>10}"
            f"{s['median_final_net_worth']:>10}"
        )

if __name__ == "__main__":
    main()