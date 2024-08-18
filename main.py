import os
import pandas as pd
import streamlit as st
import plotly.express as px

from process_data import process_pdfs  # Solo importamos process_pdfs

def set_metric_in_column(label, value):
    st.metric(label, value)

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Mercadona Data Analysis",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ruta del archivo CSV y del logo
csv_path = "data/mercadata.csv"
logo_path = "images/logo.png"  # Cambia esto a la ubicación de tu archivo de logo

# Mostrar el logo como banner en la parte superior
if os.path.exists(logo_path):
    st.image(logo_path, use_column_width=True)  # Ajusta el ancho del logo según el tamaño de la columna

# Subir archivos PDF
uploaded_files = st.file_uploader("Sube tus archivos PDF", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.success(f"Has subido {len(uploaded_files)} archivo(s) PDF.")
    
    # Procesar los archivos PDF cuando el botón es presionado
    if st.button("Procesar PDFs"):
        try:
            process_pdfs(uploaded_files)
            st.success("Archivos PDF procesados correctamente.")
        except Exception as e:
            st.error(f"Error al procesar los archivos PDF: {e}")
else:
    st.warning("Por favor, sube al menos un archivo PDF para continuar.")

# Barra lateral
with st.sidebar:
    st.title('🛒 Mercadona Data Analysis')
    
    if os.path.exists(csv_path):
        try:
            data = pd.read_csv(csv_path)
            data["fecha"] = pd.to_datetime(data["fecha"], format="%d/%m/%Y %H:%M", dayfirst=True)
            data.set_index("fecha", inplace=True)
            
            month_start_dates = data.index.to_period("M").to_timestamp().drop_duplicates().sort_values()
            selected_month_start = st.selectbox(
                "Selecciona el mes",
                month_start_dates,
                index=0,
                format_func=lambda date: date.strftime('%B %Y')
            )
            selected_month_start = pd.Timestamp(selected_month_start)
            filtered_data_by_month = data[data.index.to_period("M").start_time == selected_month_start]
            
            selected_category = st.selectbox("Selecciona la categoría", data["categoría"].unique())
            filtered_data_by_categories = data[data["categoría"] == selected_category]
        
        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}")
    else:
        st.error(f"Archivo {csv_path} no encontrado. Asegúrate de que `process_data.py` haya sido ejecutado correctamente.")

    st.subheader("Sobre la Aplicación")
    st.write('''
        - Esta aplicación analiza los patrones de gasto en diferentes categorías a lo largo del tiempo.
        - Beta Testing por [Izan](https://www.tiktok.com/@quarto.es/video/7402546595943730464), en desarrollo. ¡Se aceptan sugerencias!
    ''')

# Verificar si el archivo CSV existe y no está vacío
if os.path.exists(csv_path):
    try:
        data = pd.read_csv(csv_path)
        if not data.empty:
            data["fecha"] = pd.to_datetime(data["fecha"], format="%d/%m/%Y %H:%M", dayfirst=True)
            data.set_index("fecha", inplace=True)

            # Métricas relevantes
            total_spent = data["precio"].sum()
            total_purchases = data["identificativo de ticket"].nunique()
            avg_spent_per_purchase = data.groupby("identificativo de ticket")["precio"].sum().mean()
            category_with_highest_spent = data.groupby("categoría")["precio"].sum().idxmax()
            total_items_sold = data['item'].nunique()
            avg_spent_per_month = data["precio"].resample('M').sum().mean()
            total_tickets_per_month = data.groupby(data.index.to_period('M')).size().mean()

            # Crear columnas para las métricas
            st.markdown("### Métricas Generales")
            col1, col2, col3 = st.columns(3)

            with col1:
                set_metric_in_column("Gasto Total", f"€{total_spent:.2f}")
                set_metric_in_column("Gasto Promedio por Compra", f"€{avg_spent_per_purchase:.2f}")
                set_metric_in_column("Número Total de Compras", total_purchases)

            with col2:
                set_metric_in_column("Categoría con Mayor Gasto", category_with_highest_spent)
                set_metric_in_column("Gasto Promedio Mensual", f"€{avg_spent_per_month:.2f}")
                set_metric_in_column("Tickets por Mes", f"{total_tickets_per_month:.2f}")

            with col3:
                set_metric_in_column("Total Gastado en el Mes Seleccionado", f"€{filtered_data_by_month['precio'].sum():.2f}")
                set_metric_in_column("Número de Compras en el Mes Seleccionado", filtered_data_by_month['identificativo de ticket'].nunique())
                set_metric_in_column("Categoría con Mayor Gasto en el Mes Seleccionado", filtered_data_by_month.groupby("categoría")["precio"].sum().idxmax())


            # Separación entre las métricas y los gráficos
            st.markdown("---")

            # Crear una fila con los gráficos principales
            st.markdown("### Visualizaciones")
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                total_price_per_category = data.groupby("categoría")["precio"].sum().reset_index()
                fig_pie = px.pie(total_price_per_category, values='precio', names='categoría', title='Distribución del Gasto por Categoría')
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                monthly_expense = data["precio"].resample('M').sum().reset_index()
                fig_bar = px.bar(monthly_expense, x='fecha', y='precio', labels={'fecha': 'Mes', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_bar, use_container_width=True)

            with col3:
                avg_price_per_category = data.groupby("categoría")["precio"].mean().reset_index().sort_values(by="precio", ascending=False)
                fig_bar_avg = px.bar(avg_price_per_category, x='categoría', y='precio', labels={'precio': 'Precio Medio (€)'})
                st.plotly_chart(fig_bar_avg, use_container_width=True)

            # Separación entre gráficos
            st.markdown("---")

            # Análisis del Gasto en el Tiempo y Top 10 Items
            col1, col2 = st.columns(2)

            with col1:
                daily_expense = data["precio"].resample('D').sum().reset_index()
                fig_line = px.line(daily_expense, x='fecha', y='precio', labels={'fecha': 'Fecha', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_line, use_container_width=True)

            with col2:
                top_items = data.groupby('item')['precio'].sum().nlargest(10).reset_index()
                fig_top_items = px.bar(top_items, x='item', y='precio', labels={'item': 'Item', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_top_items, use_container_width=True)

            # Separación entre gráficos y tablas de datos
            st.markdown("---")

            # Datos Filtrados
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Datos Filtrados por Categorías")
                st.dataframe(filtered_data_by_categories, height=300)

            with col2:
                st.subheader("Datos Filtrados por Mes")
                st.dataframe(filtered_data_by_month, height=300)

        else:
            st.warning("El archivo CSV está vacío. Por favor, asegúrate de que `process_data.py` haya generado datos correctamente.")
    
    except Exception as e:
        st.error(f"Error al leer el archivo CSV: {e}")
else:
    st.error(f"Archivo {csv_path} no encontrado. Asegúrate de que `process_data.py` haya sido ejecutado correctamente.")
