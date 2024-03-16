## O que podemos fazer com o nosso programa? <br />
1. Jogar a solo<br />
2. Jogar com 2,3 ou 4 jogadores<br />
3. Jogar com 1 “bad_player” com características obrigatórias:<br />
    a) Adicionar carta a mais<br />
    b) Mentir sobre ter ganho<br />
    c) Mentir sobre o valor das suas cartas<br />
    d) Mentir sobre o valor de hash obtido do deck<br /> 
4. Jogar com 1 “bad_player” com características opcionais:<br />
    a) Retirar uma das suas cartas<br />
    b) Mentir que houve batota quando escolhido para hashing<br /> 
5. Deteção de batota (utilizando Protocolo 2PC)<br />
6. Jogar com múltiplos bad_players/players<br /><br />

## Características Programa:<br />
  __(H)it <br />__
    - *Não deixa dar Hit se mais de 21, e se tiver 21 aconselha a pessoa a dar win, pedindo outra vez para jogar<br />*
  __(S)tand <br />__
    - *Não deixa jogador dar stand se tiver mais que 21, exibindo mensagem a dizer que tem mais que 21 pontos, pedindo que este jogue outra vez<br />*
  __(W)in <br />__
    - *Não deixa jogador dar win, se tem mais que 21 pontos ou se tem menos, pedindo outra vez para este jogar<br />*
