import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from categorizer import (
    categorize_urls_automatic,
    categorize_urls_nlp,
    categorize_urls_manual
)
import google.generativeai as genai

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="SEO Categorization Tool",
    page_icon="🎯",
    layout="wide"
)

# ============================================
# TÍTULO Y DESCRIPCIÓN
# ============================================
st.title("🎯 SEO Competitive Analysis Tool")
st.markdown("""
Herramienta profesional para categorización automática de URLs y análisis competitivo SEO.
Utiliza detección por patrones, NLP con similitud semántica, y generación de reportes con IA.
""")

st.divider()

# ============================================
# SIDEBAR: CONFIGURACIÓN
# ============================================
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Modo de categorización
    mode = st.radio(
        "Modo de Categorización",
        ["Automático (Patrones)", "NLP (IA Semántica)", "Manual"],
        help="Automático: Detecta por estructura de URL. NLP: Usa similitud semántica. Manual: Defines tú las categorías."
    )
    
    # Categorías manuales si se selecciona
    manual_cats = []
    if mode == "Manual":
        st.subheader("Categorías Manuales")
        cat_input = st.text_area(
            "Ingresa categorías (una por línea)",
            "Homepage\nProducto\nMarca\nBlog\nContacto",
            height=150
        )
        manual_cats = [c.strip() for c in cat_input.split('\n') if c.strip()]
    
    st.divider()
    
    # API Key para reportes
    st.subheader("🤖 Generación de Reportes")
    gemini_key = st.text_input(
        "Gemini API Key (opcional)",
        type="password",
        help="Para generar reportes con IA. Obtén tu key gratis en https://makersuite.google.com/app/apikey"
    )
    
    if gemini_key:
        genai.configure(api_key=gemini_key)

# ============================================
# SECCIÓN PRINCIPAL: UPLOAD DE ARCHIVOS
# ============================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("📤 Cliente")
    client_file = st.file_uploader(
        "Sube CSV del cliente",
        type="csv",
        help="CSV con columnas: URL, Keyword (opcional)",
        key="client"
    )

with col2:
    st.subheader("📤 Competidores")
    comp_files = st.file_uploader(
        "Sube CSVs de competidores",
        type="csv",
        accept_multiple_files=True,
        help="Puedes subir hasta 3 competidores",
        key="competitors"
    )

st.divider()

