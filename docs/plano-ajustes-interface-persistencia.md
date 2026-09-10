# Plano de implementação — interface, histórico e formatação

## Objetivo

Executar os ajustes visuais e funcionais solicitados para o Garantiu:

- remover fundos brancos dos elementos de marca;
- simplificar textos com aparência artificial, como `01 · PREPARAR RELEASE`;
- explicar melhor as entradas de qualidade da primeira página;
- persistir as evidências de bugs e incidentes por análise;
- permitir a exportação do histórico em CSV;
- iniciar o campo de repositório vazio;
- padronizar a apresentação de datas e scores.

Este documento é um roteiro de execução. Marque os itens conforme forem concluídos.

## Escopo e decisões

### Persistência

Usar SQLite como fonte principal do histórico e CSV apenas para importação e
exportação.

Essa decisão preserva a arquitetura existente: o projeto já usa SQLite para
decisões, execuções de testes, scores e resultados de releases. Usar apenas CSV
como banco principal dificultaria consultas, relacionamentos, deduplicação e
gravações atômicas.

### Histórico de bugs

No MVP, bugs continuam sendo identificados automaticamente pelo histórico Git.
O código atual considera commits cujas mensagens contêm termos como `fix`,
`bug` e `corrige`. Não será criado um formulário de cadastro manual de bugs
nesta entrega, para evitar duplicidade entre registros manuais e commits.

### Datas e scores

- Datas e timestamps permanecem armazenados em ISO 8601 e UTC.
- A conversão para o padrão brasileiro acontece somente na interface.
- Scores permanecem numericamente como `float` entre 0 e 100.
- A interface apresenta sempre uma casa decimal, por exemplo `82,5 / 100`.
- Gráficos continuam recebendo valores numéricos, sem formatação textual.

## Estado atual confirmado

- `garantiu-logo-full.jpeg` possui fundo branco porque JPEG não suporta
  transparência.
- `garantiu-symbol.png` e `garantiu-wordmark.png` já possuem canal de
  transparência.
- O CSS adiciona fundos claros ao logo, ao símbolo das páginas e ao logo do
  rodapé.
- As sete páginas usam um cabeçalho numerado no formato `NN · AÇÃO`.
- O campo de repositório recebe `.` como valor inicial.
- JUnit e incidentes são fornecidos na primeira página, dentro de “Dados
  adicionais de qualidade”.
- Bugs são extraídos automaticamente do Git, não de um arquivo enviado pelo
  usuário.
- Scores, testes e decisões já são persistidos localmente, mas as evidências
  detalhadas de bugs e incidentes não são preservadas por análise.

## Fase 1 — Helpers de apresentação

### Implementação

- [ ] Adicionar em `garantiu/ui.py`:
  - [ ] `format_score(value)`;
  - [ ] `format_date_br(value)`;
  - [ ] `format_datetime_br(value, timezone_name="America/Sao_Paulo")`.
- [ ] Usar `zoneinfo.ZoneInfo`, disponível na biblioteca padrão do Python.
- [ ] Fazer os helpers aceitarem strings ISO, `date` e `datetime`, conforme a
  necessidade real dos chamadores.
- [ ] Caso exista um valor legado inválido, devolver o texto original em vez
  de interromper a página.
- [ ] Não alterar os valores armazenados no banco.

### Padrões visuais

| Tipo | Formato |
|---|---|
| Data | `10/09/2026` |
| Data e hora | `10/09/2026 14:35` |
| Score | `82,5 / 100` |
| Percentual | `82,5%` |

### Testes

- [ ] Criar testes unitários para data sem horário.
- [ ] Criar testes para timestamp UTC convertido para São Paulo.
- [ ] Criar teste para valor ISO com e sem offset.
- [ ] Criar teste para valor legado inválido.
- [ ] Criar testes de score inteiro e decimal.
- [ ] Confirmar que os limites de risco 40 e 70 não foram alterados.

## Fase 2 — Campo de repositório vazio

### Implementação

- [ ] Alterar o valor inicial de `repository_source` de `"."` para `""` em
  `app.py`.
- [ ] Manter a persistência do valor ao navegar entre as páginas.
- [ ] Manter a limpeza da análise quando o usuário troca de repositório.
- [ ] Não consultar o histórico enquanto o campo estiver vazio.
- [ ] Exibir uma mensagem clara ao tentar analisar sem informar o repositório.

