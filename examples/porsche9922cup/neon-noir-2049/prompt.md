# neon-noir-2049

Prompt para `/iracing-livery:paint` (Porsche 911 GT3 Cup 992.2). Design: `designs/neon_noir.py`.

```
uv run scripts/paint.py render --car porsche9922cup --design neon_noir --set "code=24 10.08.2026" --set 'katakana=["ラセルダペックス", "ネオンノワール"]'
```

---

Livery "neon-noir-2049" no Porsche 992.2 Cup, estética cyberpunk distópica inspirada em filmes neo-noir
de ficção científica: cidade chuvosa, neon refletindo em metal molhado. Arte original.

Corpo: grafite azulado escuro (#0d1117) com metálico médio, como metal molhado, e degradê sutil para o
roxo profundo (#5b0a8c) na traseira.

Camada de código:
- Chuva de código binário caindo na vertical pelas laterais, em verde-ciano (#00ffc6) com opacidade
  variável. A sequência é "24 10.08.2026" (número do carro + data da primeira vitória) em ASCII; ela se
  repete e fica mais densa da porta para trás, sem passar por cima do número.
- No teto, um bloco de "terminal" com prompt "> init lacerdapex.exe_" e linhas de log de telemetria
  fictícias.

Neon:
- Linha neon magenta (#ff2bd6) na cintura das laterais e contornando o perímetro do capô, com glow suave.
- Linha neon ciano (#00e5ff) no para-choque dianteiro baixo e na asa.

Símbolos nerds (placas de neon ou stickers gastos):
- Capô: logo + wordmark como letreiro neon magenta, lendo de frente; em volta, duas colunas de katakana
  ("ラセルダペックス" e "ネオンノワール"), um circuito impresso e um "olho" geométrico em neon no vão entre
  as saídas de ar.
- Laterais: na frente-baixa da porta, logo abaixo do número, stickers gastos de pi (π), lambda (λ), d20,
  controle de videogame retrô, Space Invader em pixel art, "42", ":wq", "sudo" e "404".
- Para-choque traseiro: código de barras + QR code decorativo + "REPLICANT UNIT // CUP-992.2".
- Asa (face de cima): "TEARS IN RAIN // LAP 01" em fonte monoespaçada.
- Retrovisores e endplates: magenta neon.
- Banner do para-brisa: preto com o wordmark em ciano, estilo display de LED.

Textura: gotas de chuva e escorridos sutis sobre o corpo; scanlines finas no teto e na tampa do motor.

Spec map: corpo com metálico ~120 e rugosidade ~40 (molhado); neon e código com metálico 0 e brilho
máximo; stickers foscos (~180).
