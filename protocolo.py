import pickle
import redis
import socket
import json

# protocolo para meninos jogarem

class Message:
    """Message Type."""

    def __init__(self):
        """Initialize message."""
        self.command = "command"

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"
    
class AfterPlay(Message):
    """ Message to send to next player after a play. """
    def __init__(self, player_port):
        """Initialize message."""
        self.command = "played"
        self.player_port = player_port

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command, "player_port": self.player_port}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"

class ReceivedCard(Message):
    """ Message to send to next player after a play. """
    def __init__(self):
        """Initialize message."""
        self.command = "receivedCard"

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"
    
    
class PlayerDefeated(Message):
    """ Message to send to send all after being defeated. """
    def __init__(self, player_port):
        """Initialize message."""
        self.command = "defeated"
        self.player_port = player_port

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command, "player_port": self.player_port}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"
    
class PlayerStand(Message):
    """ Message to send to send all after being defeated. """
    def __init__(self, player_port):
        """Initialize message."""
        self.command = "stand"
        self.player_port = player_port

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command, "player_port": self.player_port}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"

class PlayerWin(Message):
    """ Message to send to send all after being defeated. """
    def __init__(self, player_port):
        """Initialize message."""
        self.command = "win"
        self.player_port = player_port

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command, "player_port": self.player_port}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"

class PlayerDecision(Message):
    """ Message to send to elect who goes to hashing. """
    def __init__(self, decision):
        """Initialize message."""
        self.command = "decision"
        self.decision = decision

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command, "decision": self.decision}

    def __str__(self):
        return f"{{\"command\": \"{self.decision}\"}}"
    
class CoordenadorDecision(Message):
    """ Message to send to elect who goes to hashing. """
    def __init__(self, decision):
        """Initialize message."""
        self.command = "coorDecision"
        self.decision = decision

    def toDic(self):
        """Return string representation of message."""
        return {"command": self.command, "decision": self.decision}

    def __str__(self):
        return f"{{\"command\": \"{self.command}\"}}"

    
#enviar mensagem pedir 2 cartas iniciais (com self_port)
def pedir_cartas(self_port):
    msg="GC"
    msg_final=msg+str(self_port)
    return msg_final

def ir_ao_hashing(self_port):
    msg="HC"
    msg_final=msg+str(self_port)
    return msg_final


class CDProto:
    """Computação Distribuida Protocol."""
    
    @classmethod
    def receivedCard(cls) -> ReceivedCard:
        return ReceivedCard()
    
    @classmethod
    def played(cls, player_port) -> AfterPlay:
        return AfterPlay(player_port)

    @classmethod
    def playerDefeated(cls, player_port) -> PlayerDefeated:
        return PlayerDefeated(player_port)
    
    @classmethod
    def playerStand(cls, player_port) -> PlayerStand:
        return PlayerStand(player_port)
    
    @classmethod
    def playerWin(cls, player_port) -> PlayerWin:
        return PlayerWin(player_port)

    @classmethod
    def playerDecision(cls, decision) -> PlayerDecision:
        return PlayerDecision(decision)
    
    @classmethod
    def coorDecision(cls, decision) -> CoordenadorDecision:
        return CoordenadorDecision(decision)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message):
        """Sends through a connection a Message object."""
        msg_byts = json.dumps(msg.toDic()).encode('utf-8')  # mensagem em bytes
        head = len(msg_byts).to_bytes(2, 'big')  # cabeçalho em bytes
        if ((len(msg_byts)) >= 2**16):
            raise CDProtoBadFormat()
        connection.send(head + msg_byts)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""
        head = int.from_bytes(connection.recv(2), 'big')
        if head >= 2**16:
            raise CDProtoBadFormat()
        elif head == 0:
            return None
        else:
            try:
                msg = json.loads(connection.recv(head).decode('utf-8'))
            except:
                raise CDProtoBadFormat()

        if msg["command"] == 'played':
            return CDProto.played(msg['player_port'])
        elif msg["command"] == 'receivedCard':
            return CDProto.receivedCard()
        elif msg["command"] == 'defeated':
            return CDProto.playerDefeated(msg['player_port'])
        elif msg["command"] == 'stand':
            return CDProto.playerStand(msg['player_port'])
        elif msg["command"] == 'win':
            return CDProto.playerWin(msg['player_port'])
        elif msg["command"] == 'decision':
            return CDProto.playerDecision( msg['decision'])
        elif msg["command"] == 'coorDecision':
            return CDProto.coorDecision(msg['decision'])


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes = None):
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")