### Testes

- [ ] Atualizar o teste de pipeline completo para preencher explicitamente o
  caminho do repositório usado no teste.
- [ ] Testar que a aplicação inicia com o campo vazio.
- [ ] Testar a validação ao clicar em “Analisar mudanças” com o campo vazio.
- [ ] Revalidar a navegação entre “Conectar release” e “Histórico & tendências”.

## Fase 3 — Revisão dos textos

### Implementação

- [ ] Simplificar `render_page_header()` para receber somente título e
  descrição.
- [ ] Remover da interface:
  - [ ] `01 · PREPARAR RELEASE`;
  - [ ] `02 · AVALIAR RELEASE`;
  - [ ] `03 · DIRECIONAR TESTE`;
  - [ ] `04 · PRIORIZAR AUTOMAÇÃO`;
  - [ ] `05 · EXPLICAR RISCO`;
  - [ ] `06 · DECIDIR`;
  - [ ] `07 · APRENDER`;
  - [ ] `FLUXO DA RELEASE` na tela bloqueada.
- [ ] Remover a classe `.page-eyebrow` do CSS.
- [ ] Alterar “Fluxo da release” para “Etapas da release”.
- [ ] Revisar textos em caixa alta que não sejam siglas ou dados técnicos.

### Sugestões de substituição

| Texto atual | Texto sugerido |
|---|---|
| `RELEASE ANALISADA` | `Release analisada` |
| `FOCO RECOMENDADO` | `Onde testar primeiro` |
| `ARQUIVOS` | `Arquivos` |
| `MÓDULOS` | `Módulos` |
| `STATUS` | `Status` |

Os títulos funcionais atuais, como “Conectar release” e “Visão geral do
risco”, devem permanecer.

### Testes

- [ ] Atualizar testes que dependem da assinatura de `render_page_header()`.
- [ ] Criar uma asserção garantindo que nenhum HTML renderizado contenha o
  padrão de cabeçalho `NN · AÇÃO`.
- [ ] Revisar as sete páginas em uma sessão completa do AppTest.

## Fase 4 — Imagens com fundo transparente

### Implementação

- [ ] Parar de usar `garantiu-logo-full.jpeg` em `render_brand()`.
- [ ] Montar o logo principal com `garantiu-symbol.png` e
  `garantiu-wordmark.png`.
- [ ] Adaptar o wordmark para manter contraste no tema escuro:
  - criar uma versão transparente para fundo escuro; ou
  - aplicar um tratamento CSS aprovado visualmente.
- [ ] Remover os fundos claros de:
  - [ ] `.brand-full-crop`;
  - [ ] `.sidebar-footer img`;
  - [ ] `.page-brand-symbol`.
- [ ] Remover bordas e sombras que ainda produzam aparência de caixa branca.
- [ ] Manter textos alternativos adequados.
- [ ] Após confirmar que não há referências, remover o JPEG antigo em uma
  alteração separada e recuperável.

### Critérios de aceite

- [ ] Nenhuma imagem apresenta retângulo branco no tema escuro.
- [ ] Símbolo e nome continuam legíveis.
- [ ] Não existem halos brancos nas bordas transparentes.
- [ ] A identidade visual continua legível em desktop e viewport estreito.
- [ ] O ícone da página continua funcionando.

### Testes

- [ ] Atualizar `tests/test_app_smoke.py` para não exigir o JPEG antigo.
- [ ] Verificar no HTML que os assets usados são PNG.
- [ ] Fazer inspeção visual real no navegador; AppTest não substitui esta
  validação.

## Fase 5 — Clareza dos dados adicionais de qualidade

### Conteúdo que deve ser explicado

| Fonte | Para que serve | Origem |
|---|---|---|
| JUnit XML | Status dos testes executados | Terminal ou CI |
| CSV de incidentes | Quantidade de incidentes por módulo | Histórico operacional da equipe |
| CSV de detalhes | Descrição e data dos incidentes | Histórico operacional da equipe |
| Histórico de bugs | Correções anteriores relacionadas aos arquivos | Extraído automaticamente do Git |

JUnit informa resultados de execução. Ele não representa cobertura de código.

