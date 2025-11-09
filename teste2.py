import streamlit as st
import pandas as pd
import altair as alt
import locale

# --- CONSTANTES DE SIMULAÇÃO GLOBAIS ---
TAXA_DESEMPENHO = 0.80
POTENCIA_PAINEL_WP = 550
AREA_PAINEL_M2 = 2.3
FATOR_EMISSAO_CO2_KWH = 0.075

# --- URLs DAS IMAGENS DE AJUDA (JÁ HOSPEDADAS) ---
URL_AJUDA_CONSUMO = "https://i.imgur.com/kSrxp2s.png"
URL_AJUDA_TARIFA = "https://i.imgur.com/iREm1kY.png"


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="SolarSim | Simulador Solar", page_icon="☀️", layout="wide")

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "tamanho_fonte" not in st.session_state:
    st.session_state.tamanho_fonte = "Padrão"
if "tarifas_list" not in st.session_state:
    st.session_state.tarifas_list = [0.85]

# --- SIDEBAR DE ACESSIBILIDADE ---
st.sidebar.title("♿ Opções de Acessibilidade")
st.sidebar.markdown("Use esta opção caso tenha dificuldade de leitura.")
st.sidebar.radio(
    "Tamanho da Fonte",
    ("Padrão", "Grande", "Muito Grande"),
    key="tamanho_fonte",
    help="Aumenta o tamanho de todas as fontes no simulador."
)

# --- CSS CONDICIONAL (COM CORREÇÃO PARA METRICS) ---
CSS_GRANDE = """
<style>
    html, body, [class*="st-"], [data-testid="stAppViewContainer"] { font-size: 1.15rem; }
    [data-testid="stMetricLabel"] { font-size: 1.1rem !important; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; }
    [data-testid="stTooltipContent"] p { font-size: 1.1rem; }
    [data-testid="stExpander"] summary { font-size: 1.25rem; }
    [data-testid="stInfo"], [data-testid="stSuccess"] { font-size: 1.1rem; }
</style>
"""

CSS_MUITO_GRANDE = """
<style>
    html, body, [class*="st-"], [data-testid="stAppViewContainer"] { font-size: 1.25rem; }
    [data-testid="stMetricLabel"] { font-size: 1.2rem !important; }
    [data-testid="stMetricValue"] { font-size: 2.5rem !important; }
    [data-testid="stTooltipContent"] p { font-size: 1.2rem; }
    [data-testid="stExpander"] summary { font-size: 1.35rem; }
    [data-testid="stInfo"], [data-testid="stSuccess"] { font-size: 1.2rem; }
</style>
"""

if st.session_state.tamanho_fonte == "Grande":
    st.markdown(CSS_GRANDE, unsafe_allow_html=True)
elif st.session_state.tamanho_fonte == "Muito Grande":
    st.markdown(CSS_MUITO_GRANDE, unsafe_allow_html=True)


# --- LOCALE (com fallback) ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    pass

def formatar_reais(valor: float) -> str:
    """Formata um float para o padrão R$ X.XXX,XX com fallback."""
    try:
        return locale.currency(valor, grouping=True)
    except:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- BASES DE DADOS (Foco em Rio das Ostras) ---
HSP_CAPITAIS = { "Rio das Ostras (RJ)": 4.98 }
CUSTO_WP_CAPITAIS = { "Rio das Ostras (RJ)": 2.49 }


# --- FUNÇÕES DE CÁLCULO (COM ESTRATIFICAÇÃO E INVERSOR) ---

def calcular_sistema_solar(consumo_kwh, tarifa, hsp, custo_wp_regional):
    """Calculadora por Consumo (kWh -> R$)"""
    consumo_diario_kwh = consumo_kwh / 30
    potencia_necessaria_kwp = consumo_diario_kwh / (hsp * TAXA_DESEMPENHO)
    potencia_necessaria_wp = potencia_necessaria_kwp * 1000

    numero_paineis = max(1, round(potencia_necessaria_wp / POTENCIA_PAINEL_WP))
    potencia_final_sistema_wp = numero_paineis * POTENCIA_PAINEL_WP
    potencia_kwp_final = potencia_final_sistema_wp / 1000
    area_total_m2 = numero_paineis * AREA_PAINEL_M2
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

