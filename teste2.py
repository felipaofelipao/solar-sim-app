import streamlit as st
import pandas as pd
import altair as alt
import locale

# --- CONSTANTES DE SIMULAÇÃO GLOBAIS ---
TAXA_DESEMPENHO = 0.80
POTENCIA_PAINEL_WP = 550
AREA_PAINEL_M2 = 2.3
FATOR_EMISSAO_CO2_KWH = 0.075

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SolarSim | Calculadora Solar", page_icon="☀️", layout="wide")

# --- LOCALE (com fallback) ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass


def formatar_reais(valor: float) -> str:
    try:
        return locale.currency(valor, grouping=True)
    except:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --- BASES ---
HSP_CAPITAIS = {
    "Aracaju (SE)": 5.15, "Belém (PA)": 4.44, "Belo Horizonte (MG)": 5.47,
    "Boa Vista (RR)": 5.37, "Brasília (DF)": 5.61, "Campo Grande (MS)": 5.51,
    "Cuiabá (MT)": 5.51, "Curitiba (PR)": 4.54, "Florianópolis (SC)": 4.68,
    "Fortaleza (CE)": 6.13, "Goiânia (GO)": 5.75, "João Pessoa (PB)": 5.86,
    "Macapá (AP)": 5.10, "Maceió (AL)": 5.67, "Manaus (AM)": 4.27,
    "Natal (RN)": 6.13, "Palmas (TO)": 5.81, "Porto Alegre (RS)": 4.79,
    "Porto Velho (RO)": 4.67, "Recife (PE)": 5.81, "Rio Branco (AC)": 4.21,
    "Rio de Janeiro (RJ)": 5.13, "Salvador (BA)": 5.81, "São Luís (MA)": 6.30,
    "São Paulo (SP)": 4.88, "Teresina (PI)": 6.42, "Vitória (ES)": 5.25,
}

CUSTO_WP_CAPITAIS = {
    "Porto Velho (RO)": 2.17, "Rio Branco (AC)": 2.23, "Manaus (AM)": 2.38, "Boa Vista (RR)": 2.23, "Macapá (AP)": 2.25,
    "Belém (PA)": 2.88, "Palmas (TO)": 2.30, "São Luís (MA)": 2.48, "Teresina (PI)": 2.42, "Fortaleza (CE)": 2.45,
    "Natal (RN)": 2.39, "João Pessoa (PB)": 2.46, "Recife (PE)": 2.49, "Maceió (AL)": 2.39, "Aracaju (SE)": 2.42,
    "Salvador (BA)": 2.48, "Brasília (DF)": 2.52, "Goiânia (GO)": 2.41, "Cuiabá (MT)": 2.29, "Campo Grande (MS)": 2.39,
    "Belo Horizonte (MG)": 2.70, "Vitória (ES)": 2.40, "Rio de Janeiro (RJ)": 2.49, "São Paulo (SP)": 2.40,
    "Curitiba (PR)": 2.38, "Florianópolis (SC)": 2.36, "Porto Alegre (RS)": 2.60,
}


# --- CÁLCULO ---
def calcular_sistema_solar(consumo_kwh, tarifa, hsp, custo_wp_regional):
    consumo_diario_kwh = consumo_kwh / 30
    potencia_necessaria_kwp = consumo_diario_kwh / (hsp * TAXA_DESEMPENHO)
    potencia_necessaria_wp = potencia_necessaria_kwp * 1000

    numero_paineis = max(1, round(potencia_necessaria_wp / POTENCIA_PAINEL_WP))
    area_total_m2 = numero_paineis * AREA_PAINEL_M2
    potencia_final_sistema_wp = numero_paineis * POTENCIA_PAINEL_WP

    geracao_diaria_kwh = (potencia_final_sistema_wp / 1000) * hsp * TAXA_DESEMPENHO
    geracao_mensal_kwh = geracao_diaria_kwh * 30

    custo_total_estimado = potencia_final_sistema_wp * custo_wp_regional
    economia_mensal_reais = min(geracao_mensal_kwh, consumo_kwh) * tarifa

    geracao_anual_kwh = geracao_mensal_kwh * 12
    co2_evitado_anual_kg = geracao_anual_kwh * FATOR_EMISSAO_CO2_KWH

    return {
        "potencia_kwp": round(potencia_final_sistema_wp / 1000, 2),
        "numero_paineis": numero_paineis,
        "area_m2": round(area_total_m2, 2),
        "custo_total_estimado_site": custo_total_estimado,
        "economia_mensal_reais": economia_mensal_reais,
        "co2_evitado_kg": round(co2_evitado_anual_kg, 2),
        "geracao_mensal": round(geracao_mensal_kwh, 2),
    }


