# Jogo do Bixo

Simulador educativo, em Django, de jogo do bicho, roleta europeia, caça-níquel
e dado. Tudo funciona com **fichas fictícias (F$)**: não há dinheiro real,
pagamentos nem prêmios. O objetivo é mostrar, na prática e com números
calculados pelo próprio código, por que a banca sempre ganha.

> No Brasil, explorar ou realizar o jogo do bicho é contravenção penal
> (art. 58 do Decreto-Lei 3.688/1941). Este projeto existe para ensinar
> probabilidade e os mecanismos das apostas, não para incentivá-las.
> Se o jogo está pesando na sua vida, o CVV atende pelo 188, de graça, 24 h.

## O que tem

- **Jogo do bicho**: tabela dos 25 bichos, apostas em grupo, dezena, centena e
  milhar (na cabeça ou do 1º ao 5º), extrações com cinco prêmios e liquidação
  automática. Qualquer usuário logado pode acionar o sorteio; há também o
  comando `sortear`.
- **Roleta europeia**: todas as apostas comuns, com tabela mostrando que todas
  têm a mesma vantagem da banca (o zero).
- **Caça-níquel**: três rolos abertos; o retorno ao jogador é calculado por
  enumeração exata das 8000 combinações.
- **Dado**: o exemplo mais simples (chance 1 em 6, paga 5x).
- **Resultados encenados**: a roda da roleta gira até a casa sorteada, os
  rolos do caça-níquel param um a um, o dado rola e o poste do bicho revela
  os cinco prêmios dígito a dígito. O sorteio é sempre decidido no servidor;
  o JavaScript só encena a revelação e respeita a preferência "reduzir
  movimento" do sistema (sem JavaScript, o resultado aparece direto).
- **Carteira**: saldo, livro-razão, gráfico do saldo, recargas contadas e a
  comparação "teoria × prática" entre o que a matemática previa e o que o
  usuário recebeu.
- **Aprenda**: como funciona o bicho, probabilidade e valor esperado, falácias
  do apostador, lei e jogo responsável, e um simulador Monte Carlo de até
  50 000 apostas com gráfico.

## Rodando

Requer Python 3.12+ e [uv](https://docs.astral.sh/uv/) (ou `pip`).

```bash
uv venv .venv
uv pip install --python .venv -r requirements.txt

# Windows
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py createsuperuser   # opcional, para o /admin/
.venv\Scripts\python manage.py runserver

# Linux / macOS
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Abra <http://127.0.0.1:8777/> (a porta padrão do `runserver` neste projeto é 8777; passe outra como argumento se precisar), crie uma conta (só usuário e senha) e você
recebe F$ 1000 em fichas fictícias.

Outros comandos:

```bash
python manage.py test        # suíte completa
python manage.py sortear     # encerra a extração aberta e liquida as apostas
```

## Estrutura

| App      | Responsabilidade                                                      |
|----------|------------------------------------------------------------------------|
| `config` | Settings e rotas do projeto (gerado por `django-admin startproject`).   |
| `core`   | Página inicial, cadastro, template base, CSS.                           |
| `wallet` | Carteira, livro-razão (`Transaction`), serviços de débito/crédito, painel, extrato, gráfico e análise teoria × prática. |
| `bicho`  | Regras puras (`rules.py`), extrações (`Draw`), apostas (`Bet`), liquidação, comando `sortear`. |
| `casino` | Motores puros (`roulette.py`, `slots.py`, `dice.py`), rodadas (`CasinoRound`), views. |
| `learn`  | Páginas educativas e simulador Monte Carlo (`simulator.py`).            |

Regras do projeto:

- Toda movimentação de fichas passa por `wallet.services` dentro de
  `transaction.atomic()`; saldo e livro-razão são gravados na mesma transação (no SQLite, com modo IMMEDIATE para serializar escritas).
- Os motores de jogo não tocam o banco de dados e são testados isoladamente.
- Toda tabela de probabilidade, pagamento e vantagem da banca exibida no site
  é calculada pelo código dos jogos, nunca digitada à mão.

## Regras dos jogos

| Jogo / aposta              | Chance    | Paga   | Justo  | Fica com a banca |
|----------------------------|-----------|--------|--------|------------------|
| Bicho, grupo               | 1 em 25   | 18x    | 25x    | 28%              |
| Bicho, dezena              | 1 em 100  | 60x    | 100x   | 40%              |
| Bicho, centena             | 1 em 1000 | 600x   | 1000x  | 40%              |
| Bicho, milhar              | 1 em 10000| 4000x  | 10000x | 60%              |
| Roleta, qualquer aposta    | varia     | varia  | varia  | 2,7%             |
| Caça-níquel                | tabela    | tabela | —      | 6,6%             |
| Dado                       | 1 em 6    | 5x     | 6x     | 16,7%            |

No bicho, "do 1º ao 5º" paga um quinto do multiplicador por prêmio acertado,
o que mantém a vantagem da banca igual à da aposta na cabeça.

## Documentação de projeto

- Especificação: `docs/superpowers/specs/2026-10-11-jogobixo-design.md`
- Plano de implementação: `docs/superpowers/plans/2026-10-11-jogobixo.md`