# ============================================
# PROCESAMIENTO
# ============================================
if client_file:
    
    # Botón de análisis
    if st.button("🚀 Analizar URLs", type="primary", use_container_width=True):
        
        with st.spinner("Procesando..."):
            
            # ========================================
            # CLIENTE
            # ========================================
            df_client = pd.read_csv(client_file)
            
            # Validar columnas
            if 'URL' not in df_client.columns and df_client.columns[0]:
                df_client.rename(columns={df_client.columns[0]: 'URL'}, inplace=True)
            
            urls_client = df_client['URL'].dropna().tolist()
            
            # Categorizar según modo
            if mode == "Automático (Patrones)":
                results, master_cats = categorize_urls_automatic(urls_client)
            elif mode == "Manual":
                results = categorize_urls_manual(urls_client, manual_cats)
                master_cats = manual_cats
            else:  # NLP
                with st.spinner("🧠 Cargando modelo NLP... (puede tardar 30 seg la primera vez)"):
                    results, master_cats = categorize_urls_automatic(urls_client)
                    results = categorize_urls_nlp(urls_client, master_cats)
            
            # Agregar categorías al DataFrame
            results_dict = {r['url']: r['category'] for r in results}
            df_client['Categoría'] = df_client['URL'].map(results_dict)
            
            # Contar keywords si existen
            total_kws_client = 0
            if 'Keyword' in df_client.columns or (len(df_client.columns) > 1 and df_client.columns[1]):
                kw_col = 'Keyword' if 'Keyword' in df_client.columns else df_client.columns[1]
                df_client.rename(columns={kw_col: 'Keyword'}, inplace=True)
                
                for kws in df_client['Keyword'].dropna():
                    if pd.notna(kws) and str(kws).strip():
                        total_kws_client += len(str(kws).split(','))
            
            # ========================================
            # COMPETIDORES
            # ========================================
            comp_results = []
            
            if comp_files:
                for i, comp_file in enumerate(comp_files[:3]):
                    df_comp = pd.read_csv(comp_file)
                    
                    if 'URL' not in df_comp.columns and df_comp.columns[0]:
                        df_comp.rename(columns={df_comp.columns[0]: 'URL'}, inplace=True)
                    
                    urls_comp = df_comp['URL'].dropna().tolist()
                    
                    # Categorizar con las mismas categorías maestras
                    if mode == "NLP (IA Semántica)":
                        comp_cats = categorize_urls_nlp(urls_comp, master_cats)
                    elif mode == "Manual":
                        comp_cats = categorize_urls_manual(urls_comp, manual_cats)
                    else:
                        comp_cats, _ = categorize_urls_automatic(urls_comp)
                    
                    results_dict = {r['url']: r['category'] for r in comp_cats}
                    df_comp['Categoría'] = df_comp['URL'].map(results_dict)
                    
                    # Contar keywords
                    total_kws_comp = 0
                    if len(df_comp.columns) > 1:
                        kw_col = 'Keyword' if 'Keyword' in df_comp.columns else df_comp.columns[1]
                        df_comp.rename(columns={kw_col: 'Keyword'}, inplace=True)
                        
                        for kws in df_comp['Keyword'].dropna():
                            if pd.notna(kws) and str(kws).strip():
                                total_kws_comp += len(str(kws).split(','))
                    
                    comp_results.append({
                        'name': f'Competidor {i+1}',
                        'df': df_comp,
                        'total_kws': total_kws_comp
                    })
        
        # ========================================
        # MOSTRAR RESULTADOS
        # ========================================
        st.success("✅ Análisis completado!")
        
        # MÉTRICAS GENERALES
        st.header("📊 Resumen General")
        
        metrics_cols = st.columns(len(comp_results) + 1)
        
        with metrics_cols[0]:
            st.metric("Cliente - URLs", len(df_client))
            st.metric("Cliente - Keywords", total_kws_client)
            st.metric("Categorías", len(master_cats))
        
        for i, comp in enumerate(comp_results):
            with metrics_cols[i + 1]:
                st.metric(f"{comp['name']} - URLs", len(comp['df']))
                st.metric(f"{comp['name']} - KWs", comp['total_kws'])
        
        st.divider()
        
        # GRÁFICOS
        st.header("📈 Distribución por Categorías")
        
        # Cliente
        cat_counts_client = df_client['Categoría'].value_counts()
        
        fig_client = px.bar(
            x=cat_counts_client.index,
            y=cat_counts_client.values,
            title="Cliente - Distribución",
            labels={'x': 'Categoría', 'y': 'Cantidad de URLs'},
            color=cat_counts_client.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_client, use_container_width=True)
        
        # Comparación con competidores
        if comp_results:
            comparison_data = {
                'Categoría': [],
                'Cliente': [],
            }
            
            for comp in comp_results:
                comparison_data[comp['name']] = []
            
            all_categories = set(cat_counts_client.index)
            for comp in comp_results:
                all_categories.update(comp['df']['Categoría'].value_counts().index)
            
            for cat in sorted(all_categories):
                comparison_data['Categoría'].append(cat)
                comparison_data['Cliente'].append(cat_counts_client.get(cat, 0))
                
                for comp in comp_results:
                    comp_counts = comp['df']['Categoría'].value_counts()
                    comparison_data[comp['name']].append(comp_counts.get(cat, 0))
            
            df_comparison = pd.DataFrame(comparison_data)
            
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Bar(
                name='Cliente',
                x=df_comparison['Categoría'],
                y=df_comparison['Cliente'],
                marker_color='#4285f4'
            ))
            
            colors = ['#ea4335', '#fbbc04', '#34a853']
            for i, comp in enumerate(comp_results):
                fig_comp.add_trace(go.Bar(
                    name=comp['name'],
                    x=df_comparison['Categoría'],
                    y=df_comparison[comp['name']],
                    marker_color=colors[i % 3]
                ))
            
            fig_comp.update_layout(
                title='Comparación Cliente vs Competidores',
                barmode='group',
                xaxis_title='Categoría',
                yaxis_title='Cantidad de URLs'
            )
            
            st.plotly_chart(fig_comp, use_container_width=True)
        
        st.divider()
        
        # TABLAS DE RESULTADOS
        st.header("📋 Resultados Detallados")
        
        tab_names = ["Cliente"] + [comp['name'] for comp in comp_results]
        tabs = st.tabs(tab_names)
        
        with tabs[0]:
            st.dataframe(df_client, use_container_width=True)
            csv_client = df_client.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Descargar CSV Cliente",
                csv_client,
                "cliente_categorizado.csv",
                "text/csv"
            )
        
        for i, comp in enumerate(comp_results):
            with tabs[i + 1]:
                st.dataframe(comp['df'], use_container_width=True)
                csv_comp = comp['df'].to_csv(index=False).encode('utf-8')
                st.download_button(
                    f"📥 Descargar CSV {comp['name']}",
                    csv_comp,
                    f"{comp['name'].lower().replace(' ', '_')}_categorizado.csv",
                    "text/csv",
                    key=f"download_comp_{i}"
                )
        
        st.divider()
        
        # GENERACIÓN DE REPORTE CON IA
        if gemini_key:
            st.header("🤖 Reporte con IA")
            
            if st.button("📄 Generar Reporte Estratégico"):
                with st.spinner("Generando reporte... (30-40 seg)"):
                    
                    # Preparar datos para el prompt
                    comp_data_str = ""
                    for comp in comp_results:
                        comp_counts = comp['df']['Categoría'].value_counts()
                        comp_total = len(comp['df'])
                        
                        comp_data_str += f"\n{comp['name']}:\n"
                        comp_data_str += f"- Total URLs: {comp_total}\n"
                        comp_data_str += f"- Total Keywords: {comp['total_kws']}\n"
                        comp_data_str += "- Top 5 Categorías:\n"
                        
                        for cat, count in comp_counts.head(5).items():
                            pct = (count / comp_total * 100)
                            comp_data_str += f"  - {cat}: {count} URLs ({pct:.1f}%)\n"
                    
                    client_counts = df_client['Categoría'].value_counts()
                    client_total = len(df_client)
                    
                    prompt = f"""
Eres un analista SEO competitivo experto. Genera un REPORTE ESTRATÉGICO COMPLETO:

CLIENTE:
- Total URLs: {client_total}
- Total Keywords: {total_kws_client}
- Top 5 Categorías:
{chr(10).join([f"  - {cat}: {count} URLs ({count/client_total*100:.1f}%)" for cat, count in client_counts.head(5).items()])}

COMPETIDORES:
{comp_data_str}

FORMATO:

RESUMEN ESTRATÉGICO

[Describe las estrategias de posicionamiento del mercado en 2-3 párrafos]

ANÁLISIS DEL CLIENTE

[Analiza fortalezas, distribución y estrategia del cliente en 2-3 párrafos con datos específicos]

ANÁLISIS DE COMPETIDORES

[Para cada competidor: Traffic Distribution, Content Strategy, Bottom Line]

MARKET GAP Y OPORTUNIDADES

[Identifica gaps específicos y 3-4 recomendaciones accionables]

INSTRUCCIONES:
- Usa porcentajes específicos
- Identifica patrones estratégicos
- Propón recomendaciones concretas
- Lenguaje profesional y directo
"""
                    
                    try:
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        response = model.generate_content(prompt)
                        
                        st.markdown(response.text)
                        
                        # Opción de descargar
                        report_txt = response.text.encode('utf-8')
                        st.download_button(
                            "📥 Descargar Reporte",
                            report_txt,
                            "reporte_seo_competitivo.txt",
                            "text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"Error al generar reporte: {str(e)}")

else:
    st.info("👆 Sube un archivo CSV del cliente para comenzar el análisis")

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🎯 SEO Categorization Tool | Powered by Streamlit & Gemini AI")