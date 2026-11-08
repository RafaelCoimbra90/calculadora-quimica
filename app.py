import streamlit as st
import pandas as pd
import os

# 1. CONFIGURAÇÃO DA PÁGINA DO SITE
st.set_page_config(page_title="Calculadora de Orçamentos", page_icon="🧪", layout="centered")

st.title("🧪 Calculadora de Orçamentos Químicos")
st.write("Selecione os produtos, confira as marcas e monte o preço final:")

# Garanta que sua planilha no GitHub tenha exatamente este mesmo nome:
NOME_ARQUIVO = "TABELA PRODUTOS QUÍMICOS.xlsx"

@st.cache_data
def carregar_e_tratar_dados():
    if not os.path.exists(NOME_ARQUIVO):
        st.error(f"Arquivo '{NOME_ARQUIVO}' não encontrado! Certifique-se de enviá-lo para o GitHub junto com este código.")
        return None
        
    # LÊ A PLANILHA
base_de_dado = pd.read_excel(NOME_ARQUIVO)

# TRATAMENTO DE ZEROS SEGURO PARA TODOS OS FORMATOS DE TEXTO E PREÇO
for coluna in base_de_dado.columns:
    if base_de_dado[coluna].dtype == 'object' or str(base_de_dado[coluna].dtype).startswith('string'):
        base_de_dado[coluna] = base_de_dado[coluna].fillna("")
    else:
        base_de_dado[coluna] = base_de_dado[coluna].fillna(0.0)

    
    df_limpo = base_de_dado.copy()
    
    # FUNÇÃO DE LIMPEZA DE PREÇOS DE TEXTO PARA NÚMERO
    def limpar_e_converter_valor(valor):
        if pd.isna(valor):
            return 0.0
        v_str = str(valor).strip().upper()
        if v_str in ["", "NAN", "-", "NULL", "0"]:
            return 0.0
        v_str = v_str.replace("R$", "").replace(" ", "")
        if "," in v_str and "." in v_str:
            v_str = v_str.replace(".", "")
        v_str = v_str.replace(",", ".")
        try:
            return float(v_str)
        except ValueError:
            return 0.0

    # Aplica a sua limpeza a partir da 3ª coluna
    for coluna in df_limpo.columns[2:]:
        df_limpo[coluna] = df_limpo[coluna].apply(limpar_e_converter_valor)
        
    return df_limpo

# Inicializa os dados limpos
df_limpo = carregar_e_tratar_dados()

if df_limpo is not None:
    colunas_totais = list(df_limpo.columns)
    c_prod = colunas_totais[0]   # 1ª Coluna: Produto
    c_marca = colunas_totais[1]  # 2ª Coluna: Marca

    # Inicializa o carrinho de compras do site se ele não existir
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    # =====================================================================
    # 2. INTERFACE VISUAL DO SITE
    # =====================================================================
    lista_produtos = sorted(list(df_limpo[c_prod].dropna().unique()))
    
    # Menu suspenso do Streamlit
    produto_selecionado = st.selectbox("🧪 Escolha o Produto:", lista_produtos)
    
    # Filtra os dados correspondentes ao produto selecionado
    linhas_filtradas = df_limpo[df_limpo[c_prod] == produto_selecionado]
    
    if not linhas_filtradas.empty:
        linha_produto = linhas_filtradas.iloc[0]
        marca_atual = linha_produto[c_marca]
        
        # Exibe a marca correspondente
        st.info(f"🏭 **Marca do Produto:** {marca_atual}")
        
        # Varre as colunas em busca de valores válidos maiores que zero
        opcoes = []
        for coluna in df_limpo.columns[2:]:
            valor_num = linha_produto[coluna]
            if valor_num > 0:
                texto_exibicao = f"{coluna} — R$ {valor_num:.2f}"
                opcoes.append((texto_exibicao, coluna, valor_num))
                
        if opcoes:
            # Menu de escolha do preço específico
            preco_escolhido_str = st.selectbox(
                "💰 Escolha o Preço:", 
                options=[opt[0] for opt in opcoes]
            )
            # Encontra os dados reais do preço selecionado
            idx_opcao = [opt[0] for opt in opcoes].index(preco_escolhido_str)
            _, nome_coluna, valor_final = opcoes[idx_opcao]
        else:
            st.warning("Nenhum preço maior que zero disponível para este produto.")
            preco_escolhido_str = None

        # Botões de Ação lado a lado
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("➕ Adicionar ao Total", use_container_width=True) and preco_escolhido_str:
                st.session_state.carrinho.append({
                    "Produto": produto_selecionado,
                    "Marca": marca_atual,
                    "Tipo de Preço": nome_coluna,
                    "Valor (R$)": valor_final
                })
                st.toast(f"{produto_selecionado} adicionado!", icon="✅")
                
        with col_btn2:
            if st.button("🗑️ Limpar Tudo", use_container_width=True):
                st.session_state.carrinho = []
                st.rerun()  # CORRIGIDO DE: st.render()

    st.divider()

    # =====================================================================
    # 3. EXIBIÇÃO DO ORÇAMENTO ACUMULADO
    # =====================================================================
    st.subheader("📋 Resumo do Orçamento para o Cliente")
    
    if st.session_state.carrinho:
        df_carrinho = pd.DataFrame(st.session_state.carrinho)
        
        # Formata os preços na tabela visual para ficarem bonitos
        df_visual = df_carrinho.copy()
        df_visual["Valor (R$)"] = df_visual["Valor (R$)"].map("R$ {:.2f}".format)
        
        # Mostra a tabela na tela do site de forma interativa
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
        
        # Faz a soma acumulada em tempo real
        total_acumulado = df_carrinho["Valor (R$)"].sum()
        st.metric(label="💵 VALOR TOTAL DO ORÇAMENTO", value=f"R$ {total_acumulado:.2f}")
    else:
        st.caption("Nenhum item adicionado ao orçamento.")
