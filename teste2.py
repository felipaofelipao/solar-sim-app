import streamlit as st
import pandas as pd
import altair as alt
import locale
import math
import streamlit.components.v1 as components

# --- CONSTANTES DE SIMULAÇÃO GLOBAIS ---
TAXA_DESEMPENHO = 0.80
# AREA_PAINEL_M2 será dinâmica baseada na escolha
FATOR_EMISSAO_CO2_KWH = 0.075

# --- URLs DAS IMAGENS DE AJUDA ---
URL_AJUDA_CONSUMO = "https://raw.githubusercontent.com/felipaofelipao/solar-sim-app/refs/heads/main/Imagem%20do%20WhatsApp%20de%202025-11-09%20%C3%A0(s)%2017.36.05_00537b91.JPG"
URL_AJUDA_TARIFA = "https://raw.githubusercontent.com/felipaofelipao/solar-sim-app/refs/heads/main/Imagem%20do%20WhatsApp%20de%202025-11-09%20%C3%A0(s)%2017.36.05_52053dd3.JPG"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SolarSim | Simulador Solar", page_icon="☀️", layout="wide")

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "tarifas_list" not in st.session_state:
    st.session_state.tarifas_list = [0.85]
if "tarifa_estimada" not in st.session_state:
    st.session_state.tarifa_estimada = 0.95

# --- CSS GLOBAL (FONTES AUMENTADAS AO MÁXIMO) ---
CSS_APP_STYLE = """
<style>
    /* Aumenta a fonte padrão de todo o texto do corpo */
    html, body, [class*="st-"], [data-testid="stAppViewContainer"], .stMarkdown, .stText, p { 
        font-size: 1.3rem !important; 
    }

    /* Títulos das Métricas (ex: "Investimento Total") */
    div[data-testid="stMetric"] label[data-testid="stMetricLabel"] { 
        font-size: 1.6rem !important; 
        font-weight: 700 !important;
        line-height: 1.4 !important;
    }

    /* Valores das Métricas (ex: "R$ 15.000,00") - SUPER GRANDE */
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { 
        font-size: 4.0rem !important; 
        font-weight: 800 !important;
        color: #0000FF !important; 
        line-height: 1.1 !important;
    }

    /* Ajuste nos textos de ajuda e markdown */
    [data-testid="stTooltipContent"] p { font-size: 1.2rem !important; }
    [data-testid="stExpander"] summary { font-size: 1.5rem !important; font-weight: 600; }
    [data-testid="stInfo"], [data-testid="stSuccess"] { font-size: 1.3rem !important; }

    /* Aumenta a fonte dos inputs e botões */
    .stNumberInput input { font-size: 1.4rem !important; }
    .stSelectbox div[data-baseweb="select"] { font-size: 1.4rem !important; }
    button { font-size: 1.4rem !important; }

    /* Aumenta a fonte dos labels dos inputs */
    .stNumberInput label, .stSelectbox label, .stRadio label {
        font-size: 1.4rem !important;
    }
</style>
"""
st.markdown(CSS_APP_STYLE, unsafe_allow_html=True)

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


# --- BASES DE DADOS ---
HSP_CAPITAIS = {"Rio das Ostras (RJ)": 4.98}
CUSTO_WP_CAPITAIS = {"Rio das Ostras (RJ)": 2.49}


# --- FUNÇÕES DE CÁLCULO ---