def calcular_sistema_por_orcamento(orcamento, custo_wp_regional, consumo_kwh, tarifa, hsp):
    """Calculadora por Orçamento (R$ -> kWh)"""
    
    potencia_final_sistema_wp = orcamento / custo_wp_regional
    potencia_kwp_final = potencia_final_sistema_wp / 1000
    inversor_kw_rec = potencia_kwp_final / 1.25
    numero_paineis = max(1, round(potencia_final_sistema_wp / POTENCIA_PAINEL_WP))
    area_total_m2 = numero_paineis * AREA_PAINEL_M2

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
    """Estima o consumo para uma casa nova (simulação)."""
    consumo_base_pessoas = pessoas * 60
    consumo_chuveiros = chuveiros * 70
    consumo_ar = ar_cond * 100
    consumo_freezer = freezer * 40
    consumo_home_office = home_office * 60
    
    return consumo_base_pessoas + consumo_chuveiros + consumo_ar + consumo_freezer + consumo_home_office

def formatar_payback(custo, economia_mensal):
    """Calcula e formata o payback em anos e meses."""
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

# ========= INTERFACE =========

st.title("☀️ SolarSim: Simulador Solar Residencial")

st.info("👀 Dificuldade para ler? Ajuste o tamanho da fonte na barra lateral à esquerda!", icon="♿")

st.markdown("Simule o custo, economia e benefícios ambientais da energia solar. Preencha os campos abaixo para começar!")
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
    
    # Variável para armazenar o texto de ajuda dinâmico
    help_texto_tarifa = "" 
    
    # Lógica condicional para consumo
    if modo_simulacao == "Com base na minha conta de luz (Já moro no local)":
        
        consumo = st.number_input(
            "Consumo médio mensal (kWh):", 
            min_value=50, max_value=10000, value=300, step=10, key="consumo",
            help=f"""
            Abra sua conta de luz (Ex: Enel) e procure pelo campo 'Consumo Faturado em kWh' ou 'Total Consumo Mês'.
            
            **Veja onde encontrar:**
            
            ![Exemplo Conta de Luz](https://raw.githubusercontent.com/felipaofelipao/solar-sim-app/refs/heads/main/Imagem%20do%20WhatsApp%20de%202025-11-09%20%C3%A0(s)%2017.36.05_52053dd3.JPG)
            """
        )
        
        # MUDANÇA: Texto de ajuda para quem TEM conta
        help_texto_tarifa = "Some todos os valores de 'Tarifa de Energia (TE)' e 'Tarifa de Uso (TUSD)' da sua conta. Use o botão '+' para adicionar quantos campos precisar."

    else:
        st.markdown("Preencha os dados da sua futura casa:")
        c_pessoas = st.number_input("Quantas pessoas vão morar?", min_value=1, value=3, step=1, key="c_pessoas")
        c_chuveiros = st.number_input("Quantos chuveiros elétricos?", min_value=0, value=1, step=1, key="c_chuveiros")
        c_ar = st.number_input("Quantos aparelhos de ar condicionado?", min_value=0, value=1, step=1, key="c_ar")
        c_freezer = st.number_input("Quantos freezers (além da geladeira)?", min_value=0, value=0, step=1, key="c_freezer")
        c_home_office = st.number_input("Pessoas em home office (uso intenso de PC)?", min_value=0, value=0, step=1, key="c_home_office")
        
        consumo = estimar_consumo_casa_nova(c_pessoas, c_chuveiros, c_ar, c_freezer, c_home_office)
        st.info(f"Seu consumo estimado é de **{consumo} kWh/mês**.")

        # MUDANÇA: Texto de ajuda para quem NÃO TEM conta
        help_texto_tarifa = "Como você ainda não tem uma conta, usamos um valor padrão (R$ 0,85). Você pode pesquisar a tarifa residencial média da Enel Rio das Ostras e alterar este valor para uma simulação mais precisa."


    # --- CAMPO DE TARIFA ITERATIVO (COM AJUDA DINÂMICA) ---
    st.markdown("**Tarifa de Energia (R$/kWh):**")

    # Loop para exibir os campos de tarifa existentes
    for i in range(len(st.session_state.tarifas_list)):
        
        help_tarifa_final = None
        if i == 0: # Adiciona o help SÓ no primeiro campo
            
            # MUDANÇA: O texto de ajuda agora é dinâmico
            help_tarifa_final = f"""
            {help_texto_tarifa}
            
            **Exemplo de onde encontrar (se tiver conta):**
            
            ![Exemplo Conta de Luz](https://raw.githubusercontent.com/felipaofelipao/solar-sim-app/refs/heads/main/Imagem%20do%20WhatsApp%20de%202025-11-09%20%C3%A0(s)%2017.36.05_00537b91.JPG)
            """
        
        st.session_state.tarifas_list[i] = st.number_input(
            f"Valor {i+1} (TE ou TUSD)", 
            min_value=0.00, 
            max_value=3.00,
            value=st.session_state.tarifas_list[i], 
            step=0.01, 
            format="%.2f", 
            key=f"tarifa_input_{i}",
            help=help_tarifa_final # O 'help' agora é dinâmico
        )
    
    if st.button("Adicionar outro valor (+)", key="add_tarifa"):
        st.session_state.tarifas_list.append(0.0)

    tarifa_calculada = sum(st.session_state.tarifas_list)
    st.info(f"Sua Tarifa Total: **{formatar_reais(tarifa_calculada)} / kWh**")


