import sys
import os
from pathlib import Path

# Configurar path para importar módulos do backend
SCRIPT_DIR = Path(__file__).resolve().parent    # models_ml/teste
MODELS_ML_DIR = SCRIPT_DIR.parent               # models_ml
BACKEND_DIR = MODELS_ML_DIR.parent              # backend

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from models import AdvancedCurtailmentPredictor
from app.ml.features import build_training_frame

# Carregar variáveis de ambiente (DATABASE_URL)
load_dotenv(BACKEND_DIR / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")


st.set_page_config(page_title="CurtailIQ - Analytics", layout="wide", page_icon="⚡")

st.title("⚡ CurtailIQ - Visualização Avançada de Modelos de Curtailment")
st.markdown("""
Esta é uma simulação do painel analítico alimentado diretamente pelos modelos de Machine Learning (Prophet + CatBoost) 
e de Insights (PCA/KNN). Os dados são extraídos em tempo real do banco de dados (Camada Gold).
""")

@st.cache_resource
def get_engine():
    if not DATABASE_URL:
        st.warning("⚠️ DATABASE_URL não encontrada no .env do backend. Certifique-se de configurar a conexão com o banco de dados.")
        st.stop()
    return create_engine(DATABASE_URL)

@st.cache_data(ttl=3600)
def load_data(lookback_days: int = 14, max_usinas: int = 10):
    """Carrega dados locais cacheados ou do PostgreSQL."""
    cache_dir = BACKEND_DIR / "models_ml" / "data_ml" / "temp_cache"
    usinas_file = cache_dir / "usinas_cache.csv"
    eolica_file = cache_dir / "flat_dados_eolica.csv"
    solar_file = cache_dir / "flat_dados_solar.csv"
    
    if usinas_file.exists() and eolica_file.exists() and solar_file.exists():
        usinas = pd.read_csv(usinas_file)
        df_eolica = pd.read_csv(eolica_file)
        df_solar = pd.read_csv(solar_file)
        df = pd.concat([df_eolica, df_solar], ignore_index=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', utc=True)
        
        # Filtra o df local baseado no MAIOR timestamp presente nos dados (evita erro de dados antigos)
        max_ts = df['timestamp'].max()
        if pd.isna(max_ts):
            max_ts = pd.to_datetime('now', utc=True).tz_localize(None)
            
        limit_date = max_ts - pd.Timedelta(days=lookback_days)
        
        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)
            if limit_date.tz is not None:
                limit_date = limit_date.tz_localize(None)
                
        df = df[df['timestamp'] >= limit_date].copy()
    else:
        # Fallback query se os arquivos não existirem
        engine = get_engine()
        usinas_sql = text("""
            SELECT DISTINCT id_ons AS usina_id, nom_usina AS nome, 'eolica' AS fonte, 
                   'NE' AS submercado, 50.0 AS potencia_mw
            FROM public.restricao_coff_eolica_usi
            WHERE id_ons IS NOT NULL
            LIMIT :max_usinas
        """)
        
        with engine.connect() as conn:
            usinas = pd.read_sql(usinas_sql, conn, params={"max_usinas": max_usinas})
            if usinas.empty:
                st.warning("Nenhuma usina eólica encontrada.")
                st.stop()
                
            usinas_list = tuple(usinas['usina_id'].tolist())
            import datetime
            limit_date_str = (datetime.datetime.now() - datetime.timedelta(days=lookback_days)).strftime("%Y-%m-%d")
            
            flat_query = text("""
                SELECT 
                    id_ons AS usina_id,
                    CAST(din_instante AS timestamp) AS timestamp,
                    CAST(REPLACE(val_geracao, ',', '.') AS double precision) AS geracao_mwh,
                    CAST(REPLACE(val_disponibilidade, ',', '.') AS double precision) AS capacidade_mwh,
                    CAST(REPLACE(val_geracaoreferenciafinal, ',', '.') AS double precision) AS energia_restringida_mwh,
                    cod_razaorestricao AS razao_restricao
                FROM public.restricao_coff_eolica_usi
                WHERE id_ons IN :usinas
                  AND din_instante >= :limit_date_str
                LIMIT 10000
            """)
            df = pd.read_sql(flat_query, conn, params={"usinas": usinas_list, "limit_date_str": limit_date_str})
        
    if df.empty:
        st.warning("Nenhum dado temporal encontrado.")
        st.stop()
        
    df['energia_restringida_mwh'] = df['energia_restringida_mwh'].fillna(0).apply(lambda x: max(0, x))
    df['geracao_mwh'] = df['geracao_mwh'].fillna(0).apply(lambda x: max(0, x))
    df['houve_corte'] = (df['energia_restringida_mwh'] > 1.0).astype(int)
    
    # Feature engineering basico para suportar o preditor
    df['fator_capacidade'] = np.where(df['capacidade_mwh'] > 0, df['geracao_mwh'] / df['capacidade_mwh'], 0)
    df['vento_ms'] = 7.0 # Default mock
    df['irradiancia_wm2'] = 0.0
    df['temperatura_c'] = 25.0
    df['pld_reais_mwh'] = 200.0
    df['hora'] = df['timestamp'].dt.hour
    df['dia_semana'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['dia_semana'].isin([5, 6]).astype(int)
    df['mm_corte_3h'] = df.groupby('usina_id')['energia_restringida_mwh'].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df['mm_corte_24h'] = df.groupby('usina_id')['energia_restringida_mwh'].transform(lambda x: x.rolling(24, min_periods=1).mean())
    
    return usinas, df

@st.cache_resource
def load_predictor(fonte: str):
    model_name = f"curtailment_model_{fonte}.pkl"
    model_path = BACKEND_DIR / "models_ml" / "data_ml" / model_name
    if not model_path.exists():
        fallback_path = BACKEND_DIR / "models_ml" / "data_ml" / "curtailment_model_advanced.pkl"
        if fallback_path.exists():
            return AdvancedCurtailmentPredictor(str(fallback_path))
        st.error(f"Modelo não encontrado em: {model_path}. Treine o modelo primeiro.")
        st.stop()
    return AdvancedCurtailmentPredictor(str(model_path))

# Sidebar params
st.sidebar.header("Filtros")
lookback = st.sidebar.slider("Dias de Histórico (Lookback)", 7, 30, 14)
max_u = st.sidebar.number_input("Máximo de Usinas a Analisar", 1, 50, 5)

with st.spinner("Conectando ao banco flat (Extração Otimizada sem ER)..."):
    try:
        usinas, usina_full_frame = load_data(lookback, max_u)
        frame = usina_full_frame
    except Exception as e:
        st.error(f"Falha ao consultar banco: {e}")
        st.stop()

# ==========================================
# Seleção de Usina
# ==========================================
st.sidebar.divider()
st.sidebar.subheader("Contexto de Análise")

# Filtra usinas para mostrar apenas as que tem dados no período selecionado
usinas_com_dados = frame['usina_id'].unique()
usinas_validas = usinas[usinas['usina_id'].isin(usinas_com_dados)]

if usinas_validas.empty:
    st.warning("Não há usinas com dados no período selecionado (Lookback).")
    st.stop()

usina_opts = usinas_validas.to_dict('records')
selected_usina_str = st.sidebar.selectbox(
    "Selecione a Usina para detalhamento", 
    [f"{u['usina_id']} - {u['nome']} ({u['fonte']})" for u in usina_opts]
)
selected_usina_id = selected_usina_str.split(" - ")[0]
selected_usina_info = next(u for u in usina_opts if u['usina_id'] == selected_usina_id)

usina_frame = frame[frame["usina_id"] == selected_usina_id].copy()
if usina_frame.empty:
    st.warning("Não há dados suficientes para a usina selecionada neste período.")
    st.stop()

predictor = load_predictor(selected_usina_info['fonte'])

# Fazer predições
with st.spinner(f"Processando predições e explicabilidade ({selected_usina_info['fonte']})..."):
    predictions = predictor.predict_detailed(
        usina_frame, 
        pld_medio_reais_mwh=200.0, 
        usina_info=selected_usina_info
    )

# ==========================================
# VISUALIZAÇÕES
# ==========================================

resumo = predictions['resumo']
try:
    from models_ml.knn_pca_insights import run_knn_analysis
    knn = run_knn_analysis(frame, n_neighbors=7)
except Exception as e:
    knn = {}

# Abas replicando o Frontend
tab_resumo, tab_mapa, tab_financeiro, tab_regulatorio, tab_ml, tab_ml_debug = st.tabs([
    "Visão Geral", "Mapa H3 (Densidade)", "Financeiro", "Regulatório", "ML Insights", "ML Debug"
])

# Preparar dados para as abas (simulando os endpoints do backend)
df_preds = pd.DataFrame(predictions['previsoes'])
if not df_preds.empty:
    df_preds['timestamp'] = pd.to_datetime(df_preds['timestamp'])

usina_hist = usina_frame[usina_frame['energia_restringida_mwh'] > 0].copy()
if not usina_hist.empty:
    # Simulando razões para o gráfico (já que o mock extrai como 'desconhecida')
    import numpy as np
    np.random.seed(42)
    usina_hist['razao'] = np.random.choice(['Confiabilidade', 'Energético', 'Indisponibilidade Externa'], size=len(usina_hist), p=[0.4, 0.4, 0.2])
    usina_hist['perda_reais'] = usina_hist['energia_restringida_mwh'] * usina_hist['pld_reais_mwh']
else:
    usina_hist = pd.DataFrame(columns=['timestamp', 'energia_restringida_mwh', 'pld_reais_mwh', 'razao', 'perda_reais'])

# --- ABA 1: VISÃO GERAL ---
with tab_resumo:
    st.subheader(f"Resumo da Usina: {selected_usina_info['nome']} ({selected_usina_info['fonte'].title()})")
    c1, c2, c3, c4 = st.columns(4)
    
    total_perda = usina_hist['perda_reais'].sum() if not usina_hist.empty else 0
    total_energia = usina_hist['energia_restringida_mwh'].sum() if not usina_hist.empty else 0
    ressarcivel = usina_hist[usina_hist['razao'] == 'Indisponibilidade Externa']['perda_reais'].sum() if not usina_hist.empty else 0
    pct_ressarcivel = (ressarcivel / total_perda * 100) if total_perda > 0 else 0
    
    # 30-day forecast using Prophet
    prophet_30d = predictor.get_prophet_forecast(720) # 30 days
    total_mwh_30d = 0
    total_rs_30d = 0
    df_30d = pd.DataFrame()
    if prophet_30d and "previsao_serie_temporal" in prophet_30d:
        df_30d = pd.DataFrame(prophet_30d["previsao_serie_temporal"])
        df_30d['timestamp'] = pd.to_datetime(df_30d['timestamp'])
        total_mwh_30d = df_30d["valor_previsto_mwh"].sum()
        total_rs_30d = total_mwh_30d * 200.0 # PLD mock
    
    c1.metric("Perda total", f"R$ {total_perda:,.2f}", f"{total_energia:.1f} MWh cortados")
    c2.metric("Ressarcível", f"{pct_ressarcivel:.1f}%", "do total perdido")
    c3.metric("Eventos de corte", len(usina_hist), f"Ticket médio R$ {(total_perda/len(usina_hist)):,.2f}" if len(usina_hist) else "")
    c4.metric("Perda esperada (Próx 30 dias)", f"R$ {total_rs_30d:,.2f}", f"{total_mwh_30d:,.1f} MWh projetados")
    
    if not df_30d.empty:
        st.markdown("**Série Temporal Futura (30 Dias) - Prophet**")
        
        # Agrupar por dia para facilitar a visualização 
        df_30d_diario = df_30d.groupby(df_30d['timestamp'].dt.date).agg({'valor_previsto_mwh': 'sum'}).reset_index()
        fig_30d = px.line(df_30d_diario, x='timestamp', y='valor_previsto_mwh', 
                          title="Previsão de Curtailment Diário - Próximos 30 dias",
                          labels={'valor_previsto_mwh': 'MWh Previstos', 'timestamp': 'Data'})
        fig_30d.update_traces(line_color='#FF4B4B')
        st.plotly_chart(fig_30d, use_container_width=True)

# --- ABA 2: FINANCEIRO ---
with tab_financeiro:
    st.subheader("Análise Financeira")
    c1, c2 = st.columns(2)
    c1.metric("Perda realizada (Histórico)", f"R$ {total_perda:,.2f}")
    c2.metric("Energia restringida", f"{total_energia:.1f} MWh")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("**Perda por razão**")
        if not usina_hist.empty:
            fig_pie = px.pie(usina_hist, values='perda_reais', names='razao', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    with col_chart2:
        st.markdown("**Perda temporal com PLD**")
        if not usina_hist.empty:
            fig_line = px.bar(usina_hist, x='timestamp', y='perda_reais', color='razao')
            st.plotly_chart(fig_line, use_container_width=True)
            
    st.info(f"**Exposição futura (48h)**: R$ {resumo['impacto_estimado']['perda_total_estimada_reais']:,.2f} | PLD médio considerado: R$ 200/MWh")

# --- ABA 3: REGULATÓRIO ---
with tab_regulatorio:
    st.subheader("Fluxo completo do agente de ressarcimento")
    st.markdown("Reconciliação e Elegibilidade (Simulado)")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Potencial bruto", f"R$ {ressarcivel:,.2f}")
    c2.metric("Ressarcível pós-franquia", f"R$ {max(0, ressarcivel - 5000):,.2f}")
    c3.metric("Franquia aplicada", "82 h")
    c4.metric("Horas excedentes", "14 h")
    
    st.markdown("**Eventos de elegibilidade**")
    if not usina_hist.empty:
        df_table = usina_hist[['timestamp', 'razao', 'energia_restringida_mwh', 'perda_reais']].copy()
        df_table['Elegível'] = df_table['razao'].apply(lambda x: 'Sim' if x == 'Indisponibilidade Externa' else 'Não')
        st.dataframe(df_table, use_container_width=True)

# --- ABA 4: ML INSIGHTS (CatBoost, Prophet, KNN) ---
with tab_ml:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📈 Previsão e Risco de Curtailment 48h")
        if not df_preds.empty:
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Bar(
                x=df_preds['timestamp'], y=df_preds['prob_corte'],
                name="Risco (Probabilidade)", marker_color='rgba(255, 99, 132, 0.4)', yaxis='y2'
            ))
            fig_risk.add_trace(go.Scatter(
                x=df_preds['timestamp'], y=df_preds['magnitude_estimada_mwh'],
                mode='lines+markers', name="Magnitude Estimada (MWh)",
                line=dict(color='rgba(54, 162, 235, 1)', width=3), marker=dict(size=8)
            ))
            fig_risk.update_layout(
                title="Probabilidade vs Magnitude Estimada (CatBoost)",
                yaxis=dict(title="MWh"),
                yaxis2=dict(title="Probabilidade", overlaying='y', side='right', range=[0, 1]),
                hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_risk, use_container_width=True)

    with col_right:
        st.subheader("🚨 Alertas Automáticos")
        if predictions.get('alertas'):
            for alerta in predictions['alertas'][:5]:
                ts_str = pd.to_datetime(alerta['timestamp']).strftime('%d/%m %H:%M')
                st.error(f"**{ts_str}** | Risco: {alerta['prob_corte_pct']}\n\nMagnitude: {alerta['magnitude_estimada_mwh']} MWh\n\n*{alerta['recomendacao']}*")
        else:
            st.success("Nenhum alerta crítico gerado para as próximas 48h.")

    st.divider()

    c_exp, c_prophet = st.columns([1, 1])
    with c_exp:
        st.subheader("🧠 Explicabilidade (CatBoost)")
        if not usina_frame.empty and not df_preds.empty:
            idx_max_risco = df_preds['prob_corte'].idxmax()
            row_max_risco = usina_frame.iloc[idx_max_risco]
            explicacao = predictor.explain_prediction(row_max_risco)
            df_expl = pd.DataFrame(explicacao['fatores_contribuintes'])
            if not df_expl.empty:
                df_expl = df_expl.sort_values('importancia_global', ascending=True)
                fig_fi = px.bar(df_expl, x='importancia_global', y='feature', orientation='h', color_discrete_sequence=['#4BC0C0'])
                st.plotly_chart(fig_fi, use_container_width=True)

    with c_prophet:
        st.subheader("⏱️ Decomposição (Prophet)")
        decomposicao = predictions.get('decomposicao_temporal')
        if decomposicao and 'componentes' in decomposicao and decomposicao['componentes']:
            comp_tabs = st.tabs(list(decomposicao['componentes'].keys()))
            for t, (nome, comp) in zip(comp_tabs, decomposicao['componentes'].items()):
                with t:
                    st.info(comp['interpretacao'])
                    df_comp = pd.DataFrame(comp['valores'])
                    df_comp['timestamp'] = pd.to_datetime(df_comp['timestamp'])
                    st.line_chart(data=df_comp, x='timestamp', y='efeito_mwh')
        else:
            st.warning("Decomposição Prophet sem componentes suficientes nesta janela de tempo.")

    st.divider()
    
    st.subheader("🔍 Benchmarking Operacional (Mapa de Calor KNN)")
    st.markdown("Similaridade de perfil operacional entre as usinas e mapa de calor de risco de corte.")
    
    if not frame.empty and "usina_id" in frame.columns:
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import pairwise_distances
        
        cols_to_use = ["geracao_mwh", "capacidade_mwh", "mm_corte_3h", "mm_corte_24h", "energia_restringida_mwh"]
        available_cols = [c for c in cols_to_use if c in frame.columns]
        
        # Perfil médio para KNN Similarity
        usina_profiles = frame.groupby("usina_id")[available_cols].mean()
        
        if len(usina_profiles) > 1:
            scaled_profiles = StandardScaler().fit_transform(usina_profiles.fillna(0))
            dist_matrix = pairwise_distances(scaled_profiles, metric="euclidean")
            
            usinas_names = [str(u) for u in usina_profiles.index]
            df_dist = pd.DataFrame(dist_matrix, index=usinas_names, columns=usinas_names)
            
            # Converter distância para similaridade (Inverso)
            sim_matrix = 1 / (1 + df_dist)
            
            c_hm1, c_hm2 = st.columns(2)
            
            with c_hm1:
                fig_sim = px.imshow(
                    sim_matrix, 
                    text_auto=".2f", 
                    color_continuous_scale="Blues", 
                    title="Matriz de Similaridade KNN entre Usinas",
                    labels=dict(x="Usina", y="Usina", color="Similaridade")
                )
                st.plotly_chart(fig_sim, use_container_width=True)
                
            with c_hm2:
                if "hora" in frame.columns and "houve_corte" in frame.columns:
                    heatmap_data = frame.groupby(["usina_id", "hora"])["houve_corte"].mean().reset_index()
                    heatmap_pivot = heatmap_data.pivot(index="usina_id", columns="hora", values="houve_corte").fillna(0)
                    
                    fig_heat = px.imshow(
                        heatmap_pivot,
                        labels=dict(x="Hora do Dia", y="Usina", color="Prob. Corte"),
                        x=heatmap_pivot.columns,
                        y=heatmap_pivot.index,
                        color_continuous_scale="YlOrRd",
                        aspect="auto",
                        title="Mapa de Calor: Maior Chance de Cortes por Horário"
                    )
                    st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Apenas uma usina no dataset atual. Carregue mais usinas (Max Usinas > 1) para o Benchmarking KNN.")

with tab_mapa:
    st.header("🗺️ Densidade de Restrição (H3 Hexagonal)")
    st.markdown("Visão espacial da intensidade de curtailment utilizando índices **[H3 da Uber](https://h3geo.org/)**.")
    
    if not usina_full_frame.empty:
        import h3
        import pydeck as pdk
        import numpy as np
        
        # 1. Obter intensidade total por usina
        intensidade_df = usina_full_frame.groupby('usina_id')['energia_restringida_mwh'].sum().reset_index()
        
        # Obter nome das usinas lidando com os IDs 'fakes' do csv temporário
        usina_id_to_name = dict(zip(usinas['usina_id'], usinas['nome']))
        def resolve_nome(uid):
            base_id = str(uid).split('_fake_')[0]
            return usina_id_to_name.get(base_id, str(uid))
            
        intensidade_df['usina_nome'] = intensidade_df['usina_id'].apply(resolve_nome)
        
        # 2. Gerar coordenadas simuladas (Foco no cluster eólico do Piauí/Bahia/RN - NE)
        # Em produção, essas coordenadas viriam da base de dados.
        np.random.seed(42)
        usinas_ids = intensidade_df['usina_id'].unique()
        lats = np.random.normal(-8.2, 1.5, len(usinas_ids))
        lons = np.random.normal(-41.2, 1.5, len(usinas_ids))
        coords_dict = {u: (lat, lon) for u, lat, lon in zip(usinas_ids, lats, lons)}
        
        intensidade_df['lat'] = intensidade_df['usina_id'].map(lambda x: coords_dict[x][0])
        intensidade_df['lon'] = intensidade_df['usina_id'].map(lambda x: coords_dict[x][1])
        
        # Usar H3 resolution 5
        intensidade_df['hex_id'] = intensidade_df.apply(lambda row: h3.latlng_to_cell(row['lat'], row['lon'], 5), axis=1)
        
        # 3. Agregar dados por Hexágono H3
        hex_data = intensidade_df.groupby('hex_id').agg(
            intensidade_mwh=('energia_restringida_mwh', 'sum'),
            lat=('lat', 'mean'),
            lon=('lon', 'mean'),
            usinas_names=('usina_nome', lambda x: ', '.join(x.dropna().astype(str).unique()))
        ).reset_index()
        
        # Normalizar para cor e definir Risco
        max_int = hex_data['intensidade_mwh'].max()
        hex_data['elevation_norm'] = hex_data['intensidade_mwh'] / max_int if max_int > 0 else 0
        
        q33 = hex_data['intensidade_mwh'].quantile(0.33)
        q66 = hex_data['intensidade_mwh'].quantile(0.66)
        
        def get_risk_color(val):
            if val <= q33:
                return [46, 204, 113, 220] # Verde (Bom)
            elif val <= q66:
                return [241, 196, 15, 220] # Amarelo (Médio)
            else:
                return [231, 76, 60, 220] # Vermelho (Risco)
                
        def get_risk_label(val):
            if val <= q33:
                return "Bom"
            elif val <= q66:
                return "Médio"
            else:
                return "Risco"
                
        hex_data['fill_color'] = hex_data['intensidade_mwh'].apply(get_risk_color)
        hex_data['risco_label'] = hex_data['intensidade_mwh'].apply(get_risk_label)
        
        # 4. Camada H3
        layer = pdk.Layer(
            "H3HexagonLayer",
            hex_data,
            pickable=True,
            stroked=True,
            filled=True,
            extruded=True,
            get_hexagon="hex_id",
            get_fill_color="fill_color", 
            get_elevation="intensidade_mwh",
            elevation_scale=50,
        )

        view_state = pdk.ViewState(
            latitude=-8.2,
            longitude=-41.2,
            zoom=5.5,
            pitch=45,
            bearing=15
        )

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "Usina(s): {usinas_names}\nStatus: {risco_label}\nIntensidade de Corte: {intensidade_mwh} MWh\nH3 Cell: {hex_id}"},
            map_style=pdk.map_styles.DARK
        )

        st.pydeck_chart(r, use_container_width=True)
        
        # Tabela com ranking H3
        st.markdown("**Top Hexágonos por Intensidade de Restrição (MWh)**")
        st.dataframe(
            hex_data[['hex_id', 'intensidade_mwh']].sort_values('intensidade_mwh', ascending=False).head(5),
            use_container_width=True
        )

