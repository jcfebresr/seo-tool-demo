import streamlit as st
import pandas as pd

# Configuración
st.set_page_config(
    page_title="SEO Categorization Tool",
    page_icon="🎯",
    layout="wide"
)

# Título
st.title("🎯 SEO Categorization Tool")
st.markdown("Categorización automática de URLs por estructura")
st.divider()

# Función de categorización
def categorize_url(url):
    url_lower = url.lower().strip()
    path = url_lower.split('/')[-1] if '/' in url_lower else url_lower
    
    if not path or url_lower.endswith('/'):
        return "Homepage"
    elif 'shop' in url_lower or 'product' in url_lower or 'item' in url_lower:
        return "Producto"
    elif 'blog' in url_lower or 'post' in url_lower or 'article' in url_lower:
        return "Blog"
    elif 'marca' in url_lower or 'brand' in url_lower:
        return "Marca"
    elif 'contact' in url_lower or 'contacto' in url_lower:
        return "Contacto"
    elif 'about' in url_lower or 'nosotros' in url_lower:
        return "Nosotros"
    elif 'category' in url_lower or 'categoria' in url_lower:
        return "Categoria"
    else:
        return "Otros"

# Upload
uploaded_file = st.file_uploader("📤 Sube tu CSV de URLs", type="csv")

if uploaded_file:
    # Leer CSV
    df = pd.read_csv(uploaded_file)
    
    # Validar columna URL
    if 'URL' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'URL'}, inplace=True)
    
    # Categorizar
    if st.button("🚀 Categorizar URLs", type="primary"):
        with st.spinner("Procesando..."):
            df['Categoría'] = df['URL'].apply(categorize_url)
        
        st.success(f"✅ {len(df)} URLs categorizadas!")
        
        # Mostrar resultados
        st.subheader("📊 Resultados")
        st.dataframe(df, use_container_width=True)
        
        # Resumen
        st.subheader("📈 Resumen")
        category_counts = df['Categoría'].value_counts()
        st.bar_chart(category_counts)
        
        # Descargar
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar CSV Categorizado",
            csv,
            "urls_categorizadas.csv",
            "text/csv"
        )
else:
    st.info("👆 Sube un CSV con URLs para comenzar")

st.divider()
st.caption("🎯 SEO Tool | Made with Streamlit")