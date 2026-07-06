# Análise de Renda no Brasil

Projeto de análise de dados desenvolvido para simular um fluxo real de trabalho de um **Analista de Dados Jr**.

O projeto utiliza um dataset sintético inspirado em indicadores de renda do Brasil e aplica etapas de **ETL, análise exploratória, consultas SQL e visualização em Power BI**.

## Objetivo do projeto

O objetivo é analisar diferenças de renda entre regiões e estados brasileiros, identificando padrões, tendências, desigualdades e oportunidades de interpretação a partir dos dados.

O projeto foi estruturado para demonstrar habilidades práticas em análise de dados, desde o tratamento da base até a construção de insights e preparação para dashboard.

## Perguntas de negócio

- Quais estados apresentam maior e menor renda média?
- Como a renda evoluiu ao longo do tempo?
- Quais regiões possuem maior concentração de renda?
- Existe desigualdade relevante entre os estados?
- Quais estados apresentaram maior crescimento anual?
- Como transformar dados brutos em visualizações úteis para tomada de decisão?

## Etapas do projeto

1. Coleta e organização dos dados
2. Limpeza e tratamento da base
3. Análise exploratória dos dados
4. Criação de indicadores
5. Consultas SQL para análise
6. Construção de dashboard em Power BI
7. Documentação dos resultados

## Tecnologias utilizadas

- Python
- Pandas
- Jupyter Notebook
- SQL
- Power BI
- Excel
- Git e GitHub

## Estrutura do repositório

```text
analise-renda-brasil/
├── data/                 # Bases brutas e tratadas
├── notebooks/            # Notebooks de ETL e EDA
├── sql/                  # Consultas SQL e modelagem
├── dashboard/            # Guia e medidas para Power BI
├── images/               # Imagens e previews do dashboard
├── docs/                 # Dicionário de dados e documentação
├── requirements.txt      # Dependências do projeto
└── README.md
```

## Entregáveis

- Dataset tratado em CSV
- Notebooks de ETL e análise exploratória
- Consultas SQL para análise dos indicadores
- Guia para construção do dashboard em Power BI
- Imagens de preview das visualizações
- Documentação do fluxo analítico

## Principais análises

- Ranking de renda média por estado
- Comparação de renda por região
- Evolução temporal da renda
- Crescimento anual por UF
- Comparação entre média simples e média ponderada
- Análise de dispersão e desigualdade regional

## Como executar o projeto

### Instalar dependências

```bash
pip install -r requirements.txt
```

### Executar notebooks

Execute os notebooks na seguinte ordem:

```text
notebooks/01_etl.ipynb
notebooks/02_eda.ipynb
```

## Dashboard

O projeto inclui uma proposta de dashboard em Power BI com indicadores e visualizações para análise de renda.

Visualizações sugeridas:

- Cards de KPIs principais
- Gráfico de evolução temporal
- Ranking Top 10 estados
- Comparação por região
- Crescimento anual
- Mapa ou gráfico por UF

## Exemplos de indicadores

- Renda média por estado
- Renda média por região
- Variação anual
- Crescimento percentual
- Ranking de UFs
- Média ponderada pela população

## Observação sobre os dados

O dataset utilizado é sintético e foi criado para fins de portfólio.

Apesar disso, o fluxo do projeto simula uma rotina real de análise de dados, incluindo tratamento, exploração, modelagem, consultas e visualização.

## O que este projeto demonstra

- Capacidade de estruturar um projeto de dados do início ao fim
- Limpeza e transformação de dados com Python
- Análise exploratória com Jupyter Notebook
- Criação de consultas SQL
- Construção de indicadores para negócio
- Desenvolvimento de dashboard em Power BI
- Organização de repositório para portfólio

## Melhorias futuras

- Utilizar dados reais diretamente de fontes públicas
- Automatizar a etapa de coleta de dados
- Criar dashboard interativo publicado
- Adicionar análise por faixa etária, escolaridade ou gênero
- Criar documentação executiva com conclusões de negócio

## Autor

Maurício Ryo Toita Taguchi  
GitHub: [MauricioTaguchi](https://github.com/MauricioTaguchi)
