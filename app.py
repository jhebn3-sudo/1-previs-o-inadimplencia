# Importa a biblioteca Streamlit para construir a interface visual web do painel
import streamlit as st
# Importa a biblioteca pandas para a manipulação, limpeza e filtros de dados
import pandas as pd
# Importa a classe do classificador de Regressão Logística para o treinamento
from sklearn.linear_model import LogisticRegression
# Importa a biblioteca Plotly Express para gerar gráficos interativos de dispersão
import plotly.express as px
# Importa a biblioteca Plotly Graph Objects para criar o gráfico de gauge personalizado
import plotly.graph_objects as go
# Importa o módulo os para verificação de existência física do arquivo de dados
import os

# Define o layout da aplicação Streamlit ocupando toda a largura útil da tela
st.set_page_config(layout='wide')
# Configura o título principal visível na interface do usuário do painel
st.title('Painel de Previsão de Inadimplência de Clientes')

# Define a função de carga e treino do modelo com cache de recurso do Streamlit
@st.cache_resource
def treinar_modelo():
    # Especifica o caminho exato do arquivo de dados que contém o histórico
    caminho = 'inadimplencia-clientes.xlsx'
    # Caso o arquivo não exista localmente (no GitHub), retorna objetos nulos
    if not os.path.exists(caminho):
        # Retorna objetos nulos caso o arquivo não seja encontrado
        return None, None, None
    # Carrega a planilha excel original para manipulação via DataFrame pandas
    dados_brutos = pd.read_excel(caminho)
    # Elimina os registros completamente duplicados da base importada
    dados_brutos = dados_brutos.drop_duplicates()
    # Cria uma cópia limpa contendo apenas registros sem valores ausentes
    dados_historico = dados_brutos.dropna().copy()
    # Inicializa uma cópia dedicada para conversões ordinais para treino do modelo
    dados_treino = dados_historico.copy()
    # Define o dicionário de conversão ordinal de escolaridade para formato numérico
    map_esc = {'Fundamental': 0, 'Médio': 1, 'Superior': 2, 'Pós-graduação': 3}
    # Aplica as substituições numéricas ordinais na coluna Escolaridade
    dados_treino['Escolaridade'] = dados_treino['Escolaridade'].map(map_esc)
    # Define o dicionário de mapeamento categórico de vínculo empregatício
    map_vinc = {'Informal': 0, 'Autônomo': 1, 'CLT': 2}
    # Aplica as substituições numéricas ordinais na coluna Vínculo Empregatício
    dados_treino['Vínculo Empregatício'] = dados_treino['Vínculo Empregatício'].map(map_vinc)
    # Traduz as respostas Sim e Não da posse de imóvel para binários zero e um
    dados_treino['Imóvel Próprio'] = dados_treino['Imóvel Próprio'].map({'Não': 0, 'Sim': 1})
    # Traduz a situação final de adimplência do cliente em zero ou um para treino
    dados_treino['Situação'] = dados_treino['Situação'].map({'Adimplente': 0, 'Inadimplente': 1})
    # Remove qualquer eventual registro contendo nulos restantes após o mapeamento
    dados_treino = dados_treino.dropna()
    # Separa as variáveis explicativas descartando a identificação e a situação alvo
    x_app = dados_treino.drop(columns=['ID do Cliente', 'Situação'])
    # Define a variável alvo com base na coluna binária de Situação ajustada
    y_app = dados_treino['Situação']
    # Cria a instância da regressão logística definindo limite alto de convergência
    modelo = LogisticRegression(max_iter=1000, random_state=42)
    # Executa o ajuste dos coeficientes matemáticos do modelo com toda a base
    modelo.fit(x_app, y_app)
    # Retorna o classificador, a base de dados tratada original e a base convertida
    return modelo, dados_historico, dados_treino

# Executa o carregamento e treinamento do modelo de previsão
modelo, dados, dados_num = treinar_modelo()

# Verifica a ausência do arquivo e apresenta erro explicativo no Streamlit
if modelo is None:
    # Apresenta notificação de alerta em vermelho sobre arquivo de dados ausente e instruções
    st.error('Erro: O arquivo "inadimplencia-clientes.xlsx" não foi localizado no seu repositório do GitHub.')
    # Adiciona instrução para auxiliar no deploy do Streamlit Cloud
    st.info('Por favor, faça o upload do arquivo "inadimplencia-clientes.xlsx" para a pasta raiz do seu repositório no GitHub (onde está o seu app.py).')
    # Interrompe o processamento do Streamlit na página corrente
    st.stop()

# Calcula métricas resumidas para os cartões informativos do painel
total_clientes = len(dados)
# Calcula o valor total de empréstimos concedidos na base histórica
total_emprestado = dados['Valor do Empréstimo (R$)'].sum()
# Calcula o percentual médio de inadimplência real do histórico
taxa_inadimplencia_real = (dados['Situação'].value_counts(normalize=True).get('Inadimplente', 0.0)) * 100

# Cria três colunas horizontais de igual tamanho para exibir os cartões de métrica no topo
met_col1, met_col2, met_col3 = st.columns(3)
# Exibe o cartão da métrica do número total de clientes analisados na coluna 1
met_col1.metric(label='Total de Clientes no Histórico', value=f'{total_clientes}')
# Exibe o cartão do volume financeiro total sob risco ou emprestado na coluna 2
met_col2.metric(label='Volume Total Emprestado', value=f'R$ {total_emprestado:,.2f}')
# Exibe a taxa de inadimplência real calculada para a base de dados na coluna 3
met_col3.metric(label='Taxa de Inadimplência Histórica', value=f'{taxa_inadimplencia_real:.1f}%')