with col2:
    st.subheader("3️⃣ Sua Localização")
    cidades_ordenadas = sorted(HSP_CAPITAIS.keys())
        
    cidade_selecionada = st.selectbox(
        "Localização da Simulação:", 
        cidades_ordenadas,
        index=0, 
        key="cidade",
        disabled=True
    )

    st.markdown("---") 
    st.subheader("Tipo de Conexão (Enel)")
    tipo_conexao = st.selectbox(
        "Qual sua conexão com a rede?",
        ("Monofásica (Taxa Mínima 30 kWh)", 
         "Bifásica (Taxa Mínima 50 kWh)", 
         "Trifásica (Taxa Mínima 100 kWh)"),
        index=1, # Padrão para Bifásica
        key="tipo_conexao",
        help="Isso define a taxa mínima (custo de disponibilidade) que você sempre pagará, mesmo gerando 100% da sua energia."
    )

# Cálculo temporário
hsp = HSP_CAPITAIS[cidade_selecionada]
custo_wp = CUSTO_WP_CAPITAIS[cidade_selecionada]
resultados_tmp = calcular_sistema_solar(consumo, tarifa_calculada, hsp, custo_wp) 

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
    
    if st.session_state.modo_simulacao == "Com base na minha conta de luz (Já moro no local)":
        consumo_atual = st.session_state.consumo
    else:
        consumo_atual = estimar_consumo_casa_nova(
            st.session_state.c_pessoas, 
            st.session_state.c_chuveiros, 
            st.session_state.c_ar,
            st.session_state.c_freezer,
            st.session_state.c_home_office
        )
        
    tarifa_atual = sum(st.session_state.tarifas_list)
    
    cidade_atual = st.session_state.cidade
    hsp_atual = HSP_CAPITAIS[cidade_atual]
    custo_wp_atual = CUSTO_WP_CAPITAIS[cidade_atual]
    escolha_atual = st.session_state.escolha_orc
    
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
            custo_final_atual, custo_wp_atual, consumo_atual, tarifa_atual, hsp_atual
        )
    else:
        dados_finais = calcular_sistema_solar(
            consumo_atual, tarifa_atual, hsp_atual, custo_wp_atual
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
        "saldo_kwh": saldo_kwh_final
    }

