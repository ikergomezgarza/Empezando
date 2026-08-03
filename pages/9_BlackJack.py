from projects.P13_BlackJack.game import Game
import streamlit as st

Game(num_decks=6, num_players=2).play_round()