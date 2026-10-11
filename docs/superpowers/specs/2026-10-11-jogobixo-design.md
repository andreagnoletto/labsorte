# Jogo do Bixo — Simulador educativo de apostas (Django)

Data: 2026-10-11

## Objetivo

Aplicação web em Django, para fins educativos, que simula o jogo do bicho,
roleta, caça-níquel e dado, usando **fichas fictícias** (sem dinheiro real,
sem pagamentos). O propósito é mostrar na prática como esses jogos funcionam
e, principalmente, **por que a banca sempre ganha**: cada jogo expõe sua
probabilidade real, o pagamento oferecido, o pagamento justo e a vantagem da
casa, e o painel do usuário mostra o resultado acumulado das próprias apostas.

## Premissas assumidas (ninguém disponível para confirmar)

- "Educativo" = ensinar as regras e a matemática (probabilidade, valor
  esperado, vantagem da casa). Também serve como projeto de estudo de Django.
- Nenhuma integração de pagamento. Moeda: "fichas" (F$). Recargas ilimitadas,
  mas contadas e exibidas (quantas vezes o usuário precisou recarregar).
- Interface em português do Brasil; identificadores de código em inglês,
  preservando termos do domínio (milhar, centena, dezena, grupo, extração).
- Estrutura gerada pela CLI do Django (`startproject`, `startapp`), conforme
  pedido do usuário. Banco SQLite. Sem DRF, sem framework JS: templates
  server-side com CSS próprio e JS mínimo.
- Sem repositório git (o usuário não pediu).

## Jogos e regras

### Jogo do bicho

- 25 grupos (bichos), cada um com 4 dezenas: grupo *n* cobre as dezenas
  4n-3 .. 4n; a dezena 00 vale 100 e pertence ao grupo 25 (Vaca).
- Extração: 5 prêmios, cada um uma milhar de 0000 a 9999. "Cabeça" = 1º prêmio.
- Modalidades e pagamento na cabeça: Grupo 18x, Dezena 60x, Centena 600x,
  Milhar 4000x. Posição "1º ao 5º" (cercado): paga `multiplicador / 5` por
  prêmio acertado, somando os acertos (vantagem da casa idêntica à cabeça).
- Fluxo: apostas entram na extração aberta; qualquer usuário logado pode
  acionar "Sortear agora" (ou o comando `sortear`), o que encerra a extração,
  liquida as apostas pendentes, paga os vencedores e abre a próxima.

| Modalidade | Probabilidade | Paga | Justo | Retorno esperado | Vantagem da banca |
|---|---|---|---|---|---|
| Grupo | 4% | 18x | 25x | 72% | 28% |
| Dezena | 1% | 60x | 100x | 60% | 40% |
| Centena | 0,1% | 600x | 1000x | 60% | 40% |
| Milhar | 0,01% | 4000x | 10000x | 40% | 60% |

### Roleta (europeia, 37 casas)

Uma aposta por giro: número (36x), vermelho/preto, par/ímpar, baixo/alto (2x),
dúzia ou coluna (3x). Vantagem da casa 2,70% em todas.

### Caça-níquel

3 rolos de 20 símbolos com pesos; tabela de prêmios para trincas e para
exatamente duas cerejas. O RTP é calculado exatamente a partir dos rolos
(enumeração das 8000 combinações) e exibido na página.

### Dado

Acerte a face de um dado de 6 lados; paga 5x (justo seria 6x). Vantagem 16,7%.

## Arquitetura

Projeto `config` + apps:

- `core` — página inicial, cadastro, templates base e CSS.
- `wallet` — `Wallet` (saldo) e `Transaction` (livro-razão: bônus, aposta,
  prêmio, com jogo e saldo posterior). Serviços `debit`/`credit` atômicos.
  Views: extrato, recarga, painel de estatísticas (gráfico SVG do saldo).
- `bicho` — tabela estática dos 25 bichos, `Draw` (extração) e `Bet`;
  serviços de liquidação; comando `sortear`.
- `casino` — motores puros (roleta, caça-níquel, dado) + `CasinoRound`
  (jogo, aposta, prêmio, detalhes JSON).
- `learn` — páginas educativas (regras, probabilidade, vantagem da casa,
  falácias, aspectos legais e jogo responsável) e simulador Monte Carlo
  (N apostas automáticas sem mexer na carteira).

Toda movimentação de fichas passa pelos serviços de `wallet`, dentro de
`transaction.atomic()`. Estatísticas derivam do livro-razão.

## Erros

- Saldo insuficiente, aposta acima do máximo (500 fichas) ou palpite
  inválido: erro de formulário, nada é debitado.
- Sorteio sem apostas pendentes: permitido (apenas gera a extração).

## Testes

`manage.py test`: mapeamento dezena→grupo, cálculo de prêmio por modalidade e
posição, liquidação de extração (pagamento e saldo), motores de roleta /
caça-níquel / dado (pagamentos, RTP), serviços de carteira (débito atômico,
saldo insuficiente), fumaça das views principais.
