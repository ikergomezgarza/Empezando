import sys
from pathlib import Path
import streamlit as st
from collections import Counter
PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "P13_BlackJack"
sys.path.insert(0, str(PROJECT_DIR))

from projects.P13_BlackJack.game import Game
from projects.P13_BlackJack.main import run_sessions, summarize, main
from projects.P13_BlackJack.sesion_resume import build_montecarlo_matrix, plot_montecarlo, st_plot_montecarlo, st_multi_plot



unit_value = 100
min_bet= 0
max_bet = 1000000
manual= False
simulation = False
multi_strategy= False

N_SESSIONS = 100
ROUNDS_PER_SESSION = 10000
NUM_DECKS = 6

CONFIGS = {
        "Perfect strategy":                  dict(manual=False, counting=False, verbose=False, ),
        "Counting conservative":             dict(manual=False, counting=True, deviations=False, spread="conservative", verbose=False),
        "Counting deviation conservative":   dict(manual=False, counting=True, deviations=True,  spread="conservative", verbose=False),
        "Counting aggressive":               dict(manual=False, counting=True, deviations=False, spread="aggressive",   verbose=False),
        "Counting deviation aggressive":      dict(manual=False, counting=True, deviations=True,  spread="aggressive",   verbose=False),
    }

CONFIGS_COMPUTER = {
        "Perfect_strategy":                  dict(manual=False, counting=False, verbose=False, ),
        "Counting_conservative":             dict(manual=False, counting=True, deviations=False, spread="conservative", verbose=False),
        "Counting_deviation_conservative":   dict(manual=False, counting=True, deviations=True,  spread="conservative", verbose=False),
        "Counting_aggressive":               dict(manual=False, counting=True, deviations=False, spread="aggressive",   verbose=False),
        "ounting_deviation_aggressive":      dict(manual=False, counting=True, deviations=True,  spread="aggressive",   verbose=False),
    }



if "phase" not in st.session_state:
    st.session_state.phase = "setup"

#------------------ First part home screen ------------------------------


st.title("Blackjack")
st.write("")
    
col1,col2 = st.columns([1,2])

with col1:
    st.write("Strategy methode:")
    mode = st.selectbox("Way to play",["manual", "simulation", "compare strategies"], 1)
    if mode == "manual":
        manual = True
    elif mode == "simulation":
        simulation = True
    elif mode == "compare strategies":
        multi_strategy = True
        
with col2:
    st.info("Card counting system use HI-LO")
    st.info("Deviations from perfect strategy to increase edge of the player")
    st.info("The bet spread is how much you bet size changes depending on the true count (Conservative: 1-1, agressive 1 - ~2)")
    
st.write("")
st.write("")
settings = st.toggle("settings", False)

col1, col2= st.columns(2)

if settings:
    with col1:
        st.write("simulation settings")
        unit_value = st.number_input("bet per hand", 10, 10000, value= 100, step= 1)
        N_SESSIONS= st.number_input("Number of sesions:", 1, value= 100, step= 1)
        ROUNDS_PER_SESSION= st.number_input("Hands played per sesion", 1, value= 10000, step= 1)
        
    with col2:
        st.write("Table and game")
        min_bet= st.number_input("Minimum bet", 0, value= 10, step= 1)
        max_bet= st.number_input("Maximum bet", 500, value= 5000, step= 100)
        NUM_DECKS = st.number_input("Number of decks", 1, 12, value= 6, step= 1)
#------------------ Second part game playing ------------------------------

    
if manual:
    counting= False
    spread= "conservative"
    st.session_state.game = Game(num_decks=6, players=1, verbose=False, 
                            min_bet=min_bet, max_bet=max_bet,
                            manual= manual, counting=counting, spread=spread)
    
    st.session_state.phase = "playing"
    game = st.session_state.game
    
    if st.button("Run"):
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

if simulation:
    
    strategy_elected= st.selectbox("Select your strategy",["Perfect strategy", 
                                                            "Counting conservative","Counting aggressive", 
                                                            "Counting deviation conservative","Counting deviation aggressive"])
    

    if st.button("Run"):
        
        st.write(f"Running {N_SESSIONS} sessions x {ROUNDS_PER_SESSION} hands per strategy...\n")
        st.write(f"Aproximate time {int((N_SESSIONS * ROUNDS_PER_SESSION)/50_000)} seconds")
        summaries = {}
        
        col1, col2= st.columns([4,1])
        for name, config in CONFIGS.items():
            with col1:
                if strategy_elected == name:
                    results = run_sessions(config, N_SESSIONS, ROUNDS_PER_SESSION,  unit_value= unit_value)
                    summaries[name] = summarize(results)
            
                    game = Game(num_decks=NUM_DECKS, num_players=1, **config, min_bet=0, max_bet=10000000, surrender=True, DAS=True,)
                    game.players[0].unit_value = unit_value
                    matrix = build_montecarlo_matrix(results)
                    st_plot_montecarlo(matrix, name)
                else:
                    pass
        with col2:
            for name, s in summaries.items():
                st.write (f"'Mean$:   {s['mean_final_net_worth']:>12}")
                st.write(f"Std $:    {s['std_final_net_worth']:>12}")
                st.write(f"Min $:    {s['min_final_net_worth']:>12}")
                st.write(f"Max $:    {s['max_final_net_worth']:>12}")
                st.write(f"Ruin %:   {s['risk_of_ruin_pct']:>10}")
                st.write(f"Win %:    {s['win_rate_pct']:>10}")
            

if multi_strategy:
    
    strategy_elected = st.multiselect("Select strategies to compare", [
        "Perfect strategy", "Counting conservative", "Counting aggressive",
        "Counting deviation conservative", "Counting deviation aggressive"
    ])
    summaries = {}
    if st.button("Run"):
        title_plot = " vs ".join(strategy_elected)
        list_matrixes = []
        labels = []

        for name, config in CONFIGS.items():
            if name in strategy_elected:
                results = run_sessions(config, N_SESSIONS, ROUNDS_PER_SESSION, unit_value=unit_value)
                summaries[name] = summarize(results)

                game = Game(num_decks=NUM_DECKS, num_players=1, **config,
                            min_bet=0, max_bet=10000000, surrender=True, DAS=True)
                game.players[0].unit_value = unit_value
                matrix = build_montecarlo_matrix(results)
                list_matrixes.append(matrix)
                labels.append(name)

        st_multi_plot(list_matrixes, labels=labels, strategy=title_plot)