def formatar_payback(custo, economia_mensal):
    if economia_mensal > 0:
        payback_anos = custo / (economia_mensal * 12)
    else:
        return "Não aplicável"
    anos = int(payback_anos)
    meses = round((payback_anos - anos) * 12)
    return f"~ {anos} anos e {meses} meses" if anos else f"~ {meses} meses"


# ========= INTERFACE =========
st.title("☀️ SolarSim: Calculadora Solar Residencial")
st.markdown(
    "Simule o custo, economia e benefícios ambientais da energia solar. Preencha os campos abaixo para começar!")
st.divider()

# 1) Inputs
col1, col2 = st.columns(2)
with col1:
    st.subheader("1️⃣ Seus Dados de Consumo")
    consumo = st.number_input("Consumo médio mensal (kWh):", min_value=50, value=300, step=10)
    tarifa = st.number_input("Tarifa de energia (R$/kWh):", min_value=0.30, max_value=1.50, value=0.85, step=0.01,
                             format="%.2f")
with col2:
    st.subheader("2️⃣ Sua Localização")
    cidade_selecionada = st.selectbox("Selecione a capital mais próxima:", sorted(HSP_CAPITAIS.keys()))

hsp = HSP_CAPITAIS[cidade_selecionada]
custo_wp = CUSTO_WP_CAPITAIS[cidade_selecionada]
resultados_tmp = calcular_sistema_solar(consumo, tarifa, hsp, custo_wp)

# 2) Orçamento
st.divider()
st.subheader("3️⃣ Orçamento e Investimento")
col_orc, col_val = st.columns(2)
with col_orc:
    escolha_orcamento = st.radio("Como deseja inserir o valor do investimento?",
                                 ('Usar Orçamento Médio do SolarSim', 'Inserir meu Orçamento Personalizado'),
                                 index=0)
with col_val:
    if escolha_orcamento == 'Inserir meu Orçamento Personalizado':
        custo_final = st.number_input("Valor Total do Orçamento (R$):",
                                      min_value=1000.00,
                                      value=float(round(resultados_tmp["custo_total_estimado_site"], -2)),
                                      step=100.00, format="%.2f")
    else:
        st.markdown("*Estimativa SolarSim:*")
        st.info(formatar_reais(resultados_tmp["custo_total_estimado_site"]))
        custo_final = resultados_tmp["custo_total_estimado_site"]

payback_str = formatar_payback(custo_final, resultados_tmp["economia_mensal_reais"])

# 3) Calcular (salva em session_state)
if st.button("⚡ Calcular meu sistema solar", type="primary", use_container_width=True):
    st.session_state.res = {
        "cidade": cidade_selecionada,
        "hsp": hsp,
        "consumo": consumo,
        "tarifa": tarifa,
        "custo_final": custo_final,
        "dados": resultados_tmp,
        "payback": payback_str,
    }

