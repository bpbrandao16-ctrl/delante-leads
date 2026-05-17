
import re
import hashlib
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st

# =====================================================
# CONFIGURAÇÃO
# =====================================================
st.set_page_config(
    page_title="Delanté Leads",
    page_icon="📍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

DATA_PATH = Path("leads_base.xlsx")
FEEDBACK_PATH = Path("feedback_vendedores.csv")

STATUS_OPTIONS = [
    "Novo",
    "Visitado",
    "Interessado",
    "Sem potencial",
    "Cliente aberto",
    "Retornar depois",
    "Não encontrado",
]

POTENCIAL_OPTIONS = [
    "",
    "Alto",
    "Médio",
    "Baixo",
    "Sem aderência",
]

# =====================================================
# ESTILO MOBILE-FIRST
# =====================================================
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
        max-width: 760px;
    }
    .lead-card {
        border: 1px solid #e6e6e6;
        border-radius: 18px;
        padding: 14px 14px 10px 14px;
        margin-bottom: 14px;
        background: #ffffff;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05);
    }
    .lead-name {
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: 4px;
    }
    .lead-meta {
        color: #555;
        font-size: 0.88rem;
        line-height: 1.25rem;
    }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        background: #f2f2f2;
        font-size: 0.78rem;
        margin-right: 4px;
        margin-top: 4px;
    }
    .kpi {
        border-radius: 16px;
        background: #f7f7f7;
        padding: 12px;
        text-align: center;
    }
    .kpi-number {
        font-size: 1.35rem;
        font-weight: 800;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# FUNÇÕES
# =====================================================
def clean_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

def only_digits(x):
    return re.sub(r"\D", "", clean_text(x))

def make_lead_id(row):
    raw = f"{clean_text(row.get('nome'))}|{clean_text(row.get('endereco_formatado'))}|{clean_text(row.get('cidade_busca'))}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]

@st.cache_data(show_spinner=False)
def load_base(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
    elif DATA_PATH.exists():
        df = pd.read_excel(DATA_PATH)
    else:
        return pd.DataFrame()

    # Garante colunas esperadas
    expected = [
        "nome", "tipologia_busca", "cidade_busca", "endereco_formatado",
        "bairro", "cidade", "estado", "cep", "telefone", "website",
        "maps_url", "rating", "total_avaliacoes", "lat", "lng", "place_id"
    ]
    for col in expected:
        if col not in df.columns:
            df[col] = ""

    df["lead_id"] = df.apply(make_lead_id, axis=1)
    df["telefone_limpo"] = df["telefone"].apply(only_digits)
    df["whatsapp_url"] = df["telefone_limpo"].apply(
        lambda x: f"https://wa.me/55{x}" if x else ""
    )
    df["tel_url"] = df["telefone_limpo"].apply(
        lambda x: f"tel:{x}" if x else ""
    )

    # Limpeza de campos
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df

def load_feedback():
    if FEEDBACK_PATH.exists():
        fb = pd.read_csv(FEEDBACK_PATH, dtype=str).fillna("")
        return fb
    return pd.DataFrame(columns=[
        "lead_id", "status", "potencial_percebido", "observacao_vendedor",
        "proxima_acao", "vendedor", "data_ultima_visita", "updated_at"
    ])

def save_feedback_row(row):
    fb = load_feedback()

    # remove feedback anterior do mesmo lead
    fb = fb[fb["lead_id"] != row["lead_id"]]

    fb = pd.concat([fb, pd.DataFrame([row])], ignore_index=True)
    fb.to_csv(FEEDBACK_PATH, index=False, encoding="utf-8-sig")

def get_feedback_for_lead(fb, lead_id):
    if fb.empty:
        return {}
    r = fb[fb["lead_id"] == lead_id]
    if r.empty:
        return {}
    return r.iloc[-1].to_dict()

def merge_feedback(df, fb):
    if fb.empty:
        df["status_salvo"] = "Novo"
        df["potencial_salvo"] = ""
        df["observacao_salva"] = ""
        df["proxima_acao_salva"] = ""
        df["vendedor_salvo"] = ""
        df["data_ultima_visita_salva"] = ""
        return df

    last_fb = fb.drop_duplicates(subset=["lead_id"], keep="last")
    merged = df.merge(last_fb, on="lead_id", how="left")
    merged["status_salvo"] = merged["status"].fillna("Novo")
    merged["potencial_salvo"] = merged["potencial_percebido"].fillna("")
    merged["observacao_salva"] = merged["observacao_vendedor"].fillna("")
    merged["proxima_acao_salva"] = merged["proxima_acao"].fillna("")
    merged["vendedor_salvo"] = merged["vendedor"].fillna("")
    merged["data_ultima_visita_salva"] = merged["data_ultima_visita"].fillna("")
    return merged

def render_link_buttons(row):
    cols = st.columns(3)
    with cols[0]:
        if clean_text(row.get("maps_url")):
            st.link_button("📍 Maps", row["maps_url"], use_container_width=True)
        else:
           st.button(
    "📍 Maps",
    disabled=True,
    use_container_width=True,
    key=f"maps_{row['lead_id']}"
)
    with cols[1]:
        if clean_text(row.get("tel_url")):
            st.link_button("📞 Ligar", row["tel_url"], use_container_width=True)
        else:
           st.button(
    "📞 Ligar",
    disabled=True,
    use_container_width=True,
    key=f"ligar_{row['lead_id']}")
    with cols[2]:
        if clean_text(row.get("whatsapp_url")):
            st.link_button("💬 WhatsApp", row["whatsapp_url"], use_container_width=True)
        st.button(
    "💬 WhatsApp",
    disabled=True,
    use_container_width=True,
    key=f"whats_{row['lead_id']}")

# =====================================================
# APP
# =====================================================
st.title("📍 Delanté Leads")
st.caption("Consulta simples de leads B2B para o time comercial")

with st.expander("📤 Atualizar base de leads", expanded=False):
    uploaded_file = st.file_uploader(
        "Subir nova base Excel",
        type=["xlsx"],
        help="Use a base gerada pelo Google Maps ou pela consolidação de leads."
    )

df_base = load_base(uploaded_file)
fb = load_feedback()

if df_base.empty:
    st.warning("Nenhuma base encontrada. Suba um arquivo Excel para começar.")
    st.stop()

df = merge_feedback(df_base, fb)

# =====================================================
# FILTROS
# =====================================================
st.subheader("Buscar leads")

cidades = sorted([x for x in df["cidade_busca"].dropna().unique() if x])
tipologias = sorted([x for x in df["tipologia_busca"].dropna().unique() if x])
bairros = sorted([x for x in df["bairro"].dropna().unique() if x])
status_list = sorted([x for x in df["status_salvo"].dropna().unique() if x])

col1, col2 = st.columns(2)
with col1:
    cidade_sel = st.selectbox("Cidade", ["Todas"] + cidades)
with col2:
    tipo_sel = st.selectbox("Tipologia", ["Todas"] + tipologias)

col3, col4 = st.columns(2)
with col3:
    status_sel = st.selectbox("Status", ["Todos"] + status_list)
with col4:
    bairro_sel = st.selectbox("Bairro", ["Todos"] + bairros)

busca = st.text_input("Buscar por nome ou endereço", placeholder="Ex.: açougue, centro, mercado...")

filtered = df.copy()

if cidade_sel != "Todas":
    filtered = filtered[filtered["cidade_busca"] == cidade_sel]
if tipo_sel != "Todas":
    filtered = filtered[filtered["tipologia_busca"] == tipo_sel]
if status_sel != "Todos":
    filtered = filtered[filtered["status_salvo"] == status_sel]
if bairro_sel != "Todos":
    filtered = filtered[filtered["bairro"] == bairro_sel]
if busca:
    b = busca.lower().strip()
    filtered = filtered[
        filtered["nome"].str.lower().str.contains(b, na=False) |
        filtered["endereco_formatado"].str.lower().str.contains(b, na=False) |
        filtered["bairro"].str.lower().str.contains(b, na=False)
    ]

# =====================================================
# KPIs
# =====================================================
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"""<div class="kpi"><div class="kpi-number">{len(filtered)}</div><div class="kpi-label">Leads</div></div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi"><div class="kpi-number">{filtered['telefone_limpo'].ne('').sum()}</div><div class="kpi-label">Com telefone</div></div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi"><div class="kpi-number">{filtered['status_salvo'].eq('Interessado').sum()}</div><div class="kpi-label">Interessados</div></div>""", unsafe_allow_html=True)

st.divider()

# =====================================================
# LISTA DE LEADS
# =====================================================
st.subheader("Leads encontrados")

MAX_SHOW = 80
if len(filtered) > MAX_SHOW:
    st.info(f"Mostrando os primeiros {MAX_SHOW} leads. Use filtros para refinar.")
show_df = filtered.head(MAX_SHOW)

for _, row in show_df.iterrows():
    with st.container():
        st.markdown('<div class="lead-card">', unsafe_allow_html=True)

        rating = clean_text(row.get("rating"))
        aval = clean_text(row.get("total_avaliacoes"))
        rating_text = f"⭐ {rating}" if rating else ""
        if aval:
            rating_text += f" ({aval})"

        st.markdown(f"""
        <div class="lead-name">{clean_text(row.get("nome"))}</div>
        <div class="lead-meta">
            <span class="badge">{clean_text(row.get("tipologia_busca"))}</span>
            <span class="badge">{clean_text(row.get("cidade_busca"))}</span>
            <span class="badge">{clean_text(row.get("status_salvo"))}</span>
            <br>
            📍 {clean_text(row.get("bairro"))} — {clean_text(row.get("endereco_formatado"))}<br>
            {rating_text}
        </div>
        """, unsafe_allow_html=True)

        render_link_buttons(row)

        with st.expander("Registrar devolutiva"):
            key = row["lead_id"]

            status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(row["status_salvo"]) if row["status_salvo"] in STATUS_OPTIONS else 0,
                key=f"status_{key}"
            )

            potencial = st.selectbox(
                "Potencial percebido",
                POTENCIAL_OPTIONS,
                index=POTENCIAL_OPTIONS.index(row["potencial_salvo"]) if row["potencial_salvo"] in POTENCIAL_OPTIONS else 0,
                key=f"pot_{key}"
            )

            vendedor = st.text_input(
                "Vendedor",
                value=clean_text(row.get("vendedor_salvo")),
                key=f"vend_{key}",
                placeholder="Nome do vendedor"
            )

            obs = st.text_area(
                "Observação / devolutiva",
                value=clean_text(row.get("observacao_salva")),
                key=f"obs_{key}",
                placeholder="Ex.: interessado, já compra de concorrente, pediu retorno..."
            )

            prox = st.text_input(
                "Próxima ação",
                value=clean_text(row.get("proxima_acao_salva")),
                key=f"prox_{key}",
                placeholder="Ex.: retornar terça, enviar tabela, visitar novamente"
            )

            data_visita = st.date_input(
                "Data da visita/contato",
                value=date.today(),
                key=f"data_{key}"
            )

            if st.button("💾 Salvar devolutiva", key=f"save_{key}", use_container_width=True):
                save_feedback_row({
                    "lead_id": key,
                    "status": status,
                    "potencial_percebido": potencial,
                    "observacao_vendedor": obs,
                    "proxima_acao": prox,
                    "vendedor": vendedor,
                    "data_ultima_visita": str(data_visita),
                    "updated_at": datetime.now().isoformat(timespec="seconds")
                })
                st.success("Devolutiva salva.")
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# EXPORTAÇÃO
# =====================================================
st.divider()
st.subheader("Exportar devolutivas")

fb_download = load_feedback()
if fb_download.empty:
    st.caption("Ainda não há devolutivas salvas.")
else:
    st.download_button(
        "⬇️ Baixar devolutivas CSV",
        data=fb_download.to_csv(index=False, encoding="utf-8-sig"),
        file_name="feedback_vendedores.csv",
        mime="text/csv",
        use_container_width=True
    )