# 4) Mostrar resultados
if "res" in st.session_state:
    R = st.session_state.res
    dados = R["dados"]

    st.divider()
    st.subheader(f"✅ Resultados da Simulação — {R['cidade']}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Investimento Total Considerado", formatar_reais(R["custo_final"]))
        st.markdown("**Estimativa de Custos:**")
        for item, valor in dados["custos_detalhados"].items():
            st.markdown(f"**- {item}:** {formatar_reais(valor)}")
    
    with c2:
        st.metric("Potência do Sistema (Painéis)", f"{dados['potencia_kwp']} kWp")
        st.metric(
            "Inversor Recomendado (Tamanho CA)", 
            f"~ {dados['inversor_kw_recomendado']} kW",
            help="Este é o tamanho nominal (em CA) do inversor, considerando um 'oversizing' padrão de 125% da potência dos painéis (em CC)."
        )
        st.metric("Quantidade de Painéis", f"{dados['numero_paineis']}")
        st.metric("Área Mínima Necessária", f"{dados['area_m2']} m²")

    with c3:
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
            st.metric("Nova Fatura (Taxa Mínima)", formatar_reais(nova_fatura))
            st.metric("Créditos Gerados", f"{creditos_kwh:.0f} kWh / mês")

        st.metric("Retorno do Investimento (Payback)", R["payback"])
        
    st.info(
        """
        #### 💡 Qual Tipo de Inversor Escolher?
        O tamanho acima é uma estimativa da **potência**. Sua maior decisão será o **tipo** de inversor:
        * **1. Inversor de String (ou Central):**
            * **O que é:** Uma única "caixa" que gerencia todos os seus painéis juntos.
            * **Ideal para:** Telhados grandes, sem nenhuma sombra, onde o custo é o principal fator.
        * **2. Microinversor:**
            * **O que é:** Vários aparelhos pequenos instalados no telhado, um para cada painel (ou para cada 2 a 4 painéis).
            * **Ideal para:** Telhados com sombras parciais (de árvores, chaminés, etc.) ou telhados com várias "águas" (diferentes orientações).
        """
    )

    st.success(f"🌳 *Benefício Ambiental:* Este sistema evita cerca de *{dados['co2_evitado_kg']} kg de CO₂/ano* — o equivalente a *{dados['co2_evitado_kg']/150:.1f} árvores!*")

    st.subheader("📈 Comparativo Mensal: Consumo x Geração") 

    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    fator_sazonal_correto = [1.118, 1.223, 1.052, 1.014, 0.912, 0.890, 0.881, 1.014, 0.960, 0.984, 0.918, 1.042]
    
    geracao_mensal = [dados["geracao_mensal"] * f for f in fator_sazonal_correto]

    domain_ = ["Consumo (kWh)", "Geração Solar (kWh)"]
    range_ = ["#FF4B4B", "#0068C9"] 

    df = pd.DataFrame({
        "Mês": meses,
        "Consumo (kWh)": [R["consumo"]]*12,
        "Geração Solar (kWh)": geracao_mensal
    }).melt("Mês", var_name="Categoria", value_name="Energia (kWh)")
    
    grafico = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Mês", sort=meses),
        y=alt.Y("Energia (kWh)", title="Energia Mensal (kWh)"),
        color=alt.Color("Categoria", scale=alt.Scale(domain=domain_, range=range_)),
        tooltip=["Mês","Categoria","Energia (kWh)"]
    ).properties(height=350, title="📊 Comparativo Mensal: Consumo x Geração Solar").interactive()

    st.altair_chart(grafico, use_container_width=True)

    st.info("💡 **Dica:** A sua geração de energia pode ser maior que o seu consumo! Isso gera créditos de energia que podem ser usados em até 60 meses.")

    with st.expander("📘 Premissas e limitações da simulação"):
        st.markdown(f"""
        - *HSP (Horas de Sol Pleno):* média de *{R['hsp']}h/dia* para {R['cidade']}, baseada em dados do CRESESB/SWERA.    
        - *Taxa de Desempenho (PR):* {int(TAXA_DESEMPENHO*100)}%.    
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

