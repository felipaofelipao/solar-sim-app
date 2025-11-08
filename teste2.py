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
st.set_page_config(page_title="SolarSim | Simulador Solar", page_icon="☀️", layout="wide")

# --- LOCALE (com fallback) ---
try:
    # Tenta configurar o locale para Português do Brasil
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    # Se falhar (comum em servidores/deploy), usa o fallback
    pass


def formatar_reais(valor: float) -> str:
    """Formata um float para o padrão R$ X.XXX,XX com fallback."""
    try:
        # Tenta usar o locale pt_BR
        return locale.currency(valor, grouping=True)
    except:
        # Fallback manual caso o locale falhe
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --- BASES DE DADOS (DICIONÁRIOS) ---
# Foco exclusivo em Rio das Ostras com média de HSP correta
HSP_CAPITAIS = {
    "Rio das Ostras (RJ)": 4.98
}

# Foco exclusivo em Rio das Ostras (usando média do RJ)
CUSTO_WP_CAPITAIS = {
    "Rio das Ostras (RJ)": 2.49
}


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

    # Cálculo do Inversor (Oversizing de 1.25)
    inversor_kw_rec = potencia_kwp_final / 1.25

    geracao_diaria_kwh = potencia_kwp_final * hsp * TAXA_DESEMPENHO
    geracao_mensal_kwh = geracao_diaria_kwh * 30
    custo_total_estimado = potencia_final_sistema_wp * custo_wp_regional
    economia_mensal_reais = min(geracao_mensal_kwh, consumo_kwh) * tarifa
    geracao_anual_kwh = geracao_mensal_kwh * 12
    co2_evitado_anual_kg = geracao_anual_kwh * FATOR_EMISSAO_CO2_KWH

    # Estratificação de Custos
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

    # Cálculo do Inversor
    inversor_kw_rec = potencia_kwp_final / 1.25

    numero_paineis = max(1, round(potencia_final_sistema_wp / POTENCIA_PAINEL_WP))
    area_total_m2 = numero_paineis * AREA_PAINEL_M2

    geracao_diaria_kwh = potencia_kwp_final * hsp * TAXA_DESEMPENHO
    geracao_mensal_kwh = geracao_diaria_kwh * 30
    economia_mensal_reais = min(geracao_mensal_kwh, consumo_kwh) * tarifa
    geracao_anual_kwh = geracao_mensal_kwh * 12
    co2_evitado_anual_kg = geracao_anual_kwh * FATOR_EMISSAO_CO2_KWH

    # Estratificação de Custos
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


def estimar_consumo_casa_nova(pessoas, chuveiros, ar_cond):
    """Estima o consumo para uma casa nova (simulação)."""
    consumo_base_pessoas = pessoas * 60
    consumo_chuveiros = chuveiros * 70
    consumo_ar = ar_cond * 100
    return consumo_base_pessoas + consumo_chuveiros + consumo_ar


def formatar_payback(custo, economia_mensal):
    """Calcula e formata o payback em anos e meses."""
    if economia_mensal > 0:
        payback_anos = custo / (economia_mensal * 12)
    else:
        return "Não aplicável"
    anos = int(payback_anos)
    meses = round((payback_anos - anos) * 12)
    if meses == 12:  # Arredonda 11.5+ meses para 1 ano
        anos += 1
        meses = 0
    return f"~ {anos} anos e {meses} meses" if anos else f"~ {meses} meses"


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

    # Lógica condicional para consumo (Conta vs. Estimativa)
    if modo_simulacao == "Com base na minha conta de luz (Já moro no local)":
        consumo = st.number_input(
            "Consumo médio mensal (kWh):",
            min_value=50, max_value=10000, value=300, step=10, key="consumo",
            help="Abra sua conta de luz (Ex: Enel) e procure pelo campo 'Consumo Faturado em kWh' ou 'Total Consumo Mês'."
        )
    else:
        st.markdown("Preencha os dados da sua futura casa:")
        c_pessoas = st.number_input("Quantas pessoas vão morar?", min_value=1, value=3, step=1, key="c_pessoas")
        c_chuveiros = st.number_input("Quantos chuveiros elétricos?", min_value=0, value=1, step=1, key="c_chuveiros")
        c_ar = st.number_input("Quantos aparelhos de ar condicionado?", min_value=0, value=1, step=1, key="c_ar")

        # Calcula o consumo estimado e o armazena
        consumo = estimar_consumo_casa_nova(c_pessoas, c_chuveiros, c_ar)
        st.info(f"Seu consumo estimado é de **{consumo} kWh/mês**.")

    # Tooltip (help) na tarifa
    tarifa = st.number_input(
        "Tarifa de energia (R$/kWh):",
        min_value=0.30, max_value=1.50, value=0.85, step=0.01, format="%.2f", key="tarifa",
        help="Some os valores da 'Tarifa de Energia (TE)' e da 'Tarifa de Uso (TUSD)' da sua conta. Ex: (TE 0,45 + TUSD 0,40 = 0,85)"
    )