### Implementação

- [ ] Renomear o expander para “Resultados de testes e incidentes — opcional”.
- [ ] Explicar cada entrada logo abaixo do respectivo campo.
- [ ] Informar que o histórico de bugs é obtido automaticamente do Git.
- [ ] Informar que a ausência de uma fonte não significa ausência de risco.
- [ ] Adicionar botões para baixar modelos dos CSVs de incidentes.
- [ ] Reutilizar os arquivos de `sample_data/` como fonte dos modelos, evitando
  exemplos duplicados no código.
- [ ] Depois da análise, mostrar quais fontes foram utilizadas e quais estavam
  ausentes.

### Formatos de entrada

Contagem de incidentes:

```csv
module,incident_count
checkout,3
auth,1
```

Detalhes de incidentes:

```csv
module,description,date
checkout,Falha ao confirmar pagamento,2026-09-10
```

### Testes

- [ ] Confirmar que os downloads usam os arquivos corretos.
- [ ] Confirmar que nenhuma fonte opcional é preenchida automaticamente.
- [ ] Testar análise sem dados opcionais.
- [ ] Testar análise com JUnit e os dois CSVs.

## Fase 6 — Persistência das evidências

### Banco selecionado

Adicionar as novas tabelas a `garantiu_release_history.db`. Não criar outro
banco para o mesmo domínio.

### Modelo proposto

#### `release_module_scores`

- `analysis_id`: referência ao registro em `release_scores`;
- `module`;
- `score`;
- `complexity_score`;
- `bug_score`;
- `test_health_score`;
- `incident_score`.

#### `release_bug_evidence`

- `analysis_id`;
- `module`;
- `file_path`;
- `commit_hash`;
- `message`;
- `occurred_on`.

#### `release_incident_counts`

- `analysis_id`;
- `module`;
- `incident_count`.

#### `release_incident_details`

- `analysis_id`;
- `module`;
- `description`;
- `occurred_on`.

### Regras

- [ ] Usar chaves estrangeiras para relacionar as evidências ao score da
  análise.
- [ ] Ativar `PRAGMA foreign_keys = ON` nas conexões responsáveis.
- [ ] Criar índices para `analysis_id` e consultas por módulo.
- [ ] Não alterar nem apagar os registros existentes.
- [ ] Permitir que duas análises do mesmo intervalo sejam preservadas como
  snapshots distintos.
- [ ] Continuar mostrando apenas a análise mais recente por release no resumo
  atual.
- [ ] Gravar score, módulos, bugs e incidentes em uma única transação.
- [ ] Se uma evidência for inválida, reverter toda a gravação da análise.

### Integração

- [ ] Fazer `record_release_score()` continuar disponível para compatibilidade.
- [ ] Criar uma operação de nível mais alto, como
  `record_release_analysis()`, responsável pela transação completa.
- [ ] Usar o ID da análise na gravação dos módulos e evidências.
- [ ] Não gravar caminhos temporários de clones do GitHub; usar sempre a
  `repo_key` normalizada.

### Testes

- [ ] Migração sobre banco vazio.
- [ ] Migração sobre banco já existente com scores e resultados.
- [ ] Persistência dos quatro fatores por módulo.
- [ ] Persistência de commits que alteram mais de um arquivo.
- [ ] Persistência de incidentes com e sem detalhes.
- [ ] Isolamento por repositório.
- [ ] Rollback completo quando uma inserção falhar.
- [ ] Consulta após reiniciar a aplicação.

## Fase 7 — Consulta e exportação do histórico

### Interface

Organizar “Histórico & tendências” em três áreas:

1. Releases;
2. Bugs encontrados;
3. Incidentes importados.

### Implementação

- [ ] Adicionar filtro por release.
- [ ] Adicionar filtro por módulo.
- [ ] Mostrar estado vazio específico em cada área.
- [ ] Aplicar os helpers de data e score nas tabelas.
- [ ] Adicionar “Baixar CSV” para releases, bugs e incidentes.
- [ ] Gerar o CSV em memória, sem criar arquivos permanentes na pasta do
  projeto.
- [ ] Manter no CSV os valores canônicos necessários para reprocessamento:
  timestamps ISO e scores numéricos com ponto decimal.
- [ ] Usar UTF-8 e cabeçalhos documentados.

