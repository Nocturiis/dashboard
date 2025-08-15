import json
import pandas as pd
import streamlit as st
import plotly.express as px
import requests

# --- CONFIG ---
st.set_page_config(page_title="Dashboard Annonces", layout="wide")

# --- Charger les données depuis GitHub ---
URL_JSON = "https://github.com/lma20255/my-site-portfolio/blob/main/data/av.json"

@st.cache_data(ttl=3600)  # Cache pendant 1h
def load_data():
    r = requests.get(URL_JSON)
    r.raise_for_status()
    return pd.DataFrame(json.loads(r.text))

df = load_data()

# --- Nettoyage données ---
df["price_num"] = pd.to_numeric(df["price"].str.replace("€", "").str.replace(",", "").str.extract(r"(\d+)")[0], errors="coerce")
df["mileage_num"] = pd.to_numeric(df["mileage"].str.replace("km", "").str.replace(",", "").str.extract(r"(\d+)")[0], errors="coerce")

# --- Sidebar ---
st.sidebar.title("🔍 Filtres & Tri")

# --- NOUVEAU --- Checkbox "Afficher toutes les annonces"
afficher_toutes = st.sidebar.checkbox("Afficher toutes les annonces (ignorer filtres)", value=False)

# Prix - dynamique selon données
prix_max_data = int(df["price_num"].max(skipna=True)) if not pd.isna(df["price_num"].max(skipna=True)) else 60000
prix_min_input = st.sidebar.number_input("Prix min (€)", min_value=0, max_value=prix_max_data, value=0, step=500)
prix_max_input = st.sidebar.number_input("Prix max (€)", min_value=0, max_value=prix_max_data, value=prix_max_data, step=500)
prix_min, prix_max = st.sidebar.slider("💰 Prix (€)", 0, prix_max_data, (prix_min_input, prix_max_input))

# Note
note_min, note_max = st.sidebar.slider("⭐ Note", 1, 5, (1, 5))

# Année
annees_valides = [int(a) for a in df["year"].dropna().unique() if str(a).isdigit()]
if annees_valides:
    annee_min_input = st.sidebar.number_input("Année min", min_value=min(annees_valides), max_value=max(annees_valides), value=min(annees_valides), step=1)
    annee_max_input = st.sidebar.number_input("Année max", min_value=min(annees_valides), max_value=max(annees_valides), value=max(annees_valides), step=1)
    annee_min, annee_max = st.sidebar.slider("📅 Année", min(annees_valides), max(annees_valides), (annee_min_input, annee_max_input))
else:
    annee_min, annee_max = None, None

# Kilométrage
if df["mileage_num"].notna().any():
    km_min, km_max = int(df["mileage_num"].min(skipna=True)), int(df["mileage_num"].max(skipna=True))
    km_min_input = st.sidebar.number_input("Kilométrage min (km)", min_value=0, max_value=km_max, value=km_min, step=1000)
    km_max_input = st.sidebar.number_input("Kilométrage max (km)", min_value=0, max_value=km_max, value=km_max, step=1000)
    km_slider_min, km_slider_max = st.sidebar.slider("🛣️ Kilométrage", km_min, km_max, (km_min_input, km_max_input))
else:
    km_slider_min, km_slider_max = None, None

# Carburant
carburants = st.sidebar.multiselect("⛽ Carburant", sorted(df["fuel_type"].dropna().unique()))

# Transmission
transmissions = st.sidebar.multiselect("⚙️ Transmission", sorted(df["transmission"].dropna().unique()))

# Type de véhicule
types = st.sidebar.multiselect("🚗 Type", sorted(df["body_type"].dropna().unique()))

# Tri
tri_options = {
    "Prix croissant": ("price_num", True),
    "Prix décroissant": ("price_num", False),
    "Note croissante": ("ai_note", True),
    "Note décroissante": ("ai_note", False),
    "Année plus récente": ("year", False),
    "Année plus ancienne": ("year", True),
    "Kilométrage croissant": ("mileage_num", True),
    "Kilométrage décroissant": ("mileage_num", False),
}
tri_choix = st.sidebar.selectbox("📌 Trier par :", list(tri_options.keys()))