def calcular_sistema_solar(consumo_kwh, tarifa, hsp, custo_wp_regional, potencia_painel_escolhido):
    # Define a área baseada na potência do painel (aprox.)
    if potencia_painel_escolhido <= 550:
        area_unitaria = 2.3
    elif potencia_painel_escolhido <= 600:
        area_unitaria = 2.5
    else:
        area_unitaria = 3.1  # Para 700W+

    consumo_diario_kwh = consumo_kwh / 30
    potencia_necessaria_kwp = consumo_diario_kwh / (hsp * TAXA_DESEMPENHO)
    potencia_necessaria_wp = potencia_necessaria_kwp * 1000

    numero_paineis = max(1, math.ceil(potencia_necessaria_wp / potencia_painel_escolhido))
    potencia_final_sistema_wp = numero_paineis * potencia_painel_escolhido
    potencia_kwp_final = potencia_final_sistema_wp / 1000
    area_total_m2 = numero_paineis * area_unitaria
    inversor_kw_rec = potencia_kwp_final / 1.25

    geracao_diaria_kwh = potencia_kwp_final * hsp * TAXA_DESEMPENHO
    geracao_mensal_kwh = geracao_diaria_kwh * 30
    custo_total_estimado = potencia_final_sistema_wp * custo_wp_regional
    economia_mensal_reais = min(geracao_mensal_kwh, consumo_kwh) * tarifa
    geracao_anual_kwh = geracao_mensal_kwh * 12
    co2_evitado_anual_kg = geracao_anual_kwh * FATOR_EMISSAO_CO2_KWH

    custos_detalhados = {
        "Painéis Fotovoltaicos": custo_total_estimado * 0.40,
        "Inversor(es)": custo_total_estimado * 0.20,
        "Estruturas, Cabos e Proteções": custo_total_estimado * 0.15,
        "Mão de Obra e Projeto": custo_total_estimado * 0.25
    }

    return {
        "potencia_kwp": round(potencia_kwp_final, 2),
        "inversor_kw_recomendado": round(inversor_kw_rec, 2),
        "numero_paineis": numero_paineis,
        "area_m2": round(area_total_m2, 2),
        "custo_total_estimado_site": custo_total_estimado,
        "economia_mensal_reais": economia_mensal_reais,
        "co2_evitado_kg": round(co2_evitado_anual_kg, 2),
        "geracao_mensal": round(geracao_mensal_kwh, 2),
        "custos_detalhados": custos_detalhados
    }


def calcular_sistema_por_orcamento(orcamento, custo_wp_regional, consumo_kwh, tarifa, hsp, potencia_painel_escolhido):
    if potencia_painel_escolhido <= 550:
        area_unitaria = 2.3
    elif potencia_painel_escolhido <= 600:
        area_unitaria = 2.5
    else:
        area_unitaria = 3.1

    potencia_final_sistema_wp = orcamento / custo_wp_regional
    potencia_kwp_final = potencia_final_sistema_wp / 1000
    inversor_kw_rec = potencia_kwp_final / 1.25

    numero_paineis = max(1, math.ceil(potencia_final_sistema_wp / potencia_painel_escolhido))
    area_total_m2 = numero_paineis * area_unitaria

    geracao_diaria_kwh = potencia_kwp_final * hsp * TAXA_DESEMPENHO
    geracao_mensal_kwh = geracao_diaria_kwh * 30
    economia_mensal_reais = min(geracao_mensal_kwh, consumo_kwh) * tarifa
    geracao_anual_kwh = geracao_mensal_kwh * 12
    co2_evitado_anual_kg = geracao_anual_kwh * FATOR_EMISSAO_CO2_KWH

    custos_detalhados = {
        "Painéis Fotovoltaicos": orcamento * 0.40,
        "Inversor(es)": orcamento * 0.20,
        "Estruturas, Cabos e Proteções": orcamento * 0.15,
        "Mão de Obra e Projeto": orcamento * 0.25
    }

    return {
        "potencia_kwp": round(potencia_kwp_final, 2),
        "inversor_kw_recomendado": round(inversor_kw_rec, 2),
        "numero_paineis": numero_paineis,
        "area_m2": round(area_total_m2, 2),
        "custo_total_estimado_site": orcamento,
        "economia_mensal_reais": economia_mensal_reais,
        "co2_evitado_kg": round(co2_evitado_anual_kg, 2),
        "geracao_mensal": round(geracao_mensal_kwh, 2),
        "custos_detalhados": custos_detalhados
    }


def estimar_consumo_casa_nova(pessoas, chuveiros, ar_cond, freezer, home_office):
    consumo_base_pessoas = pessoas * 60
    consumo_chuveiros = chuveiros * 70
    consumo_ar = ar_cond * 100
    consumo_freezer = freezer * 40
    consumo_home_office = home_office * 60
    return consumo_base_pessoas + consumo_chuveiros + consumo_ar + consumo_freezer + consumo_home_office


def formatar_payback(custo, economia_mensal):
    if economia_mensal > 0:
        payback_anos = custo / (economia_mensal * 12)
    else:
        return "Não aplicável"
    anos = int(payback_anos)
    meses = round((payback_anos - anos) * 12)
    if meses == 12:
        anos += 1
        meses = 0
    return f"~ {anos} anos e {meses} meses" if anos else f"~ {meses} meses"


def adicionar_campo_tarifa():
    st.session_state.tarifas_list.append(0.0)


