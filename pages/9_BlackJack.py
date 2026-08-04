import sys
from pathlib import Path
import streamlit as st
PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "P13_BlackJack"
sys.path.insert(0, str(PROJECT_DIR))

from game import Game
from models.participant import Player

if "phase" not in st.session_state:
    st.session_state.phase = "setup"

#------------------ First part home screen ------------------------------

if st.session_state.phase == "setup":
    st.title("Blackjack")

    players_names=[]
    players_chips=[]

    col1, col2 = st.columns(2)

    with col1: num_players = st.number_input(f"Number of players:", 0, 6, value=1)
            
    for i in range (num_players):
        col1, col2 = st.columns(2)
        with col1: name= st.text_input(f"Player {i+1} name", f"Player{i+1}")
        with col2: chip= st.number_input(f"chips:", 0, 999999990+i, value=100)
        players_names.append(name)
        players_chips.append(chip)      

    if st.button("Start Game"):
        players = [Player(name, chips) for name, chips in zip(players_names, players_chips)]
        st.session_state.game = Game(num_decks=6, players=players, verbose=False)
        st.session_state.phase = "playing"
        st.rerun()

#------------------ Second part game playing ------------------------------

elif st.session_state.phase == "playing":
    game = st.session_state.game
    player = game.players[0]
    hand = player.hands[0]

    st.write(f"Chips: {int(player.chips)}")

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
    if hand.cards:
        st.write("Your hand:")
        cols = st.columns(len(hand.cards))
        for col, card in zip(cols, hand.cards):
            col.image(card.image_path(), width=100)
        st.write(f"Value: {hand.value()}")
    else:
        st.write("Click 'New Round' to deal cards.")
    
    
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Hit"):
        hand.add(game.shoe.draw())
        st.rerun()
    if col2.button("Stand"):
        hand.resolved = True
        st.rerun()
    if col3.button("Double") and hand.can_double():
        game.double_down(player, hand)
        st.rerun()
    if col4.button("Split") and hand.can_split():
        game.split(player, hand)
        st.rerun()
