# garantiu — Wireframe de Solução (Dia 1)

## Contexto

Hackathon, Tema 4 — "Dá para entregar com segurança?". Etapa 1 (empatia/definição do
problema) já concluída com pesquisa baseada em fontes reais (DORA, Google flaky tests,
World Quality Report, CISQ, caso CrowdStrike). Este documento cobre a Etapa 2: desenhar
um conceito de solução e um wireframe de baixa fidelidade para apresentar ainda no dia 1,
explicitamente sujeito a mudanças nos dias 2 e 3.

**Problema (Etapa 1):** Times de desenvolvimento de software enfrentam dificuldade para
decidir o que testar primeiro e qual o risco real de publicar quando muitas alterações se
acumulam antes de um release, causando falhas em produção, retrabalho e perda de confiança
nos próprios testes.

**Como poderíamos:** dar visibilidade sobre onde está o risco de cada release para times
que acumulam muitas alterações antes de publicar, de forma que saibam o que testar
primeiro e publiquem com mais confiança sem precisar rodar mais testes?

## Conceito

**Nome: garantiu.** Dashboard web que, antes de cada release, cruza dados hoje espalhados
(diff do código, histórico de bugs, cobertura/estabilidade dos testes, incidentes
passados) e devolve um **score de risco do release** com a lista priorizada do que testar
primeiro.

### Score de risco — 4 fatores

1. **Magnitude/complexidade da mudança** — arquivos e linhas alteradas, área do sistema tocada.
2. **Densidade histórica de bugs** do módulo alterado.
3. **Saúde dos testes relacionados** — cobertura + taxa de flakiness.
4. **Histórico de incidentes** naquela área do sistema.

Esses 4 fatores respondem diretamente às causas levantadas na Etapa 1 (falta de
visibilidade, informação espalhada, testes instáveis virando ruído, falta de estratégia de
priorização).

## Escopo do wireframe (fluxo completo — 7 telas)

1. **Conectar Release** — setup: escolher repositório/branch e o intervalo de mudanças
   (ex.: desde a última tag) a ser analisado.
2. **Visão Geral do Risco (home)** — score geral do release, breakdown pelos 4 fatores,
   ranking dos módulos/arquivos mais arriscados, CTA para os testes recomendados.
3. **Resumo para QA** — tradução do risco técnico em linguagem simples, por módulo:
   o que mudou, por que testar aquilo, cenários sugeridos de teste manual/exploratório,
   e um espaço para o dev deixar uma nota direta pro QA. Ver "Adendo" abaixo.
4. **Lista Priorizada de Testes** — checklist ordenado por contribuição ao risco, com
   status (a rodar / passou / falhou / flaky), tempo estimado, filtro por módulo.
5. **Detalhe do Módulo/Arquivo** — por que aquele item está arriscado: o que mudou,
   histórico de bugs, incidentes, cobertura e flakiness específicos dali.
6. **Decisão de Publicação** — score atual, % do checklist concluído, quem aprova e
   quando; fecha o loop da decisão "publica ou não publica".
7. **Histórico & Tendências** — releases passados: risco previsto x resultado real
   (falhou em produção ou não), para construir confiança na ferramenta ao longo do tempo.

## Adendo (dia 1, tarde) — persona QA e tela "Resumo para QA"

Em conversa informal com um desenvolvedor (Murilo, 09/09), surgiu um ponto que a
pesquisa da manhã não tinha capturado: hoje o dev calcula o impacto de uma mudança "na
cabeça" e explica pro QA manualmente/verbalmente — não existe um artefato disso. Ou seja,
o QA também é um usuário do problema original (não sabe o que foi impactado), só que sem
acesso ao raciocínio técnico do dev.

Decisão: o QA passa a ser uma segunda persona do garantiu, com uma tela própria (não é
só reaproveitar as telas técnicas). A tela 3 — **Resumo para QA** — mora logo depois da
Visão Geral e, por módulo/área de risco, traz:

- **O que mudou**, em linguagem simples (sem nome de arquivo, sem diff).
- **Por que testar isso** — o impacto explicado, a "conta" que o dev fazia de cabeça.
- **Cenários sugeridos** — testes manuais/exploratórios em linguagem humana (não é a
  lista técnica de testes automatizados, que continua sendo a tela 4).
- **Nota do dev** — campo curto e opcional onde quem fez a mudança deixa um aviso
  direto pro QA, reproduzindo em produto a conversa que hoje é informal.

Isso não muda o problema/HMW da Etapa 1, mas amplia o público de "times de
desenvolvimento" para deixar explícito que inclui QA como consumidor do impacto, não só
quem decide publicar. Vale confirmar isso nas entrevistas de validação.

## Fidelidade e formato de entrega

Wireframe de **baixa fidelidade, tons de cinza** — caixas, texto placeholder, sem
cores/branding definitivos. Sinaliza claramente que é conceito/rascunho, não UI final.
Entregue como um único artifact HTML navegável (abas ou botões prev/next entre as 7
telas), sem dependências externas, para uso direto no pitch do dia 1.

## Fora de escopo (dia 1)

- Algoritmo real de cálculo do score (fica para os dias 2–3, com dados de exemplo/mock).
- Integrações reais com Git/CI (mencionadas na tela de setup, não implementadas).
- Identidade visual/branding definitiva (cores, logotipo).
- Autenticação, permissões, multi-time.

## Próximos passos (dias 2–3)

- Validar o conceito com as ~3 entrevistas planejadas no roteiro da Etapa 1.
- Ajustar telas/score conforme feedback.
- Se o hackathon pedir protótipo funcional, decidir stack nesse momento (fora do escopo
  deste documento).
