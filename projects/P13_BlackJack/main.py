from game import Game



if __name__ == "__main__":
    game = Game(num_players=1)
    
    for i in range(3):
        game.play_round()