def gerar_resumo_txt(R, dados):
    resumo = f"--- RESUMO DA SIMULAÇÃO SOLAR (SolarSim) ---\n\n"
    resumo += f"Localização: {R['cidade']}\n"
    resumo += f"Consumo Mensal Base: {R['consumo']} kWh\n"
    resumo += f"Tarifa Considerada: {formatar_reais(R['tarifa'])} / kWh\n"
    resumo += f"---------------------------------------------\n"
    resumo += f"INVESTIMENTO\n"
    resumo += f"Investimento Total: {formatar_reais(R['custo_final'])}\n"
    resumo += f"Retorno (Payback): {R['payback']}\n"
    resumo += f"Economia Mensal Bruta: {formatar_reais(dados['economia_mensal_reais'])}\n"
    resumo += f"\n"
    resumo += f"---------------------------------------------\n"
    resumo += f"DETALHES DO SISTEMA\n"
    resumo += f"Potência do Sistema: {dados['potencia_kwp']} kWp\n"
    resumo += f"Painéis ({R['painel_escolhido']}W): {dados['numero_paineis']} unid.\n"
    resumo += f"Inversor Rec.: ~{dados['inversor_kw_recomendado']} kW\n"
    resumo += f"Área Mínima: {dados['area_m2']} m²\n"
    return resumo


# ========= INTERFACE =========

st.title("☀️ SolarSim: Simulador Solar Residencial")

st.markdown(
    "Simule o custo, economia e benefícios ambientais da energia solar. Preencha os campos abaixo para começar!")
st.divider()

# --- MODO DE SIMULAÇÃO ---
st.subheader("1️⃣ Modo de Simulação")
modo_simulacao = st.radio(
    "Como deseja simular?",
    ("Com base na minha conta de luz (Já moro no local)",
     "Com base em uma estimativa (Estou construindo)"),
    horizontal=True,
    key="modo_simulacao"
)

# 1) Inputs (Consumo e Localização)
col1, col2 = st.columns(2)
with col1:
    st.subheader("2️⃣ Seus Dados")

    help_texto_tarifa = ""

    if modo_simulacao == "Com base na minha conta de luz (Já moro no local)":
        consumo = st.number_input(
            "Consumo médio mensal (kWh):",
            min_value=50, max_value=10000, value=300, step=10, key="consumo",
            help=f"Abra sua conta de luz e procure pelo 'Total Consumo Mês'.\n\n![Exemplo]({URL_AJUDA_TARIFA})"
        )

        help_texto_tarifa = "Some todos os valores de 'Tarifa de Energia (TE)' e 'Tarifa de Uso (TUSD)' da sua conta."
        st.markdown("**Tarifa de Energia (R$/kWh):**")

        for i in range(len(st.session_state.tarifas_list)):
            help_tarifa_final = None
            if i == 0:
                help_tarifa_final = f"{help_texto_tarifa}\n\n**Exemplo:**\n\n![Exemplo]({URL_AJUDA_CONSUMO})"

            st.session_state.tarifas_list[i] = st.number_input(
                f"Valor {i + 1} (TE ou TUSD)",
                min_value=0.00,
                max_value=3.00,
                value=st.session_state.tarifas_list[i],
                step=0.01,
                format="%.2f",
                key=f"tarifa_input_{i}",
                help=help_tarifa_final
            )

        st.button("Adicionar outro valor (+)", key="add_tarifa", on_click=adicionar_campo_tarifa)
        tarifa_calculada = sum(st.session_state.tarifas_list)
        st.info(f"Sua Tarifa Total: **{formatar_reais(tarifa_calculada)} / kWh**")

    else:  # --- MODO "ESTOU CONSTRUINDO" ---
        st.markdown("Preencha os dados da sua futura casa:")
        c_pessoas = st.number_input("Quantas pessoas vão morar?", min_value=1, value=3, step=1, key="c_pessoas")
        c_chuveiros = st.number_input("Quantos chuveiros elétricos?", min_value=0, value=1, step=1, key="c_chuveiros")
        c_ar = st.number_input("Quantos aparelhos de ar condicionado?", min_value=0, value=1, step=1, key="c_ar")
        c_freezer = st.number_input("Quantos freezers (além da geladeira)?", min_value=0, value=0, step=1,
                                    key="c_freezer")
        c_home_office = st.number_input("Pessoas em home office?", min_value=0, value=0, step=1, key="c_home_office")

        consumo = estimar_consumo_casa_nova(c_pessoas, c_chuveiros, c_ar, c_freezer, c_home_office)
        st.info(f"Seu consumo estimado é de **{consumo} kWh/mês**.")

        tarifa_calculada = st.number_input(
            "Tarifa de energia (R$/kWh):",
            min_value=0.30, max_value=3.00, value=st.session_state.tarifa_estimada, step=0.01, format="%.2f",
            key="tarifa_estimada",
            help="Valor médio estimado da tarifa (TE + TUSD) para Rio das Ostras."
        )

