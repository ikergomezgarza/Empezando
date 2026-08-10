import sys
from pathlib import Path
import streamlit as st
from collections import Counter
PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "P13_BlackJack"
sys.path.insert(0, str(PROJECT_DIR))

from projects.P13_BlackJack.game import Game
from projects.P13_BlackJack.main import run_sessions, summarize, main
from projects.P13_BlackJack.sesion_resume import build_montecarlo_matrix, plot_montecarlo, st_plot_montecarlo



unit_value = 100
min_bet= 0
max_bet = 1000000
automatic= True
counting= False
deviation= True
spread= "conservative"

if "phase" not in st.session_state:
    st.session_state.phase = "setup"

#------------------ First part home screen ------------------------------


st.title("Blackjack")
st.write("")
    
col1,col3, col2 = st.columns(3)

with col1:
    st.write("Strategy methode:")
    automatic = st.toggle("Play Automatic:", True)
    if automatic:
        counting = st.toggle("Card counting:",True)
        deviation = st.toggle("Deviation:",True)
        spread = st.selectbox("Spread:", ["conservative", "aggressive"])
    
with col3: pass

with col2:
    st.write("Table and game")
    min_bet= st.number_input("Minimum bet", 0, value= 10, step= 1)
    max_bet= st.number_input("Maximum bet", 500, value= 5000, step= 100)
    unit_value = st.number_input("bet per hand", 10, 10000, value= 100, step= 1)
#------------------ Second part game playing ------------------------------
if st.button("Run"):
    
    if not automatic:
        
        st.session_state.game = Game(num_decks=6, players=1, verbose=False, 
                             min_bet=min_bet, max_bet=max_bet,
                             manual= not automatic, counting=counting, spread=spread)
        
        st.session_state.phase = "playing"
        game = st.session_state.game

        if st.button("New Round"):
            game.take_bets = lambda: None
            game.deal_initial()
            game.check_blackjacks()
            st.rerun()

        #show dealer card
        if game.dealer.hand.cards:
            st.write("Dealer showing:")
            st.image(game.dealer.hand.cards[0].image_path(), width=100)
        else:
            st.write("Dealer: —")
                
        #Show user cards
        if game.hand.cards:
            st.write("Your hand:")
            cols = st.columns(len(game.hand.cards))
            for col, card in zip(cols, game.hand.cards):
                col.image(card.image_path(), width=100)
            st.write(f"Value: {game.hand.value()}")
        else:
            st.write("Click 'New Round' to deal cards.")
        
        
        col1, col2, col3, col4 = st.columns(4)
        if col1.button("Hit"):
            game.hand.add(game.shoe.draw())
            st.rerun()
        if col2.button("Stand"):
            game.hand.resolved = True
            st.rerun()
        if col3.button("Double") and game.hand.can_double():
            game.double_down(game.player, game.hand)
            st.rerun()
        if col4.button("Split") and game.hand.can_split():
            game.split(game.player, game.hand)
            st.rerun()

    if automatic:
        
        CONFIGS = {
            "perfect_strategy":            dict(manual=False, counting=False, verbose=False, ),
            "counting_conservative_nodev": dict(manual=False, counting=True, deviations=False, spread="conservative", verbose=False),
            "counting_conservative_dev":   dict(manual=False, counting=True, deviations=True,  spread="conservative", verbose=False),
            "counting_aggressive_nodev":   dict(manual=False, counting=True, deviations=False, spread="aggressive",   verbose=False),
            "counting_aggressive_dev":     dict(manual=False, counting=True, deviations=True,  spread="aggressive",   verbose=False),
        }

        N_SESSIONS = 100
        ROUNDS_PER_SESSION = 10000
        NUM_DECKS = 6
        
        strategy_elected = "perfect_strategy"
        if counting:
            if spread == "conservative":
                if deviation:
                    strategy_elected = "counting_conservative_dev"
                strategy_elected = "counting_conservative_nodev"
            if spread == "aggresive":
                if deviation:
                    strategy_elected = "counting_aggressive_dev"
                strategy_elected = "counting_aggressive_nodev"
            
        
        print(f"Running {N_SESSIONS} sessions x {ROUNDS_PER_SESSION} rounds per strategy...\n")
        
        summaries = {}
    
        for name, config in CONFIGS.items():
            
            if strategy_elected == name:
                results = run_sessions(config, N_SESSIONS, ROUNDS_PER_SESSION,  unit_value= unit_value)
                summaries[name] = summarize(results)
        
                game = Game(num_decks=NUM_DECKS, num_players=1, **config, min_bet=0, max_bet=10000000, surrender=True, DAS=True,)
                game.players[0].unit_value = unit_value
                matrix = build_montecarlo_matrix(results)
                st_plot_montecarlo(matrix, name)
            else:
                pass
    
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
    
