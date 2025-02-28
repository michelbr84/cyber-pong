# Cyber Pong

**Cyber Pong** é uma versão modernizada do clássico Pong, combinando elementos retrô com tecnologias modernas. O jogo foi desenvolvido em Python com a biblioteca [Pygame](https://www.pygame.org/), e traz diversas melhorias, como efeitos de partículas, trilha sonora, modos de jogo variados e até suporte para multiplayer online.

## Recursos

- **Modos de Jogo Diversificados**:  
  - Singleplayer com IA adaptativa  
  - Multiplayer local  
  - Multiplayer online básico  
  - Modo Tournament (partida até 5 pontos)  
  - Replay de partidas gravadas

- **Efeitos Visuais Avançados**:  
  - Efeitos de partículas com pooling  
  - Efeito de "glow" e sombras para a bola e as raquetes  
  - Temas customizáveis (Classic, Dark, Neon)

- **Efeitos Sonoros e Música de Fundo**:  
  - Sons para colisões e pontuações  
  - Possibilidade de carregar uma música customizada  
  - Controle de volume via teclado

- **Opções de Customização**:  
  - Personalização dos controles  
  - Ativação do "Mobile Mode" (uso do mouse para controlar as raquetes)  
  - Ajuste de temas e modos de jogo

- **Sistema de Replay e Estatísticas**:  
  - Gravação do estado do jogo para reprodução  
  - Tela de estatísticas e ranking (armazenado em arquivo)

- **Multiplayer Online**:  
  - Suporte para partidas online básicas utilizando sockets com tratamento de erros e interpolação para suavizar a experiência

## Requisitos

- Python 3.7 ou superior
- [Pygame 2.6.1](https://www.pygame.org/) ou versão compatível
- Bibliotecas Python padrão: `numpy`, `socket`, `threading`, `os`, `time`

## Instalação

1. **Clone o repositório:**

   ```bash
   git clone https://github.com/seu-usuario/cyber-pong.git
   cd cyber-pong
   ```

2. **Instale as dependências:**

   Se você estiver utilizando `pip`, execute:

   ```bash
   pip install pygame numpy
   ```

3. **(Opcional) Coloque um arquivo de música:**

   Para usar uma trilha sonora personalizada, coloque um arquivo chamado `background.mp3` na raiz do projeto.

## Uso

Para executar o jogo, basta rodar:

```bash
python pong.py
```

## Controles

### No Menu:

- **Setas UP/DOWN**: Navegar pelas opções do menu.
- **Setas LEFT/RIGHT e teclas A/D**: Ajustar a dificuldade, modo e tema.
- **ENTER**: Selecionar a opção desejada.

### Durante o Jogo:

- **Singleplayer (IA controla a raquete direita):**
  - **W / S**: Mover a raquete esquerda para cima/baixo.
- **Multiplayer Local:**
  - **W / S**: Mover a raquete esquerda.
  - **UP / DOWN**: Mover a raquete direita.
- **Geral:**
  - **P**: Pausar/retomar o jogo.
  - **- / = (ou teclado numérico)**: Ajustar o volume da música de fundo.
  - **T**: Compartilhar o placar (simulado com uma mensagem no console).
  - **R**: Iniciar/Interromper a gravação e assistir ao replay.
  - **ESC**: Voltar ao menu a partir do jogo ou de telas como Estatísticas e Replay.

### No Modo Online:

- Siga as instruções no console para escolher entre hospedar ou conectar.
- Para clientes, informe o IP do host.

### No Modo Replay:

- Pressione **ESC**, **ENTER** ou **R** novamente para sair do replay e voltar ao menu.

## Personalização e Configurações

No menu de **Settings**, você pode:

- Redefinir os controles para cada jogador.
- Alternar o "Mobile Mode" para controlar as raquetes com o mouse.
- Carregar uma música customizada (digite o nome do arquivo de música no console quando solicitado).

## Notas

- **Multiplayer Online:** O modo online utiliza sockets de forma básica, com tratamento de erros e interpolação para suavizar a experiência. Certifique-se de que o firewall ou antivírus não bloqueiem a porta utilizada (padrão 12345).
- **Replay:** As gravações são armazenadas temporariamente durante a partida. Pressione "R" para interromper a gravação e assistir ao replay.

## Contribuição

Contribuições são bem-vindas! Se você deseja sugerir melhorias ou reportar bugs, abra uma issue ou envie um pull request no repositório.

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).