### Testes

- [ ] Consultar somente o repositório selecionado.
- [ ] Filtrar por release e módulo.
- [ ] Exportar histórico vazio e preenchido.
- [ ] Validar cabeçalhos, quantidade de linhas e codificação.
- [ ] Confirmar que a exportação não modifica o banco.

## Fase 8 — Aplicar formatação em todas as telas

- [ ] Visão geral do risco.
- [ ] Tabela de módulos.
- [ ] Cabeçalho dos fatores.
- [ ] Roteiro de teste manual.
- [ ] Suíte automatizada priorizada.
- [ ] Detalhe do módulo.
- [ ] Decisão de publicação e auditoria.
- [ ] Histórico e tendências.
- [ ] Gráfico temporal, mantendo o eixo numérico/temporal.
- [ ] CSVs de exportação, conforme a regra canônica definida neste plano.

## Fase 9 — Documentação

- [ ] Atualizar o `README.md` com:
  - origem automática do histórico de bugs;
  - significado de JUnit e dos dois CSVs;
  - localização dos bancos;
  - política de datas e fuso horário;
  - persistência das evidências;
  - exportação CSV.
- [ ] Atualizar `docs/implementacao-concluida.md` somente depois que a
  implementação estiver concluída e verificada.
- [ ] Remover referências ao JPEG da documentação e dos testes.

## Fase 10 — Validação final

### Automatizada

- [ ] Restaurar ou recriar o ambiente virtual, pois o `.venv` atual aponta
  para um executável Python inexistente.
- [ ] Instalar as dependências de `requirements.txt` no ambiente restaurado.
- [ ] Executar:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

- [ ] Executar a cobertura:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=garantiu --cov-report=term-missing
```

- [ ] Iniciar a aplicação:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### Verificação manual

- [ ] Abrir a aplicação com estado inicial limpo.
- [ ] Confirmar que o repositório começa vazio.
- [ ] Analisar um repositório sem fontes opcionais.
- [ ] Analisar outro repositório com JUnit e incidentes.
- [ ] Reiniciar a aplicação e consultar as evidências persistidas.
- [ ] Exportar os três CSVs e conferir o conteúdo.
- [ ] Verificar todas as sete páginas em desktop.
- [ ] Verificar o layout abaixo de 900 px.
- [ ] Confirmar ausência de fundos e halos brancos nos logos.
- [ ] Confirmar que datas e scores seguem o mesmo padrão em todas as telas.

## Arquivos principais afetados

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Campos, textos, navegação, gravação e histórico |
| `garantiu/ui.py` | Logo, cabeçalhos e formatadores |
| `garantiu/ui.css` | Transparência, contraste e remoção dos eyebrows |
| `garantiu/release_history.py` | Migração, persistência e consultas |
| `garantiu/bug_history.py` | Evidências extraídas do Git |
| `garantiu/incidents.py` | Importação dos CSVs |
| `tests/test_app_smoke.py` | Fluxos completos da interface |
| `tests/test_release_history.py` | Migração e persistência |
| `tests/test_bug_history.py` | Extração de bugs |
| `tests/test_incidents.py` | Validação dos CSVs |
| `README.md` | Orientação ao usuário |

## Critérios de conclusão

A implementação só deve ser considerada concluída quando:

- [ ] todos os logos estiverem transparentes e legíveis;
- [ ] não houver cabeçalhos no formato `NN · AÇÃO`;
- [ ] o campo de repositório iniciar vazio;
- [ ] as fontes de qualidade estiverem explicadas na primeira página;
- [ ] bugs, incidentes e scores puderem ser consultados após reiniciar o app;
- [ ] o histórico puder ser exportado em CSV;
- [ ] datas e scores estiverem padronizados;
- [ ] migrações preservarem os bancos existentes;
- [ ] todos os testes automatizados passarem;
- [ ] a inspeção visual em navegador estiver aprovada;
- [ ] o diff final não incluir bancos SQLite, arquivos temporários ou outros
  artefatos gerados durante os testes.

## Estimativa

Estimativa inicial: **3 a 4 dias de desenvolvimento**, incluindo testes,
documentação e revisão visual. A estimativa deve ser revista caso seja incluído
cadastro manual de bugs ou importação direta de ferramentas externas.
