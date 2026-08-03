from projects.P13_BlackJack.models.card import Card, Suit
from projects.P13_BlackJack.models.shoe import Shoe
from projects.P13_BlackJack.models.hand import Hand
from projects.P13_BlackJack.models.participant import Player, Dealer

class Game():
    
    def __init__(self, num_decks: int = 6, num_players: int = 1, verbose: bool= True, local:bool = True):
        self.shoe = Shoe(num_decks)
        self.players = [Player(f"Player{i+1}") for i in range(num_players)]
        self.dealer = Dealer()
        self.verbose = verbose
        self.local = local 
        
    # ---------- ACTIONS: SPLIT + DOUBLE ----------
    def split(self, player: Player, hand: Hand):   
        if not hand.can_split():
            raise ValueError("Cannot split this hand")
        card1,card2= hand.cards
        new_hand1= Hand(from_split=True, bet=hand.bet)
        new_hand2= Hand(from_split=True, bet=hand.bet )
        new_hand1.add(card1)
        new_hand2.add(card2)
        player.chips -= hand.bet
        new_hand1.add(self.shoe.draw())
        new_hand2.add(self.shoe.draw())
        idx = player.hands.index(hand)
        player.hands[idx:idx+1] = [new_hand1, new_hand2]
        
    def double_down(self, player: Player, hand: Hand):
        if not hand.can_double():
            raise ValueError("Cannot double this hand")
        player.chips -= hand.bet
        hand.bet *= 2
        hand.doubled = True
        hand.add(self.shoe.draw())
    
    # ---------- PHASE 1: BETS + DEAL ----------
    def get_bet(self, player: Player) -> int:
        while True:
            raw = input(f"\n{player.name}, place a bet ({player.chips} chips available): ")
            try:
                bet = int(raw)
            except ValueError:
                print("Please enter a whole number.")
                continue

            if bet <= 0:
                print("Bet must be greater than 0.")
                continue
            if bet > player.chips:
                print("Not enough chips.")
                continue

            return bet
        
    def take_bets(self):
        for player in self.players:
            amount = self.get_bet(player)
            player.place_bet(player.hands[0], amount)

    def deal_initial(self):
        for _ in range(2):
            for player in self.players:
                player.hands[0].add(self.shoe.draw())
            self.dealer.hand.add(self.shoe.draw())
                  
    # ---------- PHASE 2: CHECK BLACKJACKS ----------
    def check_blackjacks(self):
        for player in self.players:
            hand = player.hands[0]
            if hand.is_blackjack():
                player.win_bet(hand, multiplier=1.5)
                hand.resolved = True
        
    # ---------- PHASE 3: EACH PLAYER PLAYS EACH HAND ----------
    def get_action(self, player: Player, hand: Hand) -> str:
            print(f"\n{player.name}'s hand: {[str(c) for c in hand.cards]} (value: {hand.value()})")
            print(f"Dealer showing: {self.dealer.hand.cards[0]}")
            
            options = ["hit", "stand"]
            if hand.can_double():
                options.append("double")
            if hand.can_split():
                options.append("split")
            
            print(f"Options: {options}")
            action = input("Choose action: \n").strip().lower()
            
            while action not in options:
                action = input(f"Invalid. Choose from {options}: ").strip().lower()
            
            return action
        
    def play_player(self, player: Player):
        i = 0
        while i < len(player.hands):
            hand = player.hands[i]
            if not hand.resolved:
                did_split = self.play_hand(player, hand)
                if did_split:
                    continue   
            i += 1
             
    def play_hand(self, player: Player, hand: Hand):    
        while True:
            action = self.get_action(player, hand)
            if action == "stand":
                return False
            elif action == "hit":
                hand.add(self.shoe.draw())
                if hand.is_bust():
                    return False
            elif action == "double" and hand.can_double():
                self.double_down(player, hand)
                return False
            elif action == "split" and hand.can_split():
                self.split(player, hand)
                return True
        
    # ---------- PHASE 4: DEALER PLAYS ----------
    def play_dealer(self):
        while self.dealer.should_hit():
            self.dealer.hand.add(self.shoe.draw())
    
    # ---------- PHASE 5: RESOLVE ----------
    def resolve_round(self):
        for player in self.players:
            for hand in player.hands:
                if hand.resolved:
                    continue
                self.settle(player, hand)
        
    def settle(self, player: Player, hand: Hand):
        if hand.is_bust():
            return
        dealer_val= self.dealer.hand.value()
        if self.dealer.hand.is_bust() or hand.value() > dealer_val:
            player.win_bet(hand)
        elif hand.value() < dealer_val:
            pass
        else:
            player.chips += hand.bet
        
    # ---------- FULL ROUND ----------
    def play_round(self):
        
        self.take_bets()
        self.deal_initial()
        self.check_blackjacks()
        for player in self.players:
            self.play_player(player)
        self.play_dealer()
        self.resolve_round()
        for player in self.players:
            player.chip_history.append(int(player.chips))
        self.log()
            
    def log(self):
        if self.verbose:
            for player in self.players:
                if len(player.chip_history)>1:
                    if player.chip_history[-1] > player.chip_history[-2]:
                        print(f"\n{player.name} won {player.chip_history[-1] - player.chip_history[-2]} and has {player.chip_history[-1]} chips left")
                    elif player.chip_history[-1] < player.chip_history[-2]:
                        print(f"\n{player.name} lost {player.chip_history[-1] - player.chip_history[-2]} and has {player.chip_history[-1]} chips left")
                    else:
                        print(f"\n{player.name} draw and has {player.chip_history[-1]} chips left")
                        
Game(num_decks=6, num_players=2).play_round()