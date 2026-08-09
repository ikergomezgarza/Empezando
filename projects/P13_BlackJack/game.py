from models.card import Card, Suit
from models.shoe import Shoe
from models.hand import Hand
from models.participant import Player, Dealer
import math

class Game():
    
    BET_RAMPS = {
        "conservative": {2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8},
        "aggressive":   {2: 2, 3: 4, 4: 8, 5: 12, 6:16 , 7: 20},
    }
    
    def __init__(self, num_decks: int = 6, num_players: int = 1, players: list[Player] = None,
                 min_bet: int = 10, max_bet : int = 5000, 
                 manual = True, counting= False, deviations = False, spread: str = "aggressive",
                 verbose: bool= True, local:bool = True):
        
        self.shoe = Shoe(num_decks)
        self.players = players if players is not None else [Player(f"Player{i+1}") for i in range(num_players)]
        self.dealer = Dealer()
        self.min_bet = min_bet
        self.max_bet = max_bet
        self.manual = manual
        self.counting = counting
        self.deviations = deviations
        self.spread = spread
        self.verbose = verbose
        self.local = local 
        self.stats = { "hard": {"count": 0, "net": 0, "wins": 0},
                    "soft": {"count": 0, "net": 0, "wins": 0},
                    "pair_split": {"count": 0, "net": 0, "wins": 0},
                    "blackjack": {"count": 0, "net": 0},
                    "dealer_blackjack": {"count": 0, "net": 0},
                    "double": {"count": 0, "net": 0, "wins": 0},
                    "bust": {"count": 0, "net": 0},}
        self.total_bet = 0
        self.total_return = 0
        
    # ---------- ACTIONS: SPLIT + DOUBLE + INSURANCE ----------
    def split(self, player: Player, hand: Hand) -> bool:
        if not hand.can_split():
            raise ValueError("Cannot split this hand")
        if player.chips < hand.bet:
            player.cash_in(initial=False)
        if player.chips < hand.bet:
            return False   # couldn't afford it — report failure
        card1, card2 = hand.cards
        new_hand1 = Hand(from_split=True, bet=hand.bet, split_count=hand.split_count + 1)
        new_hand2 = Hand(from_split=True, bet=hand.bet, split_count=hand.split_count + 1)
        new_hand1.add(card1)
        new_hand2.add(card2)
        player.chips -= hand.bet
        new_hand1.add(self.shoe.draw())
        new_hand2.add(self.shoe.draw())
        
        idx = player.hands.index(hand)
        player.hands[idx:idx+1] = [new_hand1, new_hand2]
        return True 
        
    def double_down(self, player: Player, hand: Hand):
        if not hand.can_double():
            raise ValueError("Cannot double this hand")
        if player.chips < hand.bet:
            player.cash_in(initial=False)
        if player.chips < hand.bet:
            return  # still can't cover it after buy-in — treat as a stand, no double happens
        player.chips -= hand.bet
        hand.bet *= 2
        hand.doubled = True
        hand.add(self.shoe.draw())
        
    def insurance(self):
        
        if self.dealer.hand.can_insure():
            
            for player in self.players:
                for hand in player.hands:
                    if self.manual:   
                        options = ["yes", "no"]
                        print(f"Do you want to insure your bet: {options}")
                        action = input("Choose action: \n").strip().lower()
                        while action not in options:
                            action = input(f"Invalid. Choose from {options}: ").strip().lower()  

                        if action == "yes":
                            player.chips -= .5 * hand.bet
                            hand.insurance_bet += .5 * hand.bet
                        else:
                            continue

                    elif not self.manual and self.counting and self.deviations:
                        if round(self.shoe.true_count) >= 3:
                            player.chips -= .5 * hand.bet
                            hand.insurance_bet += .5 * hand.bet
                        else: 
                            pass
                    else:
                        pass
            
            if self.verbose:
                print("insurance round finished")
                
            for player in self.players:
                for hand in player.hands: 
                    if self.dealer.hand.is_blackjack():
                        if hand.is_blackjack():
                            player.push_bet(hand)   
                        else:
                            hand.bet = 0  
                        if hand.insurance_bet > 0:
                            player.chips += hand.insurance_bet * 3
                            hand.insurance_bet = 0
                        hand.resolved = True
                    else:
                        hand.insurance_bet = 0          
                        
    def perfect_play(self, hand: Hand, dealer_upcard: Card) -> str:
        
        rank = hand.cards[0].rank
        soft = hand.is_soft()
        split= hand.can_split()
        double= hand.can_double()
        player_val = hand.value()
        dealer_val = dealer_upcard.value
        count = math.floor(self.shoe.true_count)
        
                
        if split:
            # Main blocks (All the splits)---------------
            if rank in ("8", "A"):
                return "split"
            if rank == "9" and dealer_val in (2, 3, 4, 5, 6, 8, 9):
                return "split"
            if rank == "7" and dealer_val in (2, 3, 4, 5, 6, 7):
                return "split"
            if rank == "6" and dealer_val in (2, 3, 4, 5, 6):
                return "split"
            if rank == "4" and dealer_val in (5, 6):
                return "split"
            if rank in ("2", "3") and dealer_val in (2, 3, 4, 5, 6, 7):
                return "split"
            
        # Deviation if counting cards gives a 10-40% more
        if self.counting and self.deviations and not split and not soft:
            if count < 0:
                if player_val == 12 and dealer_val == 4:
                    return "hit"
            if count < -1:
                if player_val == 13 and dealer_val == 2:
                    return "hit"
                if player_val == 12 and dealer_val == 6:
                    return "hit"
            if count < -2:
                if player_val == 13 and dealer_val == 3:
                    return "hit"
                if player_val == 12 and dealer_val == 5:
                    return "hit"
            if count >= 0:
                if player_val == 16 and dealer_val == 10:
                    return "stand"
            if count >= 1:
                if player_val == 11 and dealer_val == 11:
                    return "double" if double else "hit"
                if player_val == 9 and dealer_val == 2:
                    return "double" if double else "hit"
            if count >= 2:
                if player_val == 12 and dealer_val == 3:
                    return "stand"
                if player_val == 15 and dealer_val == 9:
                    return "stand"
            if count >= 3:
                if player_val == 12 and dealer_val == 2:
                    return "stand"
                if player_val == 9 and dealer_val == 7:
                    return "double" if double else "hit"
                if player_val == 14 and dealer_val == 10:
                    return "stand"
            if count >= 4:
                if player_val == 15 and dealer_val == 10:
                    return "stand"
                if player_val == 10 and dealer_val == 10:
                    return "double" if double else "hit"
                if player_val == 10 and dealer_val == 11:
                    return "double" if double else "hit"
            if count >= 5:
                if player_val == 16 and dealer_val == 9:
                    return "stand"
        
        if not soft:
            #First doubles
            if player_val == 11 and double:
                return "double"
            if player_val == 10 and dealer_val in (2, 3, 4, 5, 6, 7, 8, 9) and double:
                return "double"
            if player_val == 9 and dealer_val in (3, 4, 5, 6) and double:
                return "double"
            #Second all stands
            if player_val >= 17:
                return "stand"
            if player_val in (13, 14, 15, 16) and dealer_val in (2, 3, 4, 5, 6):
                return "stand"
            if player_val == 12 and dealer_val in (4, 5, 6):
                return "stand"
            return "hit"
            
        else:
             #Exceptions cases before -------------------
            if double and dealer_val <= 6:
                if player_val == 19 and dealer_val == 6:
                    return "double"
                elif player_val == 18 and dealer_val >= 3:
                    return "double"
                elif player_val == 17 and dealer_val >= 3:
                    return "double"
                elif player_val in (15, 16) and dealer_val >= 4:
                    return "double"
                elif player_val in (13, 14) and dealer_val >= 5:
                    return "double"

            if player_val in (19, 20):
                return "stand"
            elif player_val == 18 and dealer_val <= 8:
                return "stand"
            elif player_val == 18 and dealer_val >= 9:
                return "hit"
            else:
                return "hit"
       
    # ---------- PHASE 1: BETS + DEAL ----------
    
    def bet_counting(self, player: Player):
        ramp = self.BET_RAMPS[self.spread]
        tc = math.floor(self.shoe.true_count)
        if tc < 2:
            return self.min_bet
        capped_tc = min(tc, max(ramp.keys()))
        return ramp[capped_tc] * player.unit_value
                    
                
    def get_bet(self, player: Player) -> int:
        
        if self.counting:
            return self.bet_counting(player)
        
        if not self.manual:
            return player.unit_value

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
            if bet < self.min_bet:
                print("Bet must be greater than table minimum.")
                continue
            
            if bet > player.chips:
                decision = input("Not enough chips do you want to buy in?")
                if decision == "yes":
                    player.cash_in(initial=False)
                else:
                    print("Not enough money")
                    continue

            return bet
        
    def take_bets(self):
        for player in self.players:
            amount = self.get_bet(player)
            if amount > self.max_bet:
                amount = self.max_bet
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
            if hand.is_blackjack() and self.dealer.hand.is_blackjack():
                player.push_bet(hand)
                hand.resolved = True
            elif hand.is_blackjack():
                self.stats["blackjack"]["count"] += 1
                self.stats["blackjack"]["net"] += hand.bet * 1.5
                player.win_bet(hand, multiplier=1.5)
                hand.resolved = True
    
    def check_dealer_blackjack(self):
        if self.dealer.hand.is_blackjack():
            for player in self.players:
                for hand in player.hands:
                    self.stats["dealer_blackjack"]["count"] += 1
                    if hand.is_blackjack():
                        player.push_bet(hand)
                    else:
                        self.stats["dealer_blackjack"]["net"] -= hand.bet
                        hand.bet = 0
                    hand.resolved = True
        
    # ---------- PHASE 3: EACH PLAYER PLAYS EACH HAND ----------
    def get_action(self, player: Player, hand: Hand, dealer: Dealer = None) -> str:
        
        if not self.manual:
            if not self.manual:
                action = self.perfect_play(hand, dealer.hand.cards[0])
                return action
            
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
                did_split = self.play_hand(player, hand, self.dealer)
                if did_split:
                    continue   
            i += 1
             
    def play_hand(self, player: Player, hand: Hand, dealer: Dealer):  
        if hand.category is None:
            hand.category = "soft" if hand.is_soft() else "hard"
        if hand.from_split and hand.split_count > 0 and hand.cards[0].rank == "A" and len(hand.cards) == 2:
            return False
        guard = 0  
        while True:
            guard += 1
            if guard > 30:
                raise RuntimeError(
                    f"play_hand stuck: cards={[str(c) for c in hand.cards]} "
                    f"value={hand.value()} can_double={hand.can_double()} "
                    f"can_split={hand.can_split()} resolved={hand.resolved}"
                )
            action = self.get_action(player, hand, dealer)
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
                did_split = self.split(player, hand)
                if not did_split:
                    return False   
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
        
        if self.shoe.can_rebuild_deck():
            self.shoe.build()
        
    def settle(self, player: Player, hand: Hand):
        bet = hand.bet
        cat = hand.category or "hard"
        
        if hand.is_bust():
            self.stats["bust"]["count"] += 1
            self.stats["bust"]["net"] -= bet
            self.stats[cat]["count"] += 1
            self.stats[cat]["net"] -= bet
            return
        
        dealer_val = self.dealer.hand.value()
        if self.dealer.hand.is_bust() or hand.value() > dealer_val:
            player.win_bet(hand)
            self.stats[cat]["count"] += 1
            self.stats[cat]["wins"] += 1
            self.stats[cat]["net"] += bet
            if hand.doubled:
                self.stats["double"]["count"] += 1
                self.stats["double"]["wins"] += 1
                self.stats["double"]["net"] += bet
        elif hand.value() < dealer_val:
            self.stats[cat]["count"] += 1
            self.stats[cat]["net"] -= bet
            if hand.doubled:
                self.stats["double"]["count"] += 1
                self.stats["double"]["net"] -= bet
        else:
            player.chips += bet
            self.stats[cat]["count"] += 1
        
    # ---------- FULL ROUND ----------
    def play_round(self):
        
        self.take_bets()
        self.deal_initial()
        self.check_dealer_blackjack()
        #self.insurance()
        self.check_blackjacks()
        for player in self.players:
            self.play_player(player)
        self.play_dealer()
        self.resolve_round()
        self.dealer.hand = Hand()
        for player in self.players:
            player.hands = [Hand()]
            player.net_worth.append(int(player.chips + player.bankroll))
        self.log()
    
    # ---------- PHASE 0: SIMULATION ----------
    
    def inicial_buy_in(self):
        
        for player in self.players:
            player.cash_in()
            
    def final_buy_out(self):
        for player in self.players:
            player.cash_out()
            
    def simulate(self, n_simulations: int = 1000):
        
        self.inicial_buy_in()
        for i in range(n_simulations):
            self.play_round()
        self.final_buy_out()
        self.print_stats()
            
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
                        
    def print_stats(self):
        print(f"\n{'Category':<18}{'Count':>10}{'Net $':>14}{'Net/Hand':>12}{'Win %':>10}")
        for cat, d in self.stats.items():
            if d["count"] == 0:
                continue
            net_per = d["net"] / d["count"]
            win_pct = (d.get("wins", 0) / d["count"] * 100) if "wins" in d else None
            win_str = f"{win_pct:.1f}" if win_pct is not None else "-"
            print(f"{cat:<18}{d['count']:>10}{d['net']:>14.0f}{net_per:>12.3f}{win_str:>10}")
        
       