with col2:
    st.subheader("3️⃣ Dados do Sistema")
    cidades_ordenadas = sorted(HSP_CAPITAIS.keys())
    cidade_selecionada = st.selectbox("Localização:", cidades_ordenadas, index=0, key="cidade", disabled=True)

    st.markdown("---")
    # --- OPÇÕES DE PAINEL (550, 600, 700) ---
    potencia_painel_escolhido = st.selectbox(
        "Potência do Painel Solar (Wp):",
        (550, 600, 700),
        index=0,
        key="potencia_painel",
        help="A potência do painel influencia a quantidade de placas necessárias e a área ocupada."
    )

    st.markdown("---")
    st.subheader("Tipo de Conexão (Enel)")
    tipo_conexao = st.selectbox(
        "Qual sua conexão com a rede?",
        ("Monofásica (Taxa Mínima 30 kWh)", "Bifásica (Taxa Mínima 50 kWh)", "Trifásica (Taxa Mínima 100 kWh)"),
        index=1, key="tipo_conexao",
        help="Define a taxa mínima que você sempre pagará."
    )

# Cálculo temporário
hsp = HSP_CAPITAIS[cidade_selecionada]
custo_wp = CUSTO_WP_CAPITAIS[cidade_selecionada]
if 'consumo' not in locals(): consumo = 300
if 'tarifa_calculada' not in locals(): tarifa_calculada = 0.85
resultados_tmp = calcular_sistema_solar(consumo, tarifa_calculada, hsp, custo_wp, potencia_painel_escolhido)

# 2) Orçamento
st.divider()
st.subheader("4️⃣ Orçamento e Investimento")
col_orc, col_val = st.columns(2)
with col_orc:
    escolha_orcamento = st.radio("Como deseja inserir o valor do investimento?",
                                 ('Usar Orçamento Médio do SolarSim', 'Inserir meu Orçamento Personalizado'),
                                 index=0, key="escolha_orc")
with col_val:
    if escolha_orcamento == 'Inserir meu Orçamento Personalizado':
        custo_final = st.number_input("Valor Total do Orçamento (R$):",
                                      min_value=1000.00,
                                      value=float(round(resultados_tmp["custo_total_estimado_site"], -2)),
                                      step=100.00, format="%.2f", key="custo_pers")
    else:
        st.markdown("*Estimativa SolarSim (baseada no seu consumo):*")
        st.info(formatar_reais(resultados_tmp["custo_total_estimado_site"]))
        custo_final = resultados_tmp["custo_total_estimado_site"]

# 3) Botão Calcular
if st.button("⚡ Simular meu sistema solar", type="primary", use_container_width=True):

    # --- ROLAGEM AUTOMÁTICA (MÉTODO ALTERNATIVO ROBUSTO) ---
    # Rola a página para o rodapé (footer) que é um ponto seguro
    js_scroll = """
        <script>
            var body = window.parent.document.querySelector(".main");
            var footer = window.parent.document.querySelector("footer");
            if (footer) {
                footer.scrollIntoView({behavior: "smooth", block: "end"});
            } else {
                body.scrollTop = body.scrollHeight;
            }
        </script>
    """
    components.html(js_scroll, height=0)

    if st.session_state.modo_simulacao == "Com base na minha conta de luz (Já moro no local)":
        consumo_atual = st.session_state.consumo
        tarifa_atual = sum(st.session_state.tarifas_list)
    else:
        consumo_atual = estimar_consumo_casa_nova(
            st.session_state.c_pessoas, st.session_state.c_chuveiros, st.session_state.c_ar, st.session_state.c_freezer,
            st.session_state.c_home_office
        )
        tarifa_atual = st.session_state.tarifa_estimada

    cidade_atual = st.session_state.cidade
    hsp_atual = HSP_CAPITAIS[cidade_atual]
    custo_wp_atual = CUSTO_WP_CAPITAIS[cidade_atual]
    escolha_atual = st.session_state.escolha_orc
    painel_atual = st.session_state.potencia_painel

    conexao_atual = st.session_state.tipo_conexao
    if "Monofásica" in conexao_atual:
        minimo_kwh_atual = 30
    elif "Trifásica" in conexao_atual:
        minimo_kwh_atual = 100
    else:
        minimo_kwh_atual = 50

    if escolha_atual == 'Inserir meu Orçamento Personalizado':
        custo_final_atual = st.session_state.custo_pers
        dados_finais = calcular_sistema_por_orcamento(
            custo_final_atual, custo_wp_atual, consumo_atual, tarifa_atual, hsp_atual, painel_atual
        )
    else:
        dados_finais = calcular_sistema_solar(
            consumo_atual, tarifa_atual, hsp_atual, custo_wp_atual, painel_atual
        )
        custo_final_atual = dados_finais["custo_total_estimado_site"]

    payback_final_str = formatar_payback(custo_final_atual, dados_finais["economia_mensal_reais"])
    saldo_kwh_final = dados_finais["geracao_mensal"] - consumo_atual

    st.session_state.res = {
        "cidade": cidade_atual,
        "hsp": hsp_atual,
        "consumo": consumo_atual,
        "tarifa": tarifa_atual,
        "custo_final": custo_final_atual,
        "dados": dados_finais,
        "payback": payback_final_str,
        "minimo_kwh": minimo_kwh_atual,
        "saldo_kwh": saldo_kwh_final,
        "painel_escolhido": painel_atual
    }

