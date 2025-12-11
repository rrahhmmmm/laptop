"""
Sistem Penunjang Keputusan Pemilihan Laptop
Menggunakan Metode SAW (Simple Additive Weighting)

Streamlit Web Application - User Friendly Version
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_processor import load_data, preprocess_data, filter_by_category, get_category_counts
from saw_method import (
    calculate_saw_scores,
    rank_alternatives,
    validate_weights,
    get_default_weights,
    CRITERIA_CONFIG,
    get_criteria_names
)

# Page configuration
st.set_page_config(
    page_title="SPK Pemilihan Laptop - Metode SAW",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Card styling */
    .criteria-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }

    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #eee;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #888;
        margin-top: 0.3rem;
    }

    /* Priority badge */
    .priority-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .priority-high { background: #e8f5e9; color: #2e7d32; }
    .priority-medium { background: #fff3e0; color: #ef6c00; }
    .priority-low { background: #fce4ec; color: #c2185b; }

    /* Data range display */
    .data-range {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        color: #555;
        margin-top: 0.5rem;
    }

    /* Rank badge */
    .rank-1 { background: linear-gradient(135deg, #FFD700, #FFA500); color: white; }
    .rank-2 { background: linear-gradient(135deg, #C0C0C0, #A0A0A0); color: white; }
    .rank-3 { background: linear-gradient(135deg, #CD7F32, #8B4513); color: white; }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Improved button */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }

    /* Selectbox styling */
    .importance-select {
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_preprocess_data():
    """Load and preprocess laptop data with caching."""
    df = load_data('laptop.csv')
    df = preprocess_data(df)
    return df


@st.cache_data
def get_data_statistics(df):
    """Get statistics for each criteria from the data."""
    stats = {
        'price': {
            'min': df['price_numeric'].min(),
            'max': df['price_numeric'].max(),
            'avg': df['price_numeric'].mean()
        },
        'ram': {
            'min': int(df['ram_numeric'].min()),
            'max': int(df['ram_numeric'].max()),
            'options': sorted(df['ram_numeric'].unique())
        },
        'ssd': {
            'min': int(df['ssd_numeric'].min()),
            'max': int(df['ssd_numeric'].max()),
            'options': sorted(df['ssd_numeric'].unique())
        },
        'display': {
            'min': df['display_numeric'].min(),
            'max': df['display_numeric'].max()
        },
        'gpu': {
            'min': int(df['gpu_numeric'].min()),
            'max': int(df['gpu_numeric'].max()),
            'options': sorted(df['gpu_numeric'].unique())
        },
        'rating': {
            'min': df['rating_numeric'].min(),
            'max': df['rating_numeric'].max(),
            'avg': df['rating_numeric'].mean()
        }
    }
    return stats


def importance_to_weight(importance: str) -> float:
    """Convert importance level to weight value."""
    mapping = {
        "Tidak Penting": 0.05,
        "Kurang Penting": 0.10,
        "Cukup Penting": 0.15,
        "Penting": 0.20,
        "Sangat Penting": 0.25
    }
    return mapping.get(importance, 0.15)


def format_price_idr(price):
    """Format price to readable format."""
    if price >= 100000:
        return f"₹{price/1000:.0f}K"
    return f"₹{price:,.0f}"


def main():
    # Header
    st.markdown('<h1 class="main-header">💻 Sistem Rekomendasi Laptop</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Temukan laptop terbaik sesuai kebutuhan Anda menggunakan metode SAW</p>', unsafe_allow_html=True)

    # Load data
    try:
        df = load_and_preprocess_data()
        data_stats = get_data_statistics(df)
    except FileNotFoundError:
        st.error("❌ File laptop.csv tidak ditemukan!")
        return
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return

    # Get category counts
    category_counts = get_category_counts(df)

    # =====================
    # MAIN CONTENT - STEP BY STEP
    # =====================

    # Step 1: Choose Category
    st.markdown("---")
    st.markdown("### 📌 Langkah 1: Pilih Kebutuhan Anda")

    col_cat1, col_cat2, col_cat3, col_cat4 = st.columns(4)

    with col_cat1:
        gaming_selected = st.button(
            f"🎮 Gaming\n({category_counts.get('Gaming', 0)} laptop)",
            use_container_width=True,
            key="cat_gaming"
        )
    with col_cat2:
        office_selected = st.button(
            f"💼 Office\n({category_counts.get('Office', 0)} laptop)",
            use_container_width=True,
            key="cat_office"
        )
    with col_cat3:
        student_selected = st.button(
            f"🎓 Student\n({category_counts.get('Student', 0)} laptop)",
            use_container_width=True,
            key="cat_student"
        )
    with col_cat4:
        all_selected = st.button(
            f"📱 Semua\n({len(df)} laptop)",
            use_container_width=True,
            key="cat_all"
        )

    # Handle category selection
    if gaming_selected:
        st.session_state['selected_category'] = 'Gaming'
    elif office_selected:
        st.session_state['selected_category'] = 'Office'
    elif student_selected:
        st.session_state['selected_category'] = 'Student'
    elif all_selected:
        st.session_state['selected_category'] = 'Semua Laptop'

    selected_category = st.session_state.get('selected_category', 'Semua Laptop')

    # Show selected category
    category_icons = {'Gaming': '🎮', 'Office': '💼', 'Student': '🎓', 'Semua Laptop': '📱'}
    st.info(f"**Kategori terpilih:** {category_icons.get(selected_category, '📱')} {selected_category}")

    # Step 2: Set Priorities
    st.markdown("---")
    st.markdown("### ⚖️ Langkah 2: Tentukan Prioritas Anda")
    st.markdown("Pilih seberapa penting setiap kriteria bagi Anda:")

    importance_options = ["Tidak Penting", "Kurang Penting", "Cukup Penting", "Penting", "Sangat Penting"]

    # Create 2x3 grid for criteria
    col1, col2 = st.columns(2)

    with col1:
        # HARGA
        st.markdown("""
        <div class="criteria-card">
            <h4>💰 Harga (Budget)</h4>
            <p style="color: #666; font-size: 0.9rem;">Semakin penting = prefer harga lebih murah</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="data-range">
            📊 Range: <b>{format_price_idr(data_stats['price']['min'])}</b> - <b>{format_price_idr(data_stats['price']['max'])}</b>
        </div>
        """, unsafe_allow_html=True)
        price_importance = st.select_slider(
            "Prioritas Harga",
            options=importance_options,
            value="Sangat Penting",
            key="price_imp",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # RAM
        st.markdown("""
        <div class="criteria-card">
            <h4>🧠 RAM (Memori)</h4>
            <p style="color: #666; font-size: 0.9rem;">Semakin penting = prefer RAM lebih besar</p>
        </div>
        """, unsafe_allow_html=True)
        ram_options = [int(x) for x in data_stats['ram']['options'] if x > 0]
        st.markdown(f"""
        <div class="data-range">
            📊 Tersedia: <b>{', '.join([f'{x}GB' for x in ram_options[:6]])}</b>{'...' if len(ram_options) > 6 else ''}
        </div>
        """, unsafe_allow_html=True)
        ram_importance = st.select_slider(
            "Prioritas RAM",
            options=importance_options,
            value="Penting",
            key="ram_imp",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # SSD
        st.markdown("""
        <div class="criteria-card">
            <h4>💾 Storage (SSD)</h4>
            <p style="color: #666; font-size: 0.9rem;">Semakin penting = prefer kapasitas lebih besar</p>
        </div>
        """, unsafe_allow_html=True)
        ssd_options = [int(x) for x in data_stats['ssd']['options'] if x > 0]
        st.markdown(f"""
        <div class="data-range">
            📊 Tersedia: <b>{', '.join([f'{x}GB' for x in ssd_options[:5]])}</b>{'...' if len(ssd_options) > 5 else ''}
        </div>
        """, unsafe_allow_html=True)
        ssd_importance = st.select_slider(
            "Prioritas SSD",
            options=importance_options,
            value="Cukup Penting",
            key="ssd_imp",
            label_visibility="collapsed"
        )

    with col2:
        # RATING
        st.markdown("""
        <div class="criteria-card">
            <h4>⭐ Rating (Penilaian)</h4>
            <p style="color: #666; font-size: 0.9rem;">Semakin penting = prefer rating lebih tinggi</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="data-range">
            📊 Range: <b>{data_stats['rating']['min']:.0f}</b> - <b>{data_stats['rating']['max']:.0f}</b> (rata-rata: {data_stats['rating']['avg']:.0f})
        </div>
        """, unsafe_allow_html=True)
        rating_importance = st.select_slider(
            "Prioritas Rating",
            options=importance_options,
            value="Cukup Penting",
            key="rating_imp",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # DISPLAY
        st.markdown("""
        <div class="criteria-card">
            <h4>🖥️ Ukuran Layar</h4>
            <p style="color: #666; font-size: 0.9rem;">Semakin penting = prefer layar lebih besar</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
        <div class="data-range">
            📊 Range: <b>{data_stats['display']['min']:.1f}"</b> - <b>{data_stats['display']['max']:.1f}"</b>
        </div>
        """, unsafe_allow_html=True)
        display_importance = st.select_slider(
            "Prioritas Display",
            options=importance_options,
            value="Kurang Penting",
            key="display_imp",
            label_visibility="collapsed"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # GPU
        st.markdown("""
        <div class="criteria-card">
            <h4>🎮 GPU (Kartu Grafis)</h4>
            <p style="color: #666; font-size: 0.9rem;">Semakin penting = prefer GPU dedicated lebih besar</p>
        </div>
        """, unsafe_allow_html=True)
        gpu_options = [int(x) for x in data_stats['gpu']['options']]
        st.markdown(f"""
        <div class="data-range">
            📊 Tersedia: <b>Integrated (0GB)</b>, <b>{', '.join([f'{x}GB' for x in gpu_options if x > 0][:4])}</b>
        </div>
        """, unsafe_allow_html=True)
        gpu_importance = st.select_slider(
            "Prioritas GPU",
            options=importance_options,
            value="Cukup Penting",
            key="gpu_imp",
            label_visibility="collapsed"
        )

    # Convert importance to weights
    raw_weights = {
        'price_numeric': importance_to_weight(price_importance),
        'ram_numeric': importance_to_weight(ram_importance),
        'ssd_numeric': importance_to_weight(ssd_importance),
        'rating_numeric': importance_to_weight(rating_importance),
        'display_numeric': importance_to_weight(display_importance),
        'gpu_numeric': importance_to_weight(gpu_importance)
    }

    # Normalize weights to sum to 1.0
    total_raw = sum(raw_weights.values())
    weights = {k: v / total_raw for k, v in raw_weights.items()}

    # Show weight summary
    st.markdown("---")
    st.markdown("### 📊 Ringkasan Bobot Kriteria")

    weight_cols = st.columns(6)
    criteria_labels = ['💰 Harga', '🧠 RAM', '💾 SSD', '⭐ Rating', '🖥️ Display', '🎮 GPU']
    criteria_keys = ['price_numeric', 'ram_numeric', 'ssd_numeric', 'rating_numeric', 'display_numeric', 'gpu_numeric']

    for i, (col, label, key) in enumerate(zip(weight_cols, criteria_labels, criteria_keys)):
        with col:
            pct = weights[key] * 100
            color = "#667eea" if pct >= 20 else "#888"
            st.markdown(f"""
            <div style="text-align: center; padding: 0.5rem;">
                <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{pct:.0f}%</div>
                <div style="font-size: 0.8rem; color: #666;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # Step 3: Calculate
    st.markdown("---")
    st.markdown("### 🔍 Langkah 3: Dapatkan Rekomendasi")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        top_n = st.slider("Jumlah rekomendasi yang ditampilkan:", 5, 30, 10)
        calculate_btn = st.button(
            "🚀 CARI LAPTOP TERBAIK",
            type="primary",
            use_container_width=True
        )

    # =====================
    # RESULTS SECTION
    # =====================

    if calculate_btn:
        # Filter data by category
        filtered_df = filter_by_category(df, selected_category)

        if len(filtered_df) == 0:
            st.warning("⚠️ Tidak ada laptop yang sesuai dengan filter.")
            return

        # Calculate SAW scores
        with st.spinner("🔄 Menghitung rekomendasi..."):
            scores, decision_matrix, normalized_matrix = calculate_saw_scores(
                filtered_df, weights, CRITERIA_CONFIG
            )
            ranked_df = rank_alternatives(filtered_df, scores, top_n)

        # Store in session state
        st.session_state['results'] = ranked_df
        st.session_state['normalized'] = normalized_matrix.loc[ranked_df.index]
        st.session_state['decision'] = decision_matrix.loc[ranked_df.index]
        st.session_state['weights'] = weights
        st.session_state['show_results'] = True

    # Display results if available
    if st.session_state.get('show_results', False):
        ranked_df = st.session_state['results']
        normalized_matrix = st.session_state['normalized']
        decision_matrix = st.session_state['decision']
        used_weights = st.session_state['weights']

        st.markdown("---")
        st.markdown("## 🏆 Hasil Rekomendasi")

        # Top 3 Showcase
        st.markdown("### 🥇 Top 3 Laptop Terbaik")

        top3_cols = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        medal_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]

        for i, col in enumerate(top3_cols):
            if i < len(ranked_df):
                laptop = ranked_df.iloc[i]
                with col:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
                        border-radius: 15px;
                        padding: 1.5rem;
                        text-align: center;
                        border: 3px solid {medal_colors[i]};
                        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                        min-height: 350px;
                    ">
                        <div style="font-size: 3rem;">{medals[i]}</div>
                        <h4 style="margin: 0.5rem 0; font-size: 1rem; color: #333;">
                            {laptop['Model'][:40]}{'...' if len(str(laptop['Model'])) > 40 else ''}
                        </h4>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #667eea; margin: 0.5rem 0;">
                            {laptop['Price']}
                        </div>
                        <div style="font-size: 0.9rem; color: #666; margin-top: 1rem;">
                            <div>🧠 {laptop['Ram']}</div>
                            <div>💾 {laptop['SSD']}</div>
                            <div>🖥️ {laptop['Display'][:20]}...</div>
                            <div>⭐ Rating: {laptop['Rating']}</div>
                        </div>
                        <div style="
                            margin-top: 1rem;
                            padding: 0.5rem;
                            background: linear-gradient(90deg, #667eea, #764ba2);
                            border-radius: 20px;
                            color: white;
                            font-weight: bold;
                        ">
                            Skor: {laptop['SAW_Score']:.4f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Full ranking table
        st.markdown("### 📋 Ranking Lengkap")

        display_df = ranked_df[['Rank', 'Model', 'Price', 'Ram', 'SSD', 'Graphics', 'Rating', 'SAW_Score']].copy()
        display_df['SAW_Score'] = display_df['SAW_Score'].apply(lambda x: f"{x:.4f}")
        display_df.columns = ['Rank', 'Model Laptop', 'Harga', 'RAM', 'Storage', 'GPU', 'Rating', 'Skor SAW']

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # Charts
        st.markdown("### 📈 Visualisasi")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Bar chart
            chart_data = ranked_df.head(10).copy()
            chart_data['Short_Model'] = chart_data['Model'].apply(
                lambda x: x[:25] + '...' if len(str(x)) > 25 else x
            )

            fig_bar = px.bar(
                chart_data,
                x='SAW_Score',
                y='Short_Model',
                orientation='h',
                color='SAW_Score',
                color_continuous_scale='Purples',
                title='Top 10 Skor SAW'
            )
            fig_bar.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False,
                height=400,
                xaxis_title="Skor SAW",
                yaxis_title=""
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with chart_col2:
            # Pie chart
            weight_data = pd.DataFrame({
                'Kriteria': ['Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU'],
                'Bobot': [used_weights[k] for k in criteria_keys]
            })

            fig_pie = px.pie(
                weight_data,
                values='Bobot',
                names='Kriteria',
                title='Distribusi Bobot Kriteria',
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Detail section
        with st.expander("📖 Lihat Detail Perhitungan SAW", expanded=False):
            st.markdown("#### Matriks Keputusan (Nilai Asli)")
            decision_display = decision_matrix.head(10).copy()
            decision_display.insert(0, 'Model', ranked_df['Model'].values[:10])
            decision_display.columns = ['Model', 'Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU']
            st.dataframe(decision_display, use_container_width=True, hide_index=True)

            st.markdown("#### Matriks Ternormalisasi")
            norm_display = normalized_matrix.head(10).copy()
            norm_display.insert(0, 'Model', ranked_df['Model'].values[:10])
            for col in norm_display.columns[1:]:
                norm_display[col] = norm_display[col].apply(lambda x: f"{x:.4f}")
            norm_display.columns = ['Model', 'Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU']
            st.dataframe(norm_display, use_container_width=True, hide_index=True)

            st.markdown("#### Formula SAW")
            st.latex(r"V_i = \sum_{j=1}^{n} w_j \times r_{ij}")
            st.markdown("""
            **Keterangan:**
            - **Vᵢ** = Skor akhir laptop ke-i
            - **wⱼ** = Bobot kriteria ke-j
            - **rᵢⱼ** = Nilai ternormalisasi laptop ke-i pada kriteria ke-j
            - **Benefit** (RAM, SSD, dll): r = nilai / max
            - **Cost** (Harga): r = min / nilai
            """)

    else:
        # Initial state
        st.markdown("---")

        # Statistics cards
        st.markdown("### 📊 Statistik Dataset")

        stat_cols = st.columns(4)

        with stat_cols[0]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(df)}</div>
                <div class="stat-label">Total Laptop</div>
            </div>
            """, unsafe_allow_html=True)

        with stat_cols[1]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{category_counts.get('Gaming', 0)}</div>
                <div class="stat-label">🎮 Gaming</div>
            </div>
            """, unsafe_allow_html=True)

        with stat_cols[2]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{category_counts.get('Office', 0)}</div>
                <div class="stat-label">💼 Office</div>
            </div>
            """, unsafe_allow_html=True)

        with stat_cols[3]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{category_counts.get('Student', 0)}</div>
                <div class="stat-label">🎓 Student</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Sample data
        st.markdown("### 📋 Contoh Data Laptop")
        sample_df = df[['Model', 'Price', 'Ram', 'SSD', 'Graphics', 'Category']].head(8)
        sample_df.columns = ['Model', 'Harga', 'RAM', 'Storage', 'GPU', 'Kategori']
        st.dataframe(sample_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