with col2:
    st.subheader("3️⃣ Sua Localização")
    # Selectbox desabilitado com opção única
    cidades_ordenadas = sorted(HSP_CAPITAIS.keys())

    cidade_selecionada = st.selectbox(
        "Localização da Simulação:",
        cidades_ordenadas,
        index=0,  # Só tem um item, então o índice é 0
        key="cidade",
        disabled=True  # Desabilita a caixa
    )

    # --- NOVO BLOCO: TIPO DE CONEXÃO ---
    st.markdown("---")  # Divisor
    st.subheader("Tipo de Conexão (Enel)")
    tipo_conexao = st.selectbox(
        "Qual sua conexão com a rede?",
        ("Bifásica (Taxa Mínima 50 kWh)",
         "Monofásica (Taxa Mínima 30 kWh)",
         "Trifásica (Taxa Mínima 100 kWh)"),
        index=0,  # Padrão para Bifásica
        key="tipo_conexao",
        help="Isso define a taxa mínima (custo de disponibilidade) que você sempre pagará, mesmo gerando 100% da sua energia."
    )

# Cálculo temporário para estimativa de orçamento
hsp = HSP_CAPITAIS[cidade_selecionada]
custo_wp = CUSTO_WP_CAPITAIS[cidade_selecionada]
resultados_tmp = calcular_sistema_solar(consumo, tarifa, hsp, custo_wp)

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

# 3) Botão Calcular (Salva em Session State)
if st.button("⚡ Simular meu sistema solar", type="primary", use_container_width=True):

    # Busca os valores atuais dos inputs
    if st.session_state.modo_simulacao == "Com base na minha conta de luz (Já moro no local)":
        consumo_atual = st.session_state.consumo
    else:
        consumo_atual = estimar_consumo_casa_nova(
            st.session_state.c_pessoas,
            st.session_state.c_chuveiros,
            st.session_state.c_ar
        )

    tarifa_atual = st.session_state.tarifa
    cidade_atual = st.session_state.cidade
    hsp_atual = HSP_CAPITAIS[cidade_atual]
    custo_wp_atual = CUSTO_WP_CAPITAIS[cidade_atual]
    escolha_atual = st.session_state.escolha_orc

    # --- NOVO: Lógica da Taxa Mínima ---
    conexao_atual = st.session_state.tipo_conexao
    if "Monofásica" in conexao_atual:
        minimo_kwh_atual = 30
    elif "Trifásica" in conexao_atual:
        minimo_kwh_atual = 100
    else:
        minimo_kwh_atual = 50  # Padrão Bifásica

    # Lógica principal: calcula por consumo ou por orçamento?
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

    # --- NOVO: Cálculo de Saldo e Créditos ---
    saldo_kwh_final = dados_finais["geracao_mensal"] - consumo_atual

    # Salva TUDO no session_state para persistir os resultados
    st.session_state.res = {
        "cidade": cidade_atual,
        "hsp": hsp_atual,
        "consumo": consumo_atual,
        "tarifa": tarifa_atual,
        "custo_final": custo_final_atual,
        "dados": dados_finais,
        "payback": payback_final_str,
        "minimo_kwh": minimo_kwh_atual,  # Salva a taxa mínima
        "saldo_kwh": saldo_kwh_final  # Salva o saldo
    }