# 4) Mostrar resultados
if "res" in st.session_state:
    R = st.session_state.res
    dados = R["dados"]

    st.divider()
    st.subheader(f"✅ Resultados da Simulação — {R['cidade']}")

    col_dl_1, col_dl_2 = st.columns([3, 1])
    with col_dl_2:
        st.download_button(
            label="📩 Baixar Resumo (.txt)",
            data=gerar_resumo_txt(R, dados),
            file_name="Resumo_SolarSim.txt",
            mime="text/plain",
            use_container_width=True
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Investimento Total Considerado", formatar_reais(R["custo_final"]))
        st.markdown("**Estimativa de Custos:**")
        for item, valor in dados["custos_detalhados"].items():
            st.markdown(f"**- {item}:** {formatar_reais(valor)}")

    with c2:
        st.metric("Potência do Sistema (Painéis)", f"{dados['potencia_kwp']} kWp")
        st.metric(
            "Inversor Recomendado (CA)",
            f"~ {dados['inversor_kw_recomendado']} kW",
            help="Tamanho nominal (CA) do inversor com oversizing de 125%."
        )
        st.metric(f"Quantidade de Painéis ({R['painel_escolhido']}W)", f"{dados['numero_paineis']}")
        st.metric("Área Mínima Necessária", f"{dados['area_m2']} m²")

    with c3:
        st.metric(
            "Economia Mensal Bruta",
            formatar_reais(dados["economia_mensal_reais"]),
            help="Valor máximo de economia na tarifa."
        )

        saldo_kwh = R["saldo_kwh"]
        minimo_kwh = R["minimo_kwh"]
        tarifa = R["tarifa"]

        if saldo_kwh < 0:
            consumo_rede_kwh = abs(saldo_kwh)
            kwh_a_pagar = max(consumo_rede_kwh, minimo_kwh)
            nova_fatura = kwh_a_pagar * tarifa
            st.metric("Nova Fatura Mensal Estimada", formatar_reais(nova_fatura))
            st.metric("Consumo restante da Rede", f"{consumo_rede_kwh:.0f} kWh / mês")
        else:
            creditos_kwh = saldo_kwh
            nova_fatura = minimo_kwh * tarifa
            st.metric("Nova Fatura (Taxa Mínima)", formatar_reais(nova_fatura),
                      help="Custo de disponibilidade da Enel.")
            st.metric("Créditos Gerados", f"{creditos_kwh:.0f} kWh / mês")

        st.metric("Retorno do Investimento (Payback)", R["payback"])

    st.info(
        """
        #### 💡 Qual Tipo de Inversor Escolher?
        * **1. Inversor de String:** Ideal para telhados grandes sem sombra.
        * **2. Microinversor:** Ideal para telhados com sombra ou múltiplas orientações.
        """
    )

    st.success(
        f"🌳 *Benefício Ambiental:* Este sistema evita cerca de **{dados['co2_evitado_kg']:.0f} kg de CO₂/ano** — o equivalente a **{dados['co2_evitado_kg'] / 150:.0f} árvores!**")

    st.caption(
        "**Fontes de Dados:** Irradiação Solar (HSP): **Atlas Solarimétrico CRESESB**. Custos de Mercado: **Relatórios Solfácil/Greener (2024/2025)**.")

    st.subheader("📈 Comparativo Mensal: Consumo x Geração")

    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    fator_sazonal_correto = [1.118, 1.223, 1.052, 1.014, 0.912, 0.890, 0.881, 1.014, 0.960, 0.984, 0.918, 1.042]

    geracao_mensal = [dados["geracao_mensal"] * f for f in fator_sazonal_correto]

    domain_ = ["Consumo (kWh)", "Geração Solar (kWh)"]
    range_ = ["#FF4B4B", "#0068C9"]

    df = pd.DataFrame({
        "Mês": meses,
        "Consumo (kWh)": [R["consumo"]] * 12,
        "Geração Solar (kWh)": geracao_mensal
    }).melt("Mês", var_name="Categoria", value_name="Energia (kWh)")

    grafico = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Mês", sort=meses),
        y=alt.Y("Energia (kWh)", title="Energia Mensal (kWh)"),
        color=alt.Color("Categoria", scale=alt.Scale(domain=domain_, range=range_)),
        tooltip=["Mês", "Categoria", "Energia (kWh)"]
    ).properties(height=350, title="📊 Comparativo Mensal: Consumo x Geração Solar")

    st.altair_chart(grafico, use_container_width=True)

    st.info(
        "💡 **Dica:** A sua geração de energia pode ser maior que o seu consumo! Isso gera créditos de energia que podem ser usados em até 60 meses.")

    with st.expander("📘 Premissas e limitações da simulação"):
        st.markdown(f"""
        - *HSP (Horas de Sol Pleno):* média de *{R['hsp']}h/dia* para {R['cidade']}, baseada em dados do CRESESB/SWERA.    
        - *Taxa de Desempenho (PR):* {int(TAXA_DESEMPENHO * 100)}%.    
        - *Custo médio do Wp instalado na região:* **{formatar_reais(CUSTO_WP_CAPITAIS[R['cidade']])}/Wp**.    
        - *Economia Mensal:* calculada sobre a tarifa cheia informada (não considera taxa mínima da distribuidora).    
        - *Variação sazonal:* padrão médio de irradiação no Brasil.    
        - *Emissão de CO₂ evitada:* fator médio do SIN.
        - **Cabos e Proteções:** O dimensionamento de cabos (bitola) e disjuntores **NÃO** está incluído. Isso deve ser feito por um engenheiro eletricista qualificado durante a visita técnica, pois depende da distância e das condições específicas da sua residência.
        """)

    st.subheader("📚 Quer saber mais?")
    with st.expander("Clique aqui para expandir seus conhecimentos sobre Energia Solar"):
        st.markdown("#### Como Funciona a Energia Solar (Explicação Simples)")
        col_vazio_esq, col_video, col_vazio_dir = st.columns([1, 3, 1])
        with col_video:
            st.video("https://www.youtube.com/watch?v=nKdq6BHBR0M")

        st.caption("Fonte: Canal Engenharia 360 (YouTube)")

        st.markdown("---")

        st.markdown("#### Como funcionam as Tarifas (Ex: Enel)?")
        st.markdown(
            """
            Sua conta de luz não é um valor único. Ela é composta por duas tarifas principais:

            * **TE (Tarifa de Energia):** O custo da energia elétrica que você de fato consumiu.
            * **TUSD (Tarifa de Uso do Sistema de Distribuição):** O custo para "transportar" essa energia até sua casa (uso dos postes, fios, etc.).

            Para o cálculo da **economia** com energia solar, consideramos a soma dessas duas, pois o sistema fotovoltaico gera créditos que abatem ambas as faturas.

            **Cuidado:** Você sempre pagará a **Taxa Mínima** (ou "custo de disponibilidade"), que é uma taxa para estar conectado à rede, mesmo que sua geração seja maior que o consumo. Nosso simulador agora calcula sua nova fatura com base nisso.
            """
        )

        st.markdown("---")

        st.markdown("*Regulamentação (Lei 14.300 / Geração Distribuída):*")
        st.markdown("- [**ANEEL** — regras para Micro e Minigeração Distribuída](https://www.gov.br/aneel/pt-br)")

        st.markdown("*Benefícios e Guia do Consumidor:*")
        st.markdown("- [**CRESESB/CEPEL** — Guia do Consumidor](https://cresesb.cepel.br/)")
        st.markdown("- [**Portal Solar** — notícias e fornecedores](https://www.portalsolar.com.br/)")

        st.markdown("*Sustentabilidade:*")
        st.markdown("- [**ABSOLAR** — dados e impacto do setor](https://www.absolar.org.br/)")