# --- Barre de recherche (toujours active) ---
search_query = st.text_input("", placeholder="🔎 Rechercher...", label_visibility="collapsed")

# --- Filtrage ---
if afficher_toutes:
    df_filtered = df.copy()
else:
    df_filtered = df[
        (df["price_num"].between(prix_min, prix_max, inclusive="both")) &
        (df["ai_note"].between(note_min, note_max, inclusive="both"))
    ]
    if annee_min and annee_max:
        df_filtered = df_filtered[df_filtered["year"].apply(lambda x: str(x).isdigit() and annee_min <= int(x) <= annee_max)]

    if km_slider_min and km_slider_max:
        df_filtered = df_filtered[df_filtered["mileage_num"].between(km_slider_min, km_slider_max, inclusive="both")]

    if carburants:
        df_filtered = df_filtered[df_filtered["fuel_type"].isin(carburants)]

    if transmissions:
        df_filtered = df_filtered[df_filtered["transmission"].isin(transmissions)]

    if types:
        df_filtered = df_filtered[df_filtered["body_type"].isin(types)]

# --- Appliquer le filtre recherche toujours ---
if search_query:
    sq = search_query.lower()
    df_filtered = df_filtered[df_filtered.apply(lambda r: any(
        sq in str(v).lower() for v in [r['title'], r.get('description', ''), r.get('ai_comment', '')]), axis=1)]

# --- Tri ---
sort_col, ascending = tri_options[tri_choix]
df_filtered = df_filtered.sort_values(by=sort_col, ascending=ascending)

# --- Statistiques ---
col1, col2 = st.columns([1, 2])
col1.metric("Nombre total d'annonces", len(df_filtered))
col1.metric("Note moyenne", f"{df_filtered['ai_note'].mean():.2f} / 5")

# --- Diagramme (pie chart) avec dégradé rouge -> vert ---
#colorscale = ["#ef485c", "#f46d43", "#fdae61", "#a6d96a", "#1a9850"]  # Rouge à vert
    #              2          3           4           1           5
colorscale = ["#f46d43", "#fdae61", "#a6d96a", "#ef485c", "#1a9850"]
note_counts = df_filtered['ai_note'].value_counts().sort_index()
fig = px.pie(
    values=note_counts.values,
    names=[f"{n}/5" for n in note_counts.index],
    title="Répartition des notes",
    color_discrete_sequence=colorscale
)
fig.update_layout(height=200, margin=dict(l=0, r=0, t=40, b=0))
col2.plotly_chart(fig, use_container_width=True)

# --- Barre de recherche + titre ---
col_title, col_search = st.columns([2, 2])
with col_title:
    st.markdown("### 📋 Liste des annonces")
with col_search:
    # La recherche est déjà au-dessus et active tout le temps
    pass

# --- Affichage annonces ---
for _, row in df_filtered.iterrows():
    st.markdown(
        f"""
        <div style="border-radius:10px; padding:15px; margin-bottom:15px; background-color:#1c1e1f; color:white;">
            <h4><a href="{row['url']}" target="_blank" style="text-decoration:none; color:#4da6ff;">{row['title']}</a></h4>
            <p>💰 <b>Prix :</b> {row['price']} €</p>
            <p>⭐ <b>Note :</b> {row['ai_note']}/5</p>
            <p>📅 <b>Année :</b> {row['year']}</p>
            <p>📍 <b>Ville :</b> {row['city']}</p>
            <p>🛣️ <b>Kilométrage :</b> {row['mileage']}</p>
            <p>⛽ <b>Carburant :</b> {row['fuel_type']}</p>
            <p>⚙️ <b>Transmission :</b> {row['transmission']}</p>
            <p>🚗 <b>Type :</b> {row['body_type']}</p>
            <p>📝 {row['ai_comment']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