with tab_ml_debug:
    st.header("🛠️ ML Debug & Cache Validator")
    st.markdown("Aba dedicada para debugar os modelos de ML e validar o estado dos arquivos temporais do Cache (Técnica Temp CSV).")
    
    st.subheader("📁 Status do Cache Temp (Flat CSV)")
    cache_file = BACKEND_DIR / "models_ml" / "teste" / "temp_cache" / "flat_dados_cache.csv"
    if cache_file.exists():
        size_mb = cache_file.stat().st_size / (1024 * 1024)
        st.success(f"Cache temporal ativo: `flat_dados_cache.csv` ({size_mb:.2f} MB)")
        st.json({"total_linhas_carregadas": len(usina_full_frame), "usinas_no_cache": usina_full_frame['usina_id'].nunique()})
        st.dataframe(usina_full_frame.head(5), use_container_width=True)
    else:
        st.error("Cache temporal não encontrado. Execute o script `extract_cache.py` para gerar.")
        
    st.subheader("🔮 Output Cru: CatBoost (Predição Avançada)")
    if 'predictions' in locals() and predictions:
        st.json(predictions['resumo'])
        
    st.subheader("📉 Output Cru: Prophet (Decomposição Temporal)")
    if prophet_30d:
        st.json({
            "horizonte_horas": prophet_30d.get("horizonte_horas"),
            "sample_previsao": prophet_30d.get("previsao_serie_temporal", [])[:3]
        })
    else:
        st.warning("Prophet falhou em gerar série futura.")
        
    st.subheader("🤝 Output Cru: KNN (Similaridade e Benchmarking)")
    if knn and 'similaridade_usinas' in knn:
        st.json(knn['similaridade_usinas'])
