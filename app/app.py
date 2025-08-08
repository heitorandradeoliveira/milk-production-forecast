import streamlit as st
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
import plotly.graph_objects as go
from datetime import date, datetime
from io import StringIO


# =========================
# CONFIGURAÇÕES INICIAIS
# =========================
st.set_page_config(
    page_title="Sistema de Análise e Previsão de Séries Temporais",
    layout="wide"
)
st.markdown(
    """
    <div style="display:flex; justify-content: flex-end; align-items: center; margin-bottom: 10px;">
        <a href="https://github.com/heitorandradeoliveira" target="_blank" style="text-decoration:none; font-weight:bold; font-size:16px;">
            🚀 github.com/heitorandradeoliveira
        </a>
    </div>
    """,
    unsafe_allow_html=True
)
st.title("📈 Sistema de Análise e Previsão de Séries Temporais")

# =========================
# FUNÇÕES AUXILIARES
# =========================


def carregar_dados(uploaded_file):
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    data = pd.read_csv(stringio, header=None)
    return data


def decompor_serie_plotly(ts_data):
    decomposicao = seasonal_decompose(ts_data, model='additive')

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=ts_data.index, y=ts_data,
                  name="Original", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=ts_data.index, y=decomposicao.trend,
                  name="Tendência", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=ts_data.index, y=decomposicao.seasonal,
                  name="Sazonalidade", line=dict(color="green")))
    fig.add_trace(go.Scatter(x=ts_data.index, y=decomposicao.resid,
                  name="Resíduos", line=dict(color="red")))

    fig.update_layout(
        title="Decomposição da Série Temporal",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom",
                    y=-0.3, xanchor="center", x=0.5)
    )
    return fig


def ajustar_sarima_plotly(ts_data, periodo_previsao):
    modelo = SARIMAX(ts_data, order=(2, 0, 0), seasonal_order=(0, 1, 1, 12))
    modelo_fit = modelo.fit(disp=False)
    previsao = modelo_fit.forecast(steps=periodo_previsao)

    # previsao.index = previsao.index.date

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts_data.index, y=ts_data,
                  mode="lines", name="Histórico", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=previsao.index, y=previsao, mode="lines+markers",
                  name="Previsão", line=dict(color="red", dash="dash")))

    fig.update_layout(
        title="Previsão da Série Temporal",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom",
                    y=-0.3, xanchor="center", x=0.5)
    )

    return fig, previsao


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    uploaded_file = st.file_uploader("📂 Escolha o arquivo CSV:", type=['csv'])
    if uploaded_file:
        data_inicio = date(2000, 1, 1)
        periodo = st.date_input("📅 Período Inicial da Série", data_inicio)
        periodo_previsao = st.number_input(
            "🔮 Meses para prever", min_value=1, max_value=48, value=12)
        processar = st.button("🚀 Processar")

# =========================
# PROCESSAMENTO
# =========================
if uploaded_file and processar:
    try:
        dados = carregar_dados(uploaded_file)
        ts_data = pd.Series(
            dados.iloc[:, 0].values,
            index=pd.date_range(start=periodo, periods=len(dados), freq='M')
        )

        fig_decomposicao = decompor_serie_plotly(ts_data)
        fig_previsao, previsao = ajustar_sarima_plotly(
            ts_data, periodo_previsao)

        # Criar DataFrame da previsão com datas formatadas
        previsao_df = pd.DataFrame(previsao)
        previsao_df = previsao_df.reset_index().rename(
            columns={'index': 'Date', 'predicted_mean': 'Predicted_Value'})
        previsao_df["Date"] = previsao_df["Date"].dt.strftime(
            '%Y-%m-%d')  # formato sem hora

        # Dividir a previsão em colunas
        col1, col2, col3 = st.columns([3, 3, 2])

        with col1:
            st.subheader("📊 Decomposição")
            st.plotly_chart(fig_decomposicao, use_container_width=True)

        with col2:
            st.subheader("🔮 Previsão")
            st.plotly_chart(fig_previsao, use_container_width=True)

        with col3:
            st.subheader("📄 Dados da Previsão")
            st.dataframe(previsao_df)

            # Botão para exportar CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv = previsao_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Baixar CSV",
                data=csv,
                file_name=f"previsao_{timestamp}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Erro ao processar os dados: {e}")