# 4) Mostrar resultados (se houver dados na sessão)
if "res" in st.session_state:
    R = st.session_state.res
    dados = R["dados"]

    st.divider()
    st.subheader(f"✅ Resultados da Simulação — {R['cidade']}")

    c1, c2, c3 = st.columns(3)
    # Coluna 1: Investimento e Estratificação
    with c1:
        st.metric("Investimento Total Considerado", formatar_reais(R["custo_final"]))
        st.markdown("**Estimativa de Custos:**")
        for item, valor in dados["custos_detalhados"].items():
            st.text(f"- {item}: {formatar_reais(valor)}")

    # Coluna 2: Detalhes do Sistema
    with c2:
        st.metric("Potência do Sistema (Painéis)", f"{dados['potencia_kwp']} kWp")
        st.metric(
            "Inversor Recomendado (Tamanho CA)",
            f"~ {dados['inversor_kw_recomendado']} kW",
            help="Este é o tamanho nominal (em CA) do inversor, considerando um 'oversizing' padrão de 125% da potência dos painéis (em CC)."
        )
        st.metric("Quantidade de Painéis", f"{dados['numero_paineis']}")
        st.metric("Área Mínima Necessária", f"{dados['area_m2']} m²")

    # Coluna 3: Nova Realidade Financeira (Créditos e Taxa Mínima)
    with c3:
        saldo_kwh = R["saldo_kwh"]
        minimo_kwh = R["minimo_kwh"]
        tarifa = R["tarifa"]

        if saldo_kwh < 0:
            # Caso 1: Geração MENOR que o consumo (Under-budget)
            consumo_rede_kwh = abs(saldo_kwh)
            kwh_a_pagar = max(consumo_rede_kwh, minimo_kwh)
            nova_fatura = kwh_a_pagar * tarifa

            st.metric("Nova Fatura Mensal Estimada", formatar_reais(nova_fatura))
            st.metric("Consumo restante da Rede", f"{consumo_rede_kwh:.0f} kWh / mês")

        else:
            # Caso 2: Geração MAIOR que o consumo (Over-budget)
            creditos_kwh = saldo_kwh
            nova_fatura = minimo_kwh * tarifa  # Pagará apenas a taxa mínima

            st.metric("Nova Fatura (Taxa Mínima)", formatar_reais(nova_fatura))
            st.metric("Créditos Gerados", f"{creditos_kwh:.0f} kWh / mês")

        st.metric("Retorno do Investimento (Payback)", R["payback"])

    # Bloco de Explicação do Inversor
    st.info(
        """
        #### 💡 Qual Tipo de Inversor Escolher?

        O tamanho acima é uma estimativa da **potência**. Sua maior decisão será o **tipo** de inversor:

        * **1. Inversor de String (ou Central):**
            * **O que é:** Uma única "caixa" que gerencia todos os seus painéis juntos.
            * **Ideal para:** Telhados grandes, sem nenhuma sombra, onde o custo é o principal fator. Se uma sombra atingir um painel, pode prejudicar a geração de todos os painéis ligados a ele.

        * **2. Microinversor:**
            * **O que é:** Vários aparelhos pequenos instalados no telhado, um para cada painel (ou para cada 2 a 4 painéis).
            * **Ideal para:** Telhados com sombras parciais (de árvores, chaminés, etc.), telhados com várias "águas" (diferentes orientações) ou para quem deseja monitorar cada painel individualmente.

        **Converse com seu instalador sobre qual tipo é melhor para o seu telhado!**
        """
    )

    st.success(
        f"🌳 *Benefício Ambiental:* Este sistema evita cerca de *{dados['co2_evitado_kg']} kg de CO₂/ano* — o equivalente a *{dados['co2_evitado_kg'] / 150:.1f} árvores!*")

    # ----- Gráficos -----
    st.subheader("📈 Visualização dos Resultados")
    modo_grafico = st.radio("Escolha o tipo de gráfico:", ["Mensal", "Anual"], horizontal=True, key="modo_grafico")

    # Fator Sazonal CORRIGIDO (Baseado nos dados de 4.98)
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    fator_sazonal_correto = [1.118, 1.223, 1.052, 1.014, 0.912, 0.890, 0.881, 1.014, 0.960, 0.984, 0.918, 1.042]

    geracao_mensal = [dados["geracao_mensal"] * f for f in fator_sazonal_correto]

    # Cores para Daltônicos (Alto Contraste)
    domain_ = ["Consumo (kWh)", "Geração Solar (kWh)"]
    range_ = ["#FF4B4B", "#0068C9"]  # Vermelho e Azul

    if modo_grafico == "Mensal":
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
        ).properties(height=350, title="📊 Comparativo Mensal: Consumo x Geração Solar").interactive()
    else:
        df_anual = pd.DataFrame({
            "Categoria": ["Consumo Anual", "Geração Solar Anual"],
            "Energia (kWh/ano)": [R["consumo"] * 12, sum(geracao_mensal)]
        })
        # --- CORREÇÃO DO BUG DO GRÁFICO ANUAL ---
        # Corrigido o `alt.Y` e o `tooltip` para usar o nome exato da coluna.
        grafico = alt.Chart(df_anual).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x="Categoria",
            y=alt.Y("Energia (kWh/ano)", title="Energia Anual (kWh)"),
            color=alt.Color("Categoria",
                            scale=alt.Scale(domain=["Consumo Anual", "Geração Solar Anual"], range=range_)),
            tooltip=["Categoria", "Energia (kWh/ano)"]
        ).properties(height=350, title="📊 Comparativo Anual: Consumo x Geração Solar").interactive()

    st.altair_chart(grafico, use_container_width=True)

    st.info(
        "💡 **Dica:** A sua geração de energia pode ser maior que o seu consumo! Isso gera créditos de energia que podem ser usados em até 60 meses.")

    # ----- Expanders de Informações Adicionais -----
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

        st.markdown("---")

        st.markdown("#### Como funcionam as Tarifas (Ex: Enel)?")
        st.markdown(
            """
            Sua conta de luz não é um valor único. Ela é composta por duas tarifas principais:

            * **TE (Tarifa de Energia):** O custo da energia elétrica que você de fato consumiu.
            * **TUSD (Tarifa de Uso do Sistema de Distribuição):** O custo para "transportar" essa energia até sua casa (uso dos postes, fios, etc.).

            Para o cálculo da **economia** com energia solar, consideramos a soma dessas duas, pois o sistema fotovoltaico gera créditos que abatem ambas as faturas.

            **Cuidado:** Você sempre pagará a **Taxa Mínima** (ou "custo de disponibilidade"), que é uma taxa para estar conectado à rede, mesmo que sua geração seja maior que o consumo. Nosso simulador não considera essa taxa mínima no cálculo da economia.
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
