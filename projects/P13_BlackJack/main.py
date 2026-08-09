import statistics
from collections import Counter
from game import Game


CONFIGS = {
    "perfect_strategy":            dict(manual=False, counting=False, verbose=False),
    "counting_conservative_nodev": dict(manual=False, counting=True, deviations=False, spread="conservative", verbose=False),
    "counting_conservative_dev":   dict(manual=False, counting=True, deviations=True,  spread="conservative", verbose=False),
    "counting_aggressive_nodev":   dict(manual=False, counting=True, deviations=False, spread="aggressive",   verbose=False),
    "counting_aggressive_dev":     dict(manual=False, counting=True, deviations=True,  spread="aggressive",   verbose=False),
}

N_SESSIONS = 100
ROUNDS_PER_SESSION = 10000
NUM_DECKS = 6


def run_sessions(config: dict, n_sessions: int, rounds_per_session: int) -> list[dict]:
    results = []

    for _ in range(n_sessions):
        
        if _ in (10,20,30,40,50,60,70,80,90):
            print(_)
        game = Game(num_decks=NUM_DECKS, num_players=1, **config, min_bet=0, max_bet = 10000000)
        player = game.players[0]
        player.automatic_bet = player.unit_value  # only used when counting=False

        game.simulate(rounds_per_session)
        
        net_worth = player.net_worth
        went_negative = any(nw < 0 for nw in net_worth)

        wl = Counter(
            "W" if b > a else "L" if b < a else "D"
            for a, b in zip(net_worth, net_worth[1:])
        )

        results.append({
            "final_net_worth": net_worth[-1],
            "went_negative": went_negative,
            "wins": wl["W"],
            "losses": wl["L"],
            "draws": wl["D"],
        })
        

    return results


def summarize(results: list[dict]) -> dict:
    finals = [r["final_net_worth"] for r in results]
    ruin_pct = 100 * sum(r["went_negative"] for r in results) / len(results)
    win_rate = 100 * sum(r["wins"] for r in results) / sum(
        r["wins"] + r["losses"] + r["draws"] for r in results
    )

    return {
        "mean_final_net_worth": round(statistics.mean(finals), 2),
        "std_final_net_worth": round(statistics.stdev(finals), 2),
        "min_final_net_worth": min(finals),
        "max_final_net_worth": max(finals),
        "risk_of_ruin_pct": round(ruin_pct, 2),
        "win_rate_pct": round(win_rate, 2),
    }


def main():
    print(f"Running {N_SESSIONS} sessions x {ROUNDS_PER_SESSION} rounds per strategy...\n")

    summaries = {}
    for name, config in CONFIGS.items():
        results = run_sessions(config, N_SESSIONS, ROUNDS_PER_SESSION)
        summaries[name] = summarize(results)

    header = f"{'Strategy':<24}{'Mean $':>12}{'Std $':>12}{'Min $':>12}{'Max $':>12}{'Ruin %':>10}{'Win %':>10}"
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
        )

def main2():
    pass

if __name__ == "__main__":
    main()