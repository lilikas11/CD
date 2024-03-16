# import threading
# import time
# import redis
import argparse
import random
# import selectors
# import socket
# import protocolo
# import signal
from protocolo import CDProto
from utils import score
from player import Player
import protocolo
from protocolo import CDProto
from utils import score

#Obrigatório:
# - Tirar uma carta a mais--> feito
# - Mentir sobre ter ganho --> feito
# - Mentir o valor das suas cartas --> feito
# - Mentir sobre o valor de hash obtido do deck --> feito
#Opcional:
# - Retirar carta do baralho--> feito
# - Mentir que houve batota quando escolhido para hashing -> feito


class Bad_Player(Player):
    
    def read(self, conn, mask):
        """Read data from socket."""
        try:
            msg = CDProto.recv_msg(conn)
            if not msg:
                self.r.flushdb()
                print("Player disconnected")
                print("End of game")
                print("There is no winner")
                exit()
            if msg:
                if (msg.command == "played"):
                    self.jogar(self_port)
                elif (msg.command == "receivedCard"):
                    self.playersWithCards +=1
                    if(self.playersWithCards == len(self.todosPlayers)):
                        print("All players have received their 2 cards!!")
                        print("Waiting for first player to play... ")
                    if(self.playersWithCards == len(self.todosPlayers) and (min(self.todosPlayers) == self.self_port)):
                        self.jogar(self_port)
                elif (msg.command == "defeated"):
                    print("Player", msg.player_port, "declared defeat")
                    self.players.remove(msg.player_port) #remover da lista para que este não jogue mais, só no hashing é que vai ser executado
                    self.todosPlayers.remove(msg.player_port)
                    if(len(self.todosPlayers) == 1 and self_port in self.todosPlayers):
                        print("Player", self_port, "declared Victory with", self.pontuacao_funct(self.self_port), "points")
                        self.winner = str(self.self_port)
                        print("But there's still some hashing to do.....")
                        msg = CDProto.playerWin(self_port)
                        self.sendAll(msg)
                        self.hashing(self_port)  
                elif (msg.command == "stand"):
                    print("Player", msg.player_port, "gave stand")
                elif (msg.command == "win"):
                    print("Player", msg.player_port, "declared victory")
                    self.winner = str(msg.player_port)
                    self.hashing(msg.player_port)
                elif(msg.command == "decision"):
                    self.decision.append(msg.decision)
                    if(len(self.decision) == 2):
                        print("VOTE-REQUEST 1 :", self.decision[0])
                        print("VOTE-REQUEST 2 :", self.decision[1])
                        if((self.decision[0] == "VOTE-COMMIT") and (self.decision[1] == "VOTE-COMMIT")):
                            print("Decision: No one cheated ")
                            print("Player", self.winner, "has won!!!")
                            decision = "GLOBAL-COMMIT"
                            self.r.flushdb()
                        else:
                            print("Decision: Someone cheated.")
                            print("There is no winner.")
                            decision = "GLOBAL-ABORT"
                            self.r.flushdb()
                        msg = CDProto.coorDecision(decision)
                        self.sendAll(msg)
                        self.r.flushdb() 
                        exit()
                elif(msg.command == "coorDecision"):
                    coorDecision = msg.decision
                    if(coorDecision == "GLOBAL-COMMIT"):
                       print("The coordinator has decided: No one cheated.")
                       print("O jogador", self.winner, "ganhou!!!")
                    else:
                       print("The coordinator has decided: Someone has cheated.")
                       print("There is no winner")
                    self.r.flushdb()
                    exit()
                        
                    
        except:
            conn.close()
            self.r.flushdb()
            exit(0)
        # signal.pause() 
        
    def jogar(self, self_port):
        #jogar cartas
        #try:
        valores = self.r.lrange(self_port, 0, -1)
        cards=valores
        if self.numero_jogada>0:
            print("I have played", self.numero_jogada, "times")
        print("You have", self.pontuacao_funct(self.self_port), "points. Do you want to risk it?")
        jogada=self.interact_with_user1(cards)
        if(jogada=='H'):
            if(self.pontuacao > 21):
                print("You have more than 21 points, your only way is to give (D)efeat")
                # remover carta
                print("Or do you want to remove a card from your deck? *wink wink* .... (Y/N)")
                key = " "
                while key not in "YN":
                    key = input("> ").upper()
                if(key == "Y"):
                    self.remover_ultima_carta(self_port)
                self.jogar(self_port)
                return 
            if(self.pontuacao==21):
                print("You've reached 21, claim your prize by giving (W)in ")
                self.jogar(self_port)
                return 
            self.pedir_cartas(self_port)
            # adicionar carta
            key = " "
            while key not in "N":
                print("Draw an extra card? (Y/N)")
                key = input("> ").upper()
                if(key == "Y"):
                    self.add_carta_fake(self_port)
            key = " "
            while key not in "N":
                print("Do you want to remove a card? (Y/N)")
                key = input("> ").upper()
                if(key == "Y"):
                    self.remover_ultima_carta(self_port)
                        
        elif(jogada=='S'):
            if(self.pontuacao > 21):
                print("You have more than 21 points, your only way is to give (D)efeat")
                print("Or do you want to remove your last card from your deck? *wink wink* .... (Y/N)")
                key = " "
                while key not in "YN":
                    key = input("> ").upper()
                if(key == "Y"):
                    self.remover_ultima_carta(self_port)
                self.jogar(self_port)
                return 
            msg = CDProto.playerStand(self_port)
            self.sendAll(msg)     
        elif(jogada=='W'):
            if(self.pontuacao != 21):
                print("You don't have a score to win")
                print("Do you want to lie about having won?... Y/N")
                key = " "
                while key not in "YN":
                    key = input("> ").upper()
                if(key == "Y"):
                    self.pontuacao = 21    
            if(self.pontuacao > 21):
                print("You have more than 21 points, your only way is to give (D)efeat")
                print("Or do you want to remove your last card from your deck? *wink wink* .... (Y/N)")
                key = " "
                while key not in "YN":
                    key = input("> ").upper()
                if(key == "Y"):
                    self.remover_ultima_carta(self_port)
                self.jogar(self_port)
                return 
            elif(self.pontuacao<21):
                print("You haven't won, yet... ")
                self.jogar(self_port)
                return 
            self.winner = str(self.self_port)
            print("I have proclaimed victory with ", self.pontuacao_funct(self_port), "points")
            if(len(self.PlayersForHashing) > 1):
                print("But there's still some hashing to do....")
                msg = CDProto.playerWin(self_port)
                self.sendAll(msg)
                self.hashing(self_port)
            else:
                self.r.flushdb()
                exit()     
            return
        elif(jogada=='D'):
            print("I have lost with", self.pontuacao_funct(self.self_port), "points")
            if(len(self.players) > 0):
                msg = CDProto.playerDefeated(self_port)
                self.sendAll(msg)
                if(len(self.todosPlayers) == 2):
                    self.todosPlayers.remove(self.self_port)
                    return
            else:
                self.r.flushdb()
                exit()
        # dizer a outro que já pode jogar    
        if(jogada == "D"):
            player_sock = self.nextPlayer(True)
        else:
            player_sock = self.nextPlayer()
        if(player_sock != "eu"):
            message = CDProto.played(self_port)
            CDProto.send_msg(player_sock, message)
            print("Waiting for the next players to play... ")
        else:
            self.jogar(self_port)
        self.numero_jogada+=1
        return 
        # except Exception as e:
        #     print("Ocorreu um erro:", str(e))
        #     self.r.delete(self_port)
    
    #funçoes de mentirinha
    
    def escolhido_hashing(self, self_port):
        if(self_port in self.chosen_ones):
            print("You have been chosen for hashing")
            mensagem= protocolo.ir_ao_hashing(self_port)
            player_socket2 = self.create_socket()
            player_socket2.sendall(mensagem.encode('utf-8'))
            carta=player_socket2.recv(32).decode('utf-8')
            # carta é a pontuação do hash do deck
            print("Checking Hashing...... ")
            if (self.verificar_combinacoes(carta)):
                if(len(self.todosPlayers) != 1):
                    # deram win por pontos
                    print("Hash Result: No one cheated")
                    print("Checking pontuation..... ")
                    if((int(self.dic_pont[self.winner]) != 21)):
                        print("Pontuation Result: Winner cheated. -> VOTE-ABORT")
                        decision = 'VOTE-ABORT'
                    else:
                        decision = 'VOTE-COMMIT'
                else:
                    print("Hash Result: No one cheated -> VOTE-COMMIT")
                    decision = 'VOTE-COMMIT'
            else:
                print("Hash Result: Someone cheated. -> VOTE-ABORT")
                decision = 'VOTE-ABORT'
                # mentir sobre o hash
                
            if(decision == 'VOTE-ABORT'):
                if not self.verificar_combinacoes(carta):
                    print("Do you want to lie about the Hash Result?... (Y/N)")
                elif ((len(self.todosPlayers) != 1) and (int(self.dic_pont[self.winner]) != 21)):
                    print("Do you want to lie about the pontuation Result?... (Y/N)")
                key = " "
                while key not in "YN":
                    key = input("> ").upper()
                if(key == "Y"):
                    decision = 'VOTE-COMMIT'
            else:
                # mentir que houve batota
                print("Pretend there was cheating?... (Y/N)")
                key = " "
                while key not in "YN":
                    key = input("> ").upper()
                if(key == "Y"):
                    decision = 'VOTE-ABORT'  
                    
            if(len(self.PlayersForHashing) == 2):
                if(decision == 'VOTE-COMMIT'):
                    print("No one cheated ")
                    print("Player", self.winner, "has won!!!")
                else:
                    print("The other player cheated!!!")
                    print("End of game")
                self.r.flushdb()
                exit()
                
                
            print("Sending decision to coordinator...")
            # socket
            # hash == hash das cartas
            # vote-commit ou vote-abort
            port_coordenador = self.escolherCoordenador()
            msg = CDProto.playerDecision(decision)
            port_coordenador = int(port_coordenador)
            self.decision.append(decision)
            if(self.self_port != port_coordenador):
                actual_player = port_coordenador     
                player_sock = self.player_sockets[actual_player]
                CDProto.send_msg(player_sock, msg)

    def add_carta_fake(self, self_port):
        possiblecards = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "K", "J","D","A"]
        card = random.choice(possiblecards)
        print(f"Drawed Fake Card: {card}")
        self.r.lpush(self_port, card.strip())
        print("Final Score:", self.pontuacao_funct(self.self_port))
        

    def remover_ultima_carta(self, self_port):
        carta=self.r.lindex(self_port, 0)
        self.r.lrem(self.self_port, 0, carta)
        cartas_finais=self.r.lrange(self_port, 0, -1)
        # print("Final Cards:", cartas_finais)
        print("Final Score:", self.pontuacao_funct(self.self_port))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--self', required=True, type=int)
    parser.add_argument('-p', '--players', nargs='+', required=False, type=int)
    args = parser.parse_args()
    args_namespace = vars(args)
    self_port = args_namespace['self']
    players = args_namespace['players']
    if not (args.players):
        players = []

    if (args.players ) and (args.self in args.players):
        print(f"{args.self} must not be part of the list of players")
        exit(1)
        
    bp = Bad_Player(self_port, players)
    print("")
    bp.loop()
    # p.main(args.self) #falta args.players porque só temos um jogador