# Divide a tela principal verticalmente em duas grandes colunas
col1, col2 = st.columns(2)

# Bloco de renderização e coleta de dados na coluna da esquerda
with col1:
    # Define o cabeçalho dos parâmetros de simulação individuais do cliente
    st.header('Dados do Cliente para Simulação')
    # Controle numérico do formulário para entrada de idade do proponente
    idade = st.number_input('Idade', min_value=18, max_value=100, value=35)
    # Seleção de string correspondente à escolaridade real do proponente
    escolaridade_str = st.selectbox('Escolaridade', ['Fundamental', 'Médio', 'Superior', 'Pós-graduação'])
    # Seleção de string correspondente ao vínculo de trabalho do proponente
    vinculo_str = st.selectbox('Vínculo Empregatício', ['Informal', 'Autônomo', 'CLT'])
    # Controle numérico do salário ou renda mensal recebida
    renda_mensal = st.number_input('Renda Mensal (R$)', min_value=0.0, max_value=100000.0, value=5000.0, step=100.0)
    # Controle numérico do empréstimo integral pretendido pelo proponente
    valor_emprestimo = st.number_input('Valor do Empréstimo (R$)', min_value=0.0, max_value=1000000.0, value=20000.0, step=500.0)
    # Controle numérico correspondente à parcela do financiamento calculado
    valor_parcela = st.number_input('Valor da Parcela (R$)', min_value=0.0, max_value=50000.0, value=1000.0, step=50.0)
    # Controle numérico da quantidade total de meses para quitação do débito
    prazo = st.number_input('Prazo (meses)', min_value=1, max_value=360, value=24)
    # Controle numérico com a quantidade de atrasos de pagamento anteriores
    atrasos_anteriores = st.number_input('Atrasos Anteriores', min_value=0, max_value=50, value=0)
    # Controle numérico correspondente aos anos de vínculo com a instituição financeira
    tempo_relacionamento = st.number_input('Tempo de Relacionamento (anos)', min_value=0, max_value=50, value=3)
    # Seleção indicando posse declarada de imóvel próprio residencial
    imovel_str = st.selectbox('Imóvel Próprio', ['Não', 'Sim'])

# Converte a string de escolaridade selecionada no seu equivalente numérico do modelo
escolaridade = {'Fundamental': 0, 'Médio': 1, 'Superior': 2, 'Pós-graduação': 3}[escolaridade_str]
# Converte a string do tipo de emprego de vínculo no número do modelo
vinculo = {'Informal': 0, 'Autônomo': 1, 'CLT': 2}[vinculo_str]
# Converte a opção sim ou não de moradia em formato binário zero ou um
imovel = {'Não': 0, 'Sim': 1}[imovel_str]

# Monta uma lista estruturada contendo as variáveis inseridas para uso no preditor
features = [[idade, escolaridade, vinculo, renda_mensal, valor_emprestimo, valor_parcela, prazo, atrasos_anteriores, tempo_relacionamento, imovel]]
# Obtém o diagnóstico de classificação binária gerado pela regressão
previsao = modelo.predict(features)[0]
# Extrai a matriz contendo o percentual de probabilidade estimado para as classes
probabilidade = modelo.predict_proba(features)[0]
# Isola o valor de risco correspondente à inadimplência em percentual direto
probabilidade_inadimplente = probabilidade[1] * 100

# Bloco de exibição de relatórios dinâmicos na coluna da direita
with col2:
    # Define o título da área de relatórios analíticos dinâmicos
    st.header('Resultado da Análise em Tempo Real')
    # Exibe caixa de status dinâmico correspondente à classificação estimada
    if previsao == 1:
        # Mostra indicador vermelho destacando alta probabilidade de inadimplência
        st.error('Situação prevista: Inadimplente')
    else:
        # Mostra indicador verde certificando bom perfil adimplente estimado
        st.success('Situação prevista: Adimplente')

    # Configura e constrói o gráfico de Gauge interativo do Plotly
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probabilidade_inadimplente,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risco de Inadimplência (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "salmon"}
            ]
        }
    ))
    # Renderiza o gráfico de gauge criado na interface do Streamlit
    st.plotly_chart(fig_gauge, use_container_width=True)

# Cria uma linha horizontal para separar as seções de modelagem e exploração visual de dados
st.markdown('---')
# Adiciona o título da seção de análise exploratória interativa no final da página
st.subheader('Análise de Dispersão Histórica dos Clientes')

# Cria o gráfico interativo de dispersão correlacionando as principais variáveis numéricas de concessão
fig_disp = px.scatter(
    dados,
    x='Renda Mensal (R$)',
    y='Valor do Empréstimo (R$)',
    color='Situação',
    title='Relação Renda vs Empréstimo por Status Histórico',
    labels={'Renda Mensal (R$)': 'Renda Mensal (R$)', 'Valor do Empréstimo (R$)': 'Valor do Empréstimo (R$)'},
    color_discrete_map={'Adimplente': 'green', 'Inadimplente': 'red'},
    hover_data=['Idade', 'Escolaridade', 'Atrasos Anteriores']
)
# Apresenta o gráfico de dispersão completo na largura da tela
st.plotly_chart(fig_disp, use_container_width=True)
