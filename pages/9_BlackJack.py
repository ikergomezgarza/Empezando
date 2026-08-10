import sys
from pathlib import Path
import streamlit as st
PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "P13_BlackJack"
sys.path.insert(0, str(PROJECT_DIR))

from projects.P13_BlackJack.game import Game
from projects.P13_BlackJack.main import run_sessions, summarize, main
from collections import Counter


modify_parameters = False
min_bet= 0
max_bet = 1000000
manual= False
counting= False
spread= "conservative"

if "phase" not in st.session_state:
    st.session_state.phase = "setup"

#------------------ First part home screen ------------------------------


st.title("Blackjack")
st.write("")
modify_parameters = st.toggle("Modify parameters")

if modify_parameters:
    
    col1,col2 = st.columns(2)
    
    with col1:
        st.write("Strategy methode:")
        automatic = st.toggle("Play Automatic:")
        if automatic:
            counting = st.toggle("Card counting:")
        if counting:
            spread = st.selectbox("Spread:", ["conservative", "aggressive"])
        
    with col2:
        st.write("Table and game")
        min_bet= st.slider("Minimum bet", 0, value= 10, step= 1)
        max_bet= st.slider("Maximum bet", 500, value= 5000, step= 100)


st.session_state.game = Game(num_decks=6, players=1, verbose=False, 
                             min_bet=min_bet, max_bet=max_bet,
                             manual=manual, counting=counting, spread=spread)


#------------------ Second part game playing ------------------------------
if st.button("Run"):
    st.session_state.phase = "playing"
    
    game = st.session_state.game
    
    if manual:
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

    if not manual:
        
        game.simulate()
        net_worth = game.player.net_worth
        went_negative = any(nw < 0 for nw in net_worth)

        wl = Counter(
            "W" if b > a else "L" if b < a else "D"
            for a, b in zip(net_worth, net_worth[1:])
        )

        game.results.append({
            "final_net_worth": net_worth[-1],
            "went_negative": went_negative,
            "wins": wl["W"],
            "losses": wl["L"],
            "draws": wl["D"],
        })