# 4) Mostrar resultados se houver sessão salva
if "res" in st.session_state:
    R = st.session_state.res
    dados = R["dados"]

    st.divider()
    st.subheader(f"✅ Resultados da Simulação — {R['cidade']}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Investimento Total Considerado", formatar_reais(R["custo_final"]))
        st.metric("Potência do Sistema", f"{dados['potencia_kwp']} kWp")
    with c2:
        st.metric("Economia Mensal Estimada", formatar_reais(dados["economia_mensal_reais"]))
        st.metric("Quantidade de Painéis", f"{dados['numero_paineis']}")
    with c3:
        st.metric("Retorno do Investimento (Payback)", R["payback"])
        st.metric("Área Mínima Necessária", f"{dados['area_m2']} m²")

    st.success(
        f"🌳 *Benefício Ambiental:* Este sistema evita cerca de *{dados['co2_evitado_kg']} kg de CO₂/ano* — o equivalente a *{dados['co2_evitado_kg'] / 150:.1f} árvores!*")

    # ----- Toggle dos gráficos (persistente) -----
    st.subheader("📈 Visualização dos Resultados")
    modo = st.radio("Escolha o tipo de gráfico:", ["Mensal", "Anual"], horizontal=True, key="modo_grafico")

    # Dados mensais com sazonalidade
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    fator_sazonal = [0.95, 0.97, 1.00, 1.05, 1.10, 1.12, 1.08, 1.02, 0.98, 0.96, 0.94, 0.93]
    geracao_mensal = [dados["geracao_mensal"] * f for f in fator_sazonal]

    if modo == "Mensal":
        df = pd.DataFrame({
            "Mês": meses,
            "Consumo (kWh)": [R["consumo"]] * 12,
            "Geração Solar (kWh)": geracao_mensal
        }).melt("Mês", var_name="Categoria", value_name="Energia (kWh)")
        grafico = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("Mês", sort=meses),
            y=alt.Y("Energia (kWh)", title="Energia Mensal (kWh)"),
            color=alt.Color("Categoria", scale=alt.Scale(scheme="goldred")),
            tooltip=["Mês", "Categoria", "Energia (kWh)"]
        ).properties(height=350, title="📊 Comparativo Mensal: Consumo x Geração Solar")
    else:
        df_anual = pd.DataFrame({
            "Categoria": ["Consumo Anual", "Geração Solar Anual"],
            "Energia (kWh/ano)": [R["consumo"] * 12, sum(geracao_mensal)]
        })
        grafico = alt.Chart(df_anual).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x="Categoria",
            y=alt.Y("Energia (kWh/ano)", title="Energia Anual (kWh)"),
            color=alt.Color("Categoria", scale=alt.Scale(scheme="goldred")),
            tooltip=["Categoria", "Energia (kWh/ano)"]
        ).properties(height=350, title="📊 Comparativo Anual: Consumo x Geração Solar")

    st.altair_chart(grafico, use_container_width=True)

    # ----- 💡 Dica (mantida) -----
    st.info(
        "💡 **Dica:** Use a economia mensal para investir em eficiência energética — como iluminação LED e eletrodomésticos classe A!")

    # ----- Premissas (mantido) -----
    with st.expander("📘 Premissas e limitações da simulação"):
        st.markdown(f"""
        - *HSP (Horas de Sol Pleno):* média de *{R['hsp']}h/dia* para {R['cidade']}, baseada em dados do CRESESB/SWERA.  
        - *Taxa de Desempenho (PR):* {int(TAXA_DESEMPENHO * 100)}%.  
        - *Custo médio do Wp instalado na região:* **{formatar_reais(CUSTO_WP_CAPITAIS[R['cidade']])}/Wp**.  
        - *Economia Mensal:* calculada sobre a tarifa cheia informada (não considera taxa mínima da distribuidora).  
        - *Variação sazonal:* padrão médio de irradiação no Brasil.  
        - *Emissão de CO₂ evitada:* fator médio do SIN.  
        """)
    # ----- Quer saber mais? (Com Vídeo Incorporado) -----
    st.subheader("📚 Quer saber mais?")
    with st.expander("Clique aqui para expandir seus conhecimentos sobre Energia Solar"):
        # 1. VÍDEO INCORPORADO
        st.markdown("#### Como Funciona a Energia Solar (Explicação Simples)")
        # Link do vídeo escolhido (Portal Solar)
        st.video("https://www.youtube.com/watch?v=nKdq6BHBR0M")

        st.markdown("---")

        # 2. LINKS DE REGULAMENTAÇÃO E REFERÊNCIA
        st.markdown("*Regulamentação (Lei 14.300 / Geração Distribuída):*")
        st.markdown("- [**ANEEL** — regras para Micro e Minigeração Distribuída](https://www.gov.br/aneel/pt-br)")

        st.markdown("*Benefícios e Guia do Consumidor:*")
        # Mantive o link do Portal Solar aqui também, caso o usuário prefira o texto.
        st.markdown("- [**CRESESB/CEPEL** — Guia do Consumidor](https://cresesb.cepel.br/)")
        st.markdown("- [**Portal Solar** — notícias e fornecedores](https://www.portalsolar.com.br/)")

        st.markdown("*Sustentabilidade:*")
        st.markdown("- [**ABSOLAR** — dados e impacto do setor](https://www.absolar.org.br/)")
