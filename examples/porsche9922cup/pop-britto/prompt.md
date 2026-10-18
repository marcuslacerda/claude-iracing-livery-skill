# pop-britto

Prompt para `/iracing-livery:paint` (Porsche 911 GT3 Cup 992.2). Design: `designs/pop_britto.py`.

```
uv run scripts/paint.py render --car porsche9922cup --design pop_britto
```

---

Livery "pop-britto" no Porsche 992.2 Cup, inspirada no estilo pop art de Romero Britto: arte original,
sem copiar obras específicas.

Linguagem visual:
- O carro inteiro dividido em grandes áreas orgânicas e curvas (como um vitral), separadas por
  contornos pretos grossos (~2,5–3 cm), com contorno também em todas as junções de painel.
- Cada área com cor chapada saturada OU um padrão (listras diagonais, bolinhas, xadrez, zigue-zague,
  ondas); áreas vizinhas nunca repetem cor nem padrão.
- Paleta: rosa choque #ff2d87, amarelo #ffd400, azul ciano #00a8e8, verde-limão #7ed321,
  laranja #ff7a00, roxo #9511dd, mais branco e preto. Sem degradês. Áreas grandes (legível de longe).

Elementos-assinatura (originais):
- Capô: um coração grande sorridente (metade rosa, metade laranja listrada) sobre um balão branco com
  contorno preto, ocupando a parte livre do capô entre as saídas de ar e o para-brisa, com a ponta no
  vão entre as saídas; uma faixa branca grossa com o wordmark atravessando, lendo de frente.
- Teto: um sol estilizado com raios em segmentos coloridos e rosto sorrindo.
- Laterais: um peixe de perfil feito de segmentos coloridos, sobre um balão branco, na área grande atrás
  da porta, virado para a frente nos dois lados.
- Para-choque dianteiro: sorriso amplo com lábio preto contínuo, boca vermelha e uma fileira de dentes
  brancos retos e arredondados.
- Asa (face de cima): rosa com bolinhas brancas e a logo + wordmark numa plaquinha branca no centro.
- Retrovisores e endplates: amarelo com bolinhas pretas.

Área do número: um círculo branco limpo com contorno preto grosso na parte dianteira-baixa de cada porta.

Spec map: tudo brilhante (rugosidade ~25), tipo laca, sem metálico; contornos pretos um pouco menos
brilhantes (~60).
