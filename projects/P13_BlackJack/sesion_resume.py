import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from game import Game
import statistics
import streamlit as st

def build_montecarlo_matrix(results: list[dict]) -> pd.DataFrame:

    max_len = max(len(r["net_worth"]) for r in results)
    matrix = pd.DataFrame([
        list(r["net_worth"]) + [float("nan")] * (max_len - len(r["net_worth"]))
        for r in results
    ]).T
    matrix.columns = [f"session_{i}" for i in range(len(results))]
    matrix.index.name = "hand"
    return matrix

def plot_montecarlo(matrix: pd.DataFrame, strategy = ""):
    for col in matrix.columns:
        plt.plot(matrix.index, matrix[col], alpha=0.2, color="steelblue")
    
    mean = matrix.mean(axis=1)
    std = matrix.std(axis=1)
    lower = matrix.quantile(0.05, axis=1)
    upper = matrix.quantile(0.95, axis=1)
    
        
    plt.xlabel("Hands")
    plt.ylabel("Net Worth")
    plt.title(strategy)   
    plt.plot(matrix.index, matrix.mean(axis=1), color="red", linewidth=2.5, label="Mean")
    plt.fill_between(matrix.index, mean - std, mean + std, color="red", alpha=0.15, label = "1 std" )
    plt.fill_between(matrix.index, lower, upper, color="red", alpha=0.15, label="5th–95th pct")
    plt.legend()
    plt.show()

def st_plot_montecarlo(matrix: pd.DataFrame, strategy = ""):
    for col in matrix.columns:
        plt.plot(matrix.index, matrix[col], alpha=0.2, color="steelblue")
    
    mean = matrix.mean(axis=1)
    std = matrix.std(axis=1)
    lower = matrix.quantile(0.05, axis=1)
    upper = matrix.quantile(0.95, axis=1)
            
    fig, ax = plt.subplots()
    ax.set_xlabel("Hands")
    ax.set_ylabel("Net Worth")
    ax.set_title(strategy)
    ax.plot(matrix.index, mean, color="red", linewidth=2.5, label="Mean")
    ax.fill_between(matrix.index, mean - std, mean + std, color="red", alpha=0.15, label="1 std")
    ax.fill_between(matrix.index, lower, upper, color="red", alpha=0.15, label="5th–95th pct")
    ax.legend()
    st.pyplot(fig)

def st_multi_plot(list_matrixes, labels=None, strategy=""):
    fig, ax = plt.subplots()
    ax.set_title(strategy)
    ax.set_xlabel("Hands")
    ax.set_ylabel("Net Worth")

    colors = plt.cm.tab10.colors

    for i, matrix in enumerate(list_matrixes):
        mean = matrix.mean(axis=1)
        std = matrix.std(axis=1)
        color = colors[i % len(colors)]
        label = labels[i] if labels else f"Series {i+1}"

        ax.plot(matrix.index, mean, color=color, linewidth=2.5, label=label)
        ax.fill_between(matrix.index, mean - std, mean + std, color=color, alpha=0.15)

    ax.legend()
    st.pyplot(fig)

def summarize(results: list[dict]) -> dict:
    finals = [r["final_net_worth"] for r in results]
    ruin_pct = 100 * sum(r["went_negative"] for r in results) / len(results)

    total_wins = sum(r["wins"] for r in results)
    total_losses = sum(r["losses"] for r in results)
    total_draws = sum(r["draws"] for r in results)

    win_rate = 100 * total_wins / (total_wins + total_losses + total_draws)
    
    if len(results) == 1:
        return {
                "mean_final_net_worth": round(statistics.mean(finals), 2),
                "std_final_net_worth": round(0, 2),
                "min_final_net_worth": min(finals),
                "max_final_net_worth": max(finals),
                "risk_of_ruin_pct": round(ruin_pct, 2),
                "win_rate_pct": round(win_rate, 2),
                "median_final_net_worth": round(statistics.median(finals), 2),
            }
        
    return {
        "mean_final_net_worth": round(statistics.mean(finals), 2),
        "std_final_net_worth": round(statistics.stdev(finals), 2),
        "min_final_net_worth": min(finals),
        "max_final_net_worth": max(finals),
        "risk_of_ruin_pct": round(ruin_pct, 2),
        "win_rate_pct": round(win_rate, 2),
        "median_final_net_worth": round(statistics.median(finals), 2),
    }
