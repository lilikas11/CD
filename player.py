import hashlib
import itertools
import threading
import redis
import argparse
import selectors
import socket
import protocolo
import signal
from protocolo import CDProto
from utils import score

class Player:

    def __init__(self, self_port, players):
        self.self_port = self_port  # player port
        self.players = []   
        self.todosPlayers = [self_port] # list of players ports
        for player in players:
            self.players.append(player)
            self.todosPlayers.append(player)
        self.todosPlayers = sorted(self.todosPlayers)
        self.PlayersForHashing = tuple(self.todosPlayers)
        self.OthersPlayersFromBegin = tuple(self.players)
        # inicializar a socket do jogador
        self.player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.player_socket.bind(("localhost", self_port))
        self.player_socket.listen(100)
        self.player_sel = selectors.DefaultSelector()
        
        # vars globais
        self.chosen_ones=[] #lista de jogadores que vão ao hashing
        self.player_sockets = {}    # port: socket
        self.r = 0
        self.numero_jogada=0
        self.pontuacao=0
        self.ready_players = 1
        self.all_playersReady = False
        self.messagesRead = 0
        self.playersWithCards = 1
        self.lst_pontuacoes=[]
        self.dic_pont={}
        self.decision=[]
        self.winner = ""

        if(len(players) > 0):
            self.player_sel.register(self.player_socket, selectors.EVENT_READ, self.accept)
            self.connect_players_thread = threading.Thread(target=self.connect_players)
            self.connect_players_thread.start()
        else:
            self.main()
    
    def accept(self, sock, mask):
        """Accept new connection."""
        conn, addr = sock.accept()
        print("A player has connected")
        conn.setblocking(False)
        self.player_sel.register(conn, selectors.EVENT_READ, self.read)
        self.player_sockets[addr[1]] = conn
        
        # self.player_sel.select()
        
    def connect_players(self):
        """Conectar aos outros jogadores e esperar até que todos estejam prontos."""
        print("Waiting for remaining players...")
        for port in self.players:
            player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            while True:
                try:                
                    player_socket.connect(("localhost", port))
                    self.player_sockets[port] = player_socket
                    break
                except ConnectionRefusedError:
                    # Caso a conexão seja recusada, tentar novamente
                    continue
        return 
        
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
        
    def signal_handler(self, signal, frame):
        # Função para limpar Redis, quando se faz CTRL_C
        print("\nInterrumpted program. Cleaning Redis...")
        self.r.flushdb()  # Limpar todos os dados do Redis
        print("Redis is clean. Shutting down program.")
        exit(0)

    def create_socket(self):
        player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        player_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        player_socket.connect(('localhost', 5000))
        return player_socket

    def main(self): #retirei players_port porque só temos um jogador
        signal.signal(signal.SIGINT, self.signal_handler)
        print("Let's play!")
        self.port=self.self_port
        self.r = redis.Redis(host='localhost', port=6379) #numero porta random
        # deck_process = subprocess.Popen(['python', 'deck.py'])
        self.cartas_iniciais(self.self_port)
        return 
            
            
        #enviar mensagem pedir 2 cartas iniciais   
    def cartas_iniciais(self, self_port):
        n=0
        while(n<2):
            self.pedir_cartas(self_port)
            n+=1
            if n==2:
                if(len(self.players) > 0):
                    msg=CDProto.receivedCard()
                    print("Waiting for other players cards... ")
                    self.sendAll(msg)
                else:
                     self.jogar(self_port)

    def pedir_cartas(self, self_port):
        self.player_socket = self.create_socket()
        mensagem=protocolo.pedir_cartas(self_port)
        self.player_socket.sendall(mensagem.encode('utf-8'))
        carta=self.player_socket.recv(2).decode('utf-8')
        print(f"Card:'{carta.strip()}'")
        self.r.lpush(self_port, carta.strip())
        print("Actual Score:", self.pontuacao_funct(self.self_port))
        
        
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
                self.jogar(self_port)
                return 
            if(self.pontuacao==21):
                print("You've reached 21, claim your prize by giving (W)in ")
                self.jogar(self_port)
                return 
            self.pedir_cartas(self_port)
        elif(jogada=='S'):
            if(self.pontuacao > 21):
                print("You have more than 21 points, your only way is to give (D)efeat")
                self.jogar(self_port)
                return 
            msg = CDProto.playerStand(self_port)
            self.sendAll(msg)     
        elif(jogada=='W'):
            if(self.pontuacao > 21):
                print("You have more than 21 points, your only way is to give (D)efeat")
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
            # e se eu quiser desistir?
            # if(self.pontuacao<21):
            #     print("Continue playing, you still have a chance to win... ")
            #     self.jogar(self_port)
            #     return 
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
        
    def escolhido_hashing(self, self_port): 
        if(self_port in self.chosen_ones):
            print("You have been chosen for hashing")
            mensagem= protocolo.ir_ao_hashing(self_port)
            player_socket2 = self.create_socket()
            player_socket2.sendall(mensagem.encode('utf-8'))
            carta=player_socket2.recv(32).decode('utf-8')
            # carta é a pontuação do hash do deck
            print("Checking Hashing..... ")
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
                
    def escolherCoordenador(self):
    # ver quem é o coordenador:
        for chave in self.r.scan_iter():
            pontuacao=0
            chaves=self.r.lrange(chave, 0, -1)
            for i in chaves:
                i=i.decode("utf-8")[0]
                pontuacao+=score(i)
                self.dic_pont[chave.decode("utf-8")]=pontuacao
        pont_c =min(self.dic_pont.values())
        for port in self.dic_pont.keys():
            if self.dic_pont[port] == pont_c: 
                port_coordenador=port
                break
        return(port_coordenador)
    
    
    def verificar_combinacoes(self, hash_desejado):
        hash_desejado = str(hash_desejado)
        self.lst_pontuacoes = list(self.lst_pontuacoes)
        # Gerar todas as combinações possíveis da ordem das cartas
        
        permutations = itertools.permutations(self.lst_pontuacoes)
        for permutation in permutations:
            # Converter a permutação em uma lista
            permutation_list = list(permutation)
            hash_calculado = hashlib.md5(f'{permutation_list}'.encode('utf-8')).hexdigest()
            # Verificar se a permutação corresponde à lista desejada
            if hash_calculado == hash_desejado:
                return True
        return False
            
            
    def pontuacao_funct(self, player_port):
        player_port = player_port
        self.pontuacao = 0
        valores = self.r.lrange(player_port, 0, -1)
        for cards in valores:
            cards=cards.decode("utf-8")[0]
            self.pontuacao += score(cards)

        return self.pontuacao
    
    def nextPlayer(self, defeated = False):
        actual_player = self.self_port
        player_index = self.todosPlayers.index(self.self_port)
        if len(self.todosPlayers) == 1:
            return "eu"
        elif player_index == (len(self.todosPlayers) - 1):
            player_index = 0
        else:
            player_index +=1
        actual_player = self.todosPlayers[player_index]
        player_sock = self.player_sockets[actual_player]
        if defeated:
            self.todosPlayers.remove(self.self_port)
        return player_sock

    def hashing(self, winner_port):
        #ver valores do redis
        for chave in self.r.scan_iter():
            chaves=self.r.lrange(chave, 0, -1)
            for i in chaves:
                i=i.decode("utf-8")
                self.lst_pontuacoes.append(i)
        print("Cards in table: ", self.lst_pontuacoes)
        port_coordenador = self.escolherCoordenador()
        lenght=len(self.PlayersForHashing)
        if(lenght==1):
            self.chosen_ones.append(self.PlayersForHashing[0])
        if(lenght==2):
            self.chosen_ones.append(self.PlayersForHashing[0])
            self.chosen_ones.append(self.PlayersForHashing[1])
        if(lenght>=3):
            #ver quem enviou mensagem de vitoria
            port_coordenador = int(self.escolherCoordenador())
            if(self.self_port == int(port_coordenador)):
                print("I am the coordinator.")
                print("Waiting for players decision, which have been elected to hash")
            winner_port = int(self.winner)
            if(lenght == 3):
                for i in self.PlayersForHashing:
                    if (i != int(port_coordenador)):
                        self.chosen_ones.append(i)
            if(lenght>=4):
                lst_values={}
                #já temos só 3, porque o que ganhou foi-se embora
                self.PlayersForHashing4More = list(self.PlayersForHashing)
                self.PlayersForHashing4More.remove(winner_port)
                self.PlayersForHashing4More.remove(port_coordenador)
                for chave in self.PlayersForHashing4More:
                    print(chave)
                    chave = str(chave)
                    lst_values[chave] = self.dic_pont[chave]
                print(lst_values.items())
                sorted_lst = sorted(lst_values.items(), key=lambda x: x[1])
                jogadores_ordenados = [item[0] for item in sorted_lst]
                print(jogadores_ordenados)
                jogador1 = int(jogadores_ordenados[0])
                jogador2= int(jogadores_ordenados[1])
                print(jogador1)
                print(jogador2)
                print(self.chosen_ones)
                self.chosen_ones.append(jogador1)
                self.chosen_ones.append(jogador2)
        self.escolhido_hashing(self.self_port)
        return self.chosen_ones
        
    
    def interact_with_user1(self, cards):
        """ All interaction with user must be done through this method.
        YOU CANNOT CHANGE THIS METHOD. """

        print(f"Current cards: {cards}")
        print("(H)it")
        print("(S)tand")
        print("(W)in")  # Claim victory
        print("(D)efeat") # Fold in defeat
        key = " "
        while key not in "HSWD":
            key = input("> ").upper()
        return key.upper()
    
    def loop(self):
        """Server loop.""" 
        while True:
            events = self.player_sel.select()
            for key, mask in events:
                if key.fileobj is self.player_socket:
                    self.accept(key.fileobj, mask)
                    self.ready_players += 1
                    if self.ready_players == len(self.todosPlayers):
                        print("All players are ready!")
                        self.all_playersReady = True
                        self.main()
                else:
                    callback = key.data
                    callback(key.fileobj, mask)
            # signal.pause()
    
    def sendAll(self, msg):
        for player in self.OthersPlayersFromBegin:
            player_socket = self.player_sockets[player]
            CDProto.send_msg(player_socket, msg)


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
        
    p = Player(self_port, players)
    p.loop()
    # p.main(args.self) #falta args.players porque só temos um jogador