"""
Sistem Penunjang Keputusan Pemilihan Laptop
Menggunakan Metode SAW (Simple Additive Weighting)

Modern Premium UI/UX Design
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
from data_processor import load_data, preprocess_data, filter_by_category, get_category_counts
from saw_method import (
    calculate_saw_scores,
    rank_alternatives,
    CRITERIA_CONFIG,
)
from ai_assistant import (
    parse_user_message,
    convert_ai_filters_to_app_filters,
    convert_ai_weights_to_app_weights,
    ConversationMemory,
    generate_explanation,
)

# Path to data file
DATA_FILE = 'laptop.csv'


def save_to_csv(new_data: dict):
    """Save new laptop data to CSV file"""
    # Load existing data
    df = pd.read_csv(DATA_FILE)

    # Create new row
    new_row = pd.DataFrame([new_data])

    # Append to dataframe
    df = pd.concat([df, new_row], ignore_index=True)

    # Save back to CSV
    df.to_csv(DATA_FILE, index=False)

    # Clear cache to reload data
    st.cache_data.clear()

    return True


def import_from_excel(uploaded_file):
    """Import data from Excel file"""
    try:
        # Read Excel file
        new_df = pd.read_excel(uploaded_file)

        # Check required columns
        required_cols = ['Model', 'Price', 'Ram', 'SSD', 'Display', 'Graphics']
        missing_cols = [col for col in required_cols if col not in new_df.columns]

        if missing_cols:
            return False, f"Missing columns: {', '.join(missing_cols)}"

        # Load existing data
        existing_df = pd.read_csv(DATA_FILE)

        # Append new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)

        # Save to CSV
        combined_df.to_csv(DATA_FILE, index=False)

        # Clear cache
        st.cache_data.clear()

        return True, f"Successfully imported {len(new_df)} laptops!"
    except Exception as e:
        return False, f"Error: {str(e)}"

# Page configuration
st.set_page_config(
    page_title="LaptopFinder AI | Smart Decision System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Premium CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    /* Root Variables */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #ec4899;
        --accent: #06b6d4;
        --dark: #0f172a;
        --dark-light: #1e293b;
        --gray: #64748b;
        --light: #f8fafc;
        --success: #10b981;
        --warning: #f59e0b;
        --glass: rgba(255, 255, 255, 0.05);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* Hide Streamlit Elements */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stToolbar"] {display: none;}
    div[data-testid="stDecoration"] {display: none;}

    /* Main Container */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        background-attachment: fixed;
    }

    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    /* Animated Background Orbs */
    .bg-orbs {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    }

    .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.4;
        animation: float 20s ease-in-out infinite;
    }

    .orb-1 {
        width: 600px;
        height: 600px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        top: -200px;
        right: -200px;
        animation-delay: 0s;
    }

    .orb-2 {
        width: 500px;
        height: 500px;
        background: linear-gradient(135deg, #ec4899, #f43f5e);
        bottom: -150px;
        left: -150px;
        animation-delay: -5s;
    }

    .orb-3 {
        width: 400px;
        height: 400px;
        background: linear-gradient(135deg, #06b6d4, #0ea5e9);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation-delay: -10s;
    }

    @keyframes float {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(50px, -50px) scale(1.1); }
        50% { transform: translate(-30px, 30px) scale(0.95); }
        75% { transform: translate(-50px, -30px) scale(1.05); }
    }

    /* Hero Section */
    .hero-section {
        text-align: center;
        padding: 3rem 0;
        position: relative;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.2));
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 8px 20px;
        border-radius: 50px;
        font-size: 0.85rem;
        color: #a5b4fc;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 4rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #fff 0%, #a5b4fc 50%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.25rem;
        color: #94a3b8;
        max-width: 600px;
        margin: 0 auto 2rem;
        line-height: 1.6;
        text-align: center;
        align-items: center;
        display: block;
    }

    /* Glass Card */
    .glass-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        margin: 2rem 0;
    }

    .stat-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.4));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .stat-card:hover::before {
        opacity: 1;
    }

    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.2);
    }

    .stat-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }

    .stat-number {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fff, #a5b4fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .stat-label {
        font-size: 0.9rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Category Cards */
    .category-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .category-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(30, 41, 59, 0.3));
        border: 2px solid transparent;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .category-card::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 16px;
        padding: 2px;
        background: linear-gradient(135deg, transparent, transparent);
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        transition: background 0.3s ease;
    }

    .category-card:hover::before {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
    }

    .category-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
    }

    .category-card.selected {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(236, 72, 153, 0.2));
        border-color: var(--primary);
    }

    .category-icon {
        font-size: 3rem;
        margin-bottom: 0.75rem;
        display: block;
    }

    .category-name {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
        margin-bottom: 0.25rem;
    }

    .category-count {
        font-size: 0.85rem;
        color: #64748b;
    }

    /* Section Title */
    .section-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 2.5rem 0 1.5rem;
    }

    .section-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        border-radius: 12px;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        color: #fff;
        font-size: 1.1rem;
    }

    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #fff;
    }

    /* Criteria Card */
    .criteria-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(30, 41, 59, 0.3));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }

    .criteria-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.5));
    }

    .criteria-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
    }

    .criteria-icon {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        font-size: 1.25rem;
    }

    .criteria-icon.price { background: linear-gradient(135deg, #10b981, #059669); }
    .criteria-icon.ram { background: linear-gradient(135deg, #6366f1, #4f46e5); }
    .criteria-icon.storage { background: linear-gradient(135deg, #f59e0b, #d97706); }
    .criteria-icon.rating { background: linear-gradient(135deg, #ec4899, #db2777); }
    .criteria-icon.display { background: linear-gradient(135deg, #06b6d4, #0891b2); }
    .criteria-icon.gpu { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

    .criteria-name {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #fff;
        font-size: 1rem;
    }

    .criteria-type {
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 20px;
        margin-left: auto;
    }

    .criteria-type.cost {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
    }

    .criteria-type.benefit {
        background: rgba(99, 102, 241, 0.2);
        color: #a5b4fc;
    }

    .criteria-range {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
    }

    /* Weight Display */
    .weight-display {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .weight-item {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(30, 41, 59, 0.3));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }

    .weight-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.75rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .weight-label {
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.25rem;
    }

    /* Action Button */
    .action-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.1rem;
        padding: 1rem 3rem;
        border-radius: 16px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);
        text-decoration: none;
        width: 100%;
        margin: 1rem 0;
    }

    .action-button:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.4);
    }

    /* Streamlit Button Override */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: #fff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        padding: 1rem 2rem !important;
        border-radius: 16px !important;
        border: none !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3) !important;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.4) !important;
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    }

    /* Result Cards */
    .result-podium {
        display: grid;
        grid-template-columns: 1fr 1.2fr 1fr;
        gap: 1.5rem;
        margin: 2rem 0;
        align-items: end;
    }

    .podium-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.4));
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .podium-card:hover {
        transform: translateY(-10px);
    }

    .podium-card.gold {
        border: 2px solid #fbbf24;
        box-shadow: 0 20px 60px rgba(251, 191, 36, 0.2);
    }

    .podium-card.silver {
        border: 2px solid #9ca3af;
        box-shadow: 0 15px 40px rgba(156, 163, 175, 0.15);
    }

    .podium-card.bronze {
        border: 2px solid #d97706;
        box-shadow: 0 15px 40px rgba(217, 119, 6, 0.15);
    }

    .podium-rank {
        position: absolute;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.75rem;
    }

    .podium-rank.gold { background: linear-gradient(135deg, #fbbf24, #f59e0b); }
    .podium-rank.silver { background: linear-gradient(135deg, #9ca3af, #6b7280); }
    .podium-rank.bronze { background: linear-gradient(135deg, #d97706, #b45309); }

    .podium-model {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #fff;
        font-size: 1rem;
        margin: 2rem 0 0.5rem;
        line-height: 1.4;
    }

    .podium-price {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }

    .podium-specs {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin: 1rem 0;
        font-size: 0.85rem;
        color: #94a3b8;
    }

    .podium-score {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(236, 72, 153, 0.2));
        border-radius: 12px;
        padding: 0.75rem;
        margin-top: 1rem;
    }

    .podium-score-label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .podium-score-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #fff;
    }

    /* Data Table Styling */
    .dataframe {
        background: transparent !important;
        border: none !important;
    }

    div[data-testid="stDataFrame"] {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        overflow: hidden;
    }

    div[data-testid="stDataFrame"] > div {
        background: transparent !important;
    }

    /* Slider Styling */
    .stSlider > div > div {
        background: rgba(99, 102, 241, 0.3) !important;
    }

    .stSlider > div > div > div {
        background: linear-gradient(135deg, #6366f1, #ec4899) !important;
    }

    /* Select Slider */
    div[data-baseweb="slider"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 10px;
        padding: 0.5rem;
    }

    /* Chart Container */
    .chart-container {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(30, 41, 59, 0.5) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Info/Success/Warning boxes */
    .stAlert {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }

    /* Radio buttons */
    .stRadio > div {
        background: transparent !important;
    }

    .stRadio label {
        color: #fff !important;
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
        margin: 2rem 0;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .stats-grid { grid-template-columns: repeat(2, 1fr); }
        .category-grid { grid-template-columns: repeat(2, 1fr); }
        .weight-display { grid-template-columns: repeat(3, 1fr); }
        .result-podium { grid-template-columns: 1fr; }
    }

    /* Chat Bubble Styles */
    .chat-container {
        max-height: 400px;
        overflow-y: auto;
        padding: 1rem;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 16px;
        margin-bottom: 1rem;
    }

    .chat-bubble {
        max-width: 85%;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        line-height: 1.5;
        font-size: 0.95rem;
    }

    .chat-bubble-ai {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.15));
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 20px 20px 20px 4px;
        margin-right: auto;
        color: #e2e8f0;
    }

    .chat-bubble-user {
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(244, 63, 94, 0.15));
        border: 1px solid rgba(236, 72, 153, 0.3);
        border-radius: 20px 20px 4px 20px;
        margin-left: auto;
        color: #e2e8f0;
        text-align: right;
    }

    .chat-sender {
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .chat-bubble-ai .chat-sender {
        justify-content: flex-start;
    }

    .chat-bubble-user .chat-sender {
        justify-content: flex-end;
    }

    .ai-filters-badge {
        display: inline-block;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.25rem 0.25rem 0.25rem 0;
    }

    .ai-thinking {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #94a3b8;
        font-size: 0.9rem;
        padding: 1rem;
    }

    .ai-thinking .dot {
        width: 8px;
        height: 8px;
        background: #6366f1;
        border-radius: 50%;
        animation: pulse 1.5s ease-in-out infinite;
    }

    .ai-thinking .dot:nth-child(2) { animation-delay: 0.2s; }
    .ai-thinking .dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes pulse {
        0%, 100% { opacity: 0.3; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1); }
    }

    /* API Key Input */
    .api-key-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(30, 41, 59, 0.4));
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .api-key-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }

    .api-key-status.valid {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
    }

    .api-key-status.invalid {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
    }
</style>

<!-- Background Orbs -->
<div class="bg-orbs">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_preprocess_data():
    df = load_data('laptop.csv')
    df = preprocess_data(df)
    return df


@st.cache_data
def get_data_statistics(df):
    stats = {
        'price': {'min': df['price_numeric'].min(), 'max': df['price_numeric'].max()},
        'ram': {'options': sorted([int(x) for x in df['ram_numeric'].unique() if x > 0])},
        'ssd': {'options': sorted([int(x) for x in df['ssd_numeric'].unique() if x > 0])},
        'display': {'min': df['display_numeric'].min(), 'max': df['display_numeric'].max()},
        'gpu': {'options': sorted([int(x) for x in df['gpu_numeric'].unique()])},
        'rating': {'min': df['rating_numeric'].min(), 'max': df['rating_numeric'].max(), 'avg': df['rating_numeric'].mean()}
    }
    return stats


def format_price(price):
    """Format price to Rupiah (IDR) - assuming 1 INR = 192 IDR (approximate rate)"""
    # Convert from INR to IDR (1 INR ≈ 192 IDR)
    price_idr = price * 192
    if price_idr >= 1000000000:  # >= 1 Miliar
        return f"Rp {price_idr/1000000000:.1f} Miliar"
    elif price_idr >= 1000000:  # >= 1 Juta
        return f"Rp {price_idr/1000000:.1f} Juta"
    else:
        return f"Rp {price_idr:,.0f}".replace(",", ".")


def format_price_display(price_str):
    """Convert price string from INR to IDR for display"""
    import re
    # Extract numeric value from price string like "₹50,399"
    cleaned = re.sub(r'[₹,\s]', '', str(price_str))
    try:
        price_inr = float(cleaned)
        price_idr = price_inr * 192  # Convert to IDR
        if price_idr >= 1000000:
            return f"Rp {price_idr/1000000:.1f} Juta"
        else:
            return f"Rp {price_idr:,.0f}".replace(",", ".")
    except:
        return price_str


def main():
    # Load data
    try:
        df = load_and_preprocess_data()
        data_stats = get_data_statistics(df)
        category_counts = get_category_counts(df)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return

    # ========== DATA MANAGEMENT SECTION (TOP) ==========
    with st.expander("📥 Kelola Data Laptop", expanded=False):
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.05));
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(99, 102, 241, 0.2);
        ">
            <h4 style="color: #fff; margin: 0;">Tambah Data Laptop Baru</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                Input manual atau import dari file Excel (.xlsx)
            </p>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["📝 Input Manual", "📊 Import Excel", "👁️ Lihat Data"])

        # Tab 1: Manual Input
        with tab1:
            st.markdown("##### Masukkan Data Laptop Baru")

            col_form1, col_form2 = st.columns(2)

            with col_form1:
                model_name = st.text_input(
                    "Nama Model Laptop *",
                    placeholder="Contoh: ASUS ROG Strix G15",
                    key="input_model"
                )
                price = st.number_input(
                    "Harga (Rp) *",
                    min_value=0,
                    value=10000000,
                    step=500000,
                    format="%d",
                    key="input_price",
                    help="Masukkan harga dalam Rupiah"
                )
                ram = st.selectbox(
                    "RAM (GB) *",
                    options=[4, 8, 16, 32, 64],
                    index=1,
                    key="input_ram"
                )
                ssd = st.selectbox(
                    "Storage/SSD (GB) *",
                    options=[128, 256, 512, 1024, 2048],
                    index=2,
                    key="input_ssd"
                )

            with col_form2:
                display_size = st.selectbox(
                    "Ukuran Layar (inch) *",
                    options=[13.3, 14.0, 15.6, 16.0, 17.3],
                    index=2,
                    key="input_display"
                )
                graphics = st.text_input(
                    "Graphics/GPU *",
                    placeholder="Contoh: NVIDIA GeForce RTX 4060 8GB",
                    key="input_graphics"
                )
                rating = st.slider(
                    "Rating (0-100)",
                    min_value=0,
                    max_value=100,
                    value=70,
                    key="input_rating"
                )
                generation = st.text_input(
                    "Processor/Generation",
                    placeholder="Contoh: 13th Gen Intel Core i7",
                    key="input_gen"
                )

            col_extra1, col_extra2, col_extra3 = st.columns(3)
            with col_extra1:
                core = st.text_input(
                    "Core Info",
                    placeholder="Contoh: Octa Core, 16 Threads",
                    key="input_core"
                )
            with col_extra2:
                os_type = st.selectbox(
                    "Operating System",
                    options=["Windows 11 OS", "Windows 10 OS", "Mac OS", "DOS OS", "Linux"],
                    key="input_os"
                )
            with col_extra3:
                warranty = st.selectbox(
                    "Warranty",
                    options=["1 Year Warranty", "2 Year Warranty", "3 Year Warranty"],
                    key="input_warranty"
                )

            if st.button("💾 Simpan Data Laptop", type="primary", use_container_width=True):
                if model_name and graphics:
                    # Convert price from IDR to INR for storage (1 INR ≈ 192 IDR)
                    price_inr = price / 192

                    new_laptop = {
                        'Unnamed: 0': '',
                        'Model': model_name,
                        'Price': f"₹{price_inr:,.0f}",
                        'Rating': rating,
                        'Generation': generation if generation else 'N/A',
                        'Core': core if core else 'N/A',
                        'Ram': f"{ram} GB DDR4 RAM",
                        'SSD': f"{ssd} GB SSD",
                        'Display': f"{display_size} inches, 1920 x 1080 pixels",
                        'Graphics': graphics,
                        'OS': os_type,
                        'Warranty': warranty
                    }

                    if save_to_csv(new_laptop):
                        st.success(f"✅ Laptop '{model_name}' berhasil ditambahkan!")
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Mohon isi Nama Model dan Graphics!")

        # Tab 2: Import Excel
        with tab2:
            st.markdown("##### Import Data dari Excel")

            st.info("""
            **Format Excel yang dibutuhkan:**
            - Kolom wajib: `Model`, `Price`, `Ram`, `SSD`, `Display`, `Graphics`
            - Kolom opsional: `Rating`, `Generation`, `Core`, `OS`, `Warranty`
            """)

            # Download template button
            template_data = {
                'Model': ['Contoh Laptop 1', 'Contoh Laptop 2'],
                'Price': ['₹50,000', '₹75,000'],
                'Rating': [70, 80],
                'Generation': ['13th Gen Intel Core i5', '12th Gen Intel Core i7'],
                'Core': ['Quad Core, 8 Threads', 'Octa Core, 16 Threads'],
                'Ram': ['8 GB DDR4 RAM', '16 GB DDR5 RAM'],
                'SSD': ['512 GB SSD', '1 TB SSD'],
                'Display': ['15.6 inches, 1920 x 1080 pixels', '14 inches, 2560 x 1600 pixels'],
                'Graphics': ['Intel Iris Xe', 'NVIDIA GeForce RTX 3050 4GB'],
                'OS': ['Windows 11 OS', 'Windows 11 OS'],
                'Warranty': ['1 Year Warranty', '1 Year Warranty']
            }
            template_df = pd.DataFrame(template_data)

            # Create downloadable template
            import io
            buffer = io.BytesIO()
            template_df.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)

            st.download_button(
                label="📥 Download Template Excel",
                data=buffer,
                file_name="template_laptop.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            uploaded_file = st.file_uploader(
                "Upload File Excel (.xlsx)",
                type=['xlsx'],
                key="excel_upload"
            )

            if uploaded_file is not None:
                # Preview the data
                preview_df = pd.read_excel(uploaded_file)
                st.markdown("**Preview Data:**")
                st.dataframe(preview_df.head(5), use_container_width=True)

                col_imp1, col_imp2 = st.columns(2)
                with col_imp1:
                    st.metric("Jumlah Data", len(preview_df))
                with col_imp2:
                    st.metric("Kolom", len(preview_df.columns))

                if st.button("📤 Import Data", type="primary", use_container_width=True):
                    uploaded_file.seek(0)  # Reset file pointer
                    success, message = import_from_excel(uploaded_file)
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)

        # Tab 3: View Data
        with tab3:
            st.markdown("##### Data Laptop Saat Ini")

            # Load raw data
            raw_df = pd.read_csv(DATA_FILE)

            col_view1, col_view2, col_view3 = st.columns(3)
            with col_view1:
                st.metric("Total Data", len(raw_df))
            with col_view2:
                st.metric("Kolom", len(raw_df.columns))
            with col_view3:
                search = st.text_input("🔍 Cari Model", placeholder="Ketik nama laptop...", key="search_model")

            if search:
                filtered = raw_df[raw_df['Model'].str.contains(search, case=False, na=False)]
                st.dataframe(filtered[['Model', 'Price', 'Ram', 'SSD', 'Graphics', 'Rating']].head(20), use_container_width=True, hide_index=True)
                st.caption(f"Menampilkan {len(filtered)} hasil")
            else:
                st.dataframe(raw_df[['Model', 'Price', 'Ram', 'SSD', 'Graphics', 'Rating']].tail(10), use_container_width=True, hide_index=True)
                st.caption("Menampilkan 10 data terakhir")

    # ========== HERO SECTION ==========
    st.markdown("""
    <div class="hero-section">
        <div class="hero-badge">
            <span>✨</span>
            <span>KELOMPOK 3 - Powered by SAW Algorithm</span>
        </div>
        <h1 class="hero-title">Sistem cerdas untuk menemukan laptop impian Anda.
            Analisis {total}+ laptop dengan teknologi Decision Support System.</h1>
    </div>
    """.format(total=len(df)), unsafe_allow_html=True)

    # ========== STATS SECTION ==========
    st.markdown(f"""
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-icon">💻</div>
            <div class="stat-number">{len(df)}</div>
            <div class="stat-label">Total Laptop</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🎮</div>
            <div class="stat-number">{category_counts.get('Gaming', 0)}</div>
            <div class="stat-label">Gaming Laptop</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">💼</div>
            <div class="stat-number">{category_counts.get('Office', 0)}</div>
            <div class="stat-label">Office Laptop</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🎓</div>
            <div class="stat-number">{category_counts.get('Student', 0)}</div>
            <div class="stat-label">Student Laptop</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ========== STEP 1: CATEGORY ==========
    st.markdown("""
    <div class="section-header">
        <div class="section-number">1</div>
        <div class="section-title">Pilih Kategori Kebutuhan</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🎮 Gaming", key="btn_gaming", use_container_width=True):
            st.session_state['category'] = 'Gaming'
    with col2:
        if st.button("💼 Office", key="btn_office", use_container_width=True):
            st.session_state['category'] = 'Office'
    with col3:
        if st.button("🎓 Student", key="btn_student", use_container_width=True):
            st.session_state['category'] = 'Student'
    with col4:
        if st.button("📱 Semua", key="btn_all", use_container_width=True):
            st.session_state['category'] = 'Semua Laptop'

    selected_cat = st.session_state.get('category', 'Semua Laptop')
    cat_icons = {'Gaming': '🎮', 'Office': '💼', 'Student': '🎓', 'Semua Laptop': '📱'}

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(236, 72, 153, 0.1));
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    ">
        <span style="font-size: 1.5rem;">{cat_icons.get(selected_cat, '📱')}</span>
        <span style="color: #fff; font-weight: 500;">Kategori terpilih: <strong>{selected_cat}</strong></span>
    </div>
    """, unsafe_allow_html=True)

    # ========== STEP 2: AI CHAT & FILTER ==========
    st.markdown("""
    <div class="section-header">
        <div class="section-number">2</div>
        <div class="section-title">Cari Laptop dengan AI atau Filter Manual</div>
    </div>
    """, unsafe_allow_html=True)

    # Initialize session states
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'ai_filters' not in st.session_state:
        st.session_state['ai_filters'] = {}
    if 'ai_weights' not in st.session_state:
        st.session_state['ai_weights'] = {}
    if 'use_ai_mode' not in st.session_state:
        st.session_state['use_ai_mode'] = True
    if 'conversation_memory' not in st.session_state:
        st.session_state['conversation_memory'] = ConversationMemory()

    # Convert price range to IDR for display
    price_min_idr = int(data_stats['price']['min'] * 192)
    price_max_idr = int(data_stats['price']['max'] * 192)

    # Tabs for AI Chat and Manual Filter
    tab_ai, tab_manual = st.tabs(["💬 Chat dengan AI", "⚙️ Filter Manual"])

    # ===== TAB 1: AI CHAT =====
    with tab_ai:
        st.session_state['use_ai_mode'] = True

        # Chat Interface
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.05));
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(99, 102, 241, 0.2);
        ">
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
                💡 <strong style="color: #fff;">Contoh pertanyaan:</strong><br>
                "Saya butuh laptop untuk editing video, budget 15 juta"<br>
                "Cari laptop gaming murah dengan RAM besar"<br>
                "Laptop untuk mahasiswa, ringan dan tahan lama"
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Display chat history
        chat_container = st.container()
        with chat_container:
            if not st.session_state['chat_history']:
                st.markdown("""
                <div class="chat-bubble chat-bubble-ai">
                    <div class="chat-sender">🤖 AI Assistant</div>
                    <div>Halo! Saya siap membantu Anda menemukan laptop yang tepat.
                    Ceritakan kebutuhan Anda, misalnya untuk apa laptopnya dan berapa budget yang tersedia.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for chat in st.session_state['chat_history']:
                    if chat['role'] == 'user':
                        st.markdown(f"""
                        <div class="chat-bubble chat-bubble-user">
                            <div class="chat-sender">👤 Anda</div>
                            <div>{chat['content']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Check if this is a recommendation message
                        if chat.get('is_recommendation'):
                            # Recommendation message with special styling
                            st.markdown("""
                            <div class="chat-bubble chat-bubble-ai" style="
                                background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.1));
                                border: 1px solid rgba(16, 185, 129, 0.3);
                            ">
                                <div class="chat-sender">🎯 Hasil Rekomendasi</div>
                            </div>
                            """, unsafe_allow_html=True)
                            # Use st.markdown for proper markdown rendering
                            st.markdown(chat['content'])
                        elif chat.get('is_clarification'):
                            # Clarification message with distinct styling
                            st.markdown(f"""
                            <div class="chat-bubble chat-bubble-ai" style="
                                background: linear-gradient(135deg, rgba(251, 191, 36, 0.15), rgba(245, 158, 11, 0.1));
                                border: 1px solid rgba(251, 191, 36, 0.3);
                            ">
                                <div class="chat-sender">❓ Klarifikasi</div>
                                <div>{chat['content']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # AI response with filters badges
                            filters_html = ""
                            if chat.get('filters'):
                                filters_html = "<div style='margin-top: 0.75rem;'>"
                                f = chat['filters']
                                if f.get('price_max'):
                                    filters_html += f"<span class='ai-filters-badge'>💰 Budget ≤ Rp {f['price_max']:,.0f}</span>".replace(",", ".")
                                if f.get('ram_min'):
                                    filters_html += f"<span class='ai-filters-badge'>🧠 RAM ≥ {f['ram_min']}GB</span>"
                                if f.get('gpu_min'):
                                    filters_html += f"<span class='ai-filters-badge'>🎮 GPU ≥ {f['gpu_min']}GB</span>"
                                if f.get('ssd_min'):
                                    filters_html += f"<span class='ai-filters-badge'>💾 SSD ≥ {f['ssd_min']}GB</span>"
                                filters_html += "</div>"

                            st.markdown(f"""
                            <div class="chat-bubble chat-bubble-ai">
                                <div class="chat-sender">🤖 AI Assistant</div>
                                <div>{chat['content']}</div>
                                {filters_html}
                            </div>
                            """, unsafe_allow_html=True)

        # Chat input
        col_input, col_send = st.columns([5, 1])
        with col_input:
            user_message = st.text_input(
                "Ketik pesan",
                placeholder="Ceritakan kebutuhan laptop Anda...",
                key="chat_input",
                label_visibility="collapsed"
            )
        with col_send:
            send_button = st.button("📤", use_container_width=True, key="send_chat")

        # Process chat
        if send_button and user_message:
            # Get memory
            memory = st.session_state['conversation_memory']

            # Add user message to history and memory
            st.session_state['chat_history'].append({
                'role': 'user',
                'content': user_message
            })
            memory.add_message('user', user_message)

            # Process with AI (with memory context)
            with st.spinner("🤔 AI sedang menganalisis..."):
                result = parse_user_message(user_message, data_stats, memory)

            # Check if AI needs clarification
            if result.get('needs_clarification', False):
                # AI is asking for clarification
                clarification_msg = result['response_message']
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': clarification_msg,
                    'is_clarification': True
                })
                memory.add_message('assistant', clarification_msg)
                st.rerun()

            elif result['success']:
                # Store filters and weights
                st.session_state['ai_filters'] = result['filters']
                st.session_state['ai_weights'] = result['weights']

                # Update memory with detected preferences
                if result.get('detected_preferences'):
                    memory.update_preferences(result['detected_preferences'])

                # Convert to app format
                app_filters = convert_ai_filters_to_app_filters(
                    result['filters'], data_stats
                )
                app_weights = convert_ai_weights_to_app_weights(
                    result['weights']
                )
                st.session_state['filters'] = app_filters
                st.session_state['weights'] = app_weights

                # === AUTO CALCULATE SAW & GENERATE RESULTS ===
                # Filter data by category
                filtered_df = filter_by_category(df, selected_cat)

                # Apply range filters
                if app_filters:
                    filtered_df = filtered_df[
                        (filtered_df['price_numeric'] >= app_filters['price'][0]) &
                        (filtered_df['price_numeric'] <= app_filters['price'][1])
                    ]
                    filtered_df = filtered_df[
                        (filtered_df['ram_numeric'] >= app_filters['ram'][0]) &
                        (filtered_df['ram_numeric'] <= app_filters['ram'][1])
                    ]
                    filtered_df = filtered_df[
                        (filtered_df['ssd_numeric'] >= app_filters['ssd'][0]) &
                        (filtered_df['ssd_numeric'] <= app_filters['ssd'][1])
                    ]
                    filtered_df = filtered_df[
                        (filtered_df['rating_numeric'] >= app_filters['rating'][0]) &
                        (filtered_df['rating_numeric'] <= app_filters['rating'][1])
                    ]
                    filtered_df = filtered_df[
                        (filtered_df['display_numeric'] >= app_filters['display'][0]) &
                        (filtered_df['display_numeric'] <= app_filters['display'][1])
                    ]
                    filtered_df = filtered_df[
                        (filtered_df['gpu_numeric'] >= app_filters['gpu'][0]) &
                        (filtered_df['gpu_numeric'] <= app_filters['gpu'][1])
                    ]

                # Generate recommendation message
                if len(filtered_df) == 0:
                    recommendation_msg = "😔 Maaf, tidak ada laptop yang sesuai dengan kriteria Anda. Coba perluas budget atau kurangi spesifikasi yang diminta."
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': result['response_message'],
                        'filters': result['filters'],
                        'weights': result['weights']
                    })
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': recommendation_msg
                    })
                    memory.add_message('assistant', result['response_message'])
                    memory.add_message('assistant', recommendation_msg)
                else:
                    # Calculate SAW
                    scores, decision_matrix, normalized_matrix = calculate_saw_scores(
                        filtered_df, app_weights, CRITERIA_CONFIG
                    )
                    ranked_df = rank_alternatives(filtered_df, scores, min(5, len(filtered_df)))

                    # Store results
                    st.session_state['results'] = ranked_df
                    st.session_state['normalized'] = normalized_matrix.loc[ranked_df.index]
                    st.session_state['decision'] = decision_matrix.loc[ranked_df.index]
                    st.session_state['show_results'] = True

                    # Build recommendation chat message with EXPLAINABILITY
                    recommendation_msg = f"🎯 **Berdasarkan analisis kebutuhan Anda, berikut {min(3, len(ranked_df))} laptop terbaik:**\n\n"

                    # Prepare user preferences for explanation
                    user_prefs = memory.user_preferences.copy()
                    if result.get('use_case'):
                        user_prefs['use_case'] = result['use_case']

                    # Convert ranked_df to list of dicts for explanation
                    candidates_list = ranked_df.to_dict('records')

                    medals = ['🥇', '🥈', '🥉']
                    for i, (idx, laptop) in enumerate(ranked_df.head(3).iterrows()):
                        medal = medals[i] if i < 3 else f"{i+1}."
                        price_idr = laptop['price_numeric'] * 192
                        if price_idr >= 1000000:
                            price_str = f"Rp {price_idr/1000000:.1f} Juta"
                        else:
                            price_str = f"Rp {price_idr:,.0f}".replace(",", ".")

                        recommendation_msg += f"{medal} **{laptop['Model'][:40]}{'...' if len(str(laptop['Model'])) > 40 else ''}**\n"
                        recommendation_msg += f"   💰 {price_str} | ⭐ Rating: {laptop['Rating']} | Score: {laptop['SAW_Score']:.3f}\n"
                        recommendation_msg += f"   🧠 {laptop['Ram']} | 💾 {laptop['SSD']}\n"

                        # Add explanation for top laptop only
                        if i == 0:
                            laptop_dict = laptop.to_dict()
                            explanation = generate_explanation(laptop_dict, user_prefs, candidates_list, rank=1)
                            if explanation:
                                recommendation_msg += f"\n{explanation}\n"

                        recommendation_msg += "\n"

                        # Track recommended laptops in memory
                        memory.add_recommended_laptop(laptop['Model'][:30])

                    # Add AI analysis + recommendations to chat history
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': result['response_message'],
                        'filters': result['filters'],
                        'weights': result['weights']
                    })
                    st.session_state['chat_history'].append({
                        'role': 'assistant',
                        'content': recommendation_msg,
                        'is_recommendation': True
                    })
                    memory.add_message('assistant', result['response_message'])
                    memory.add_message('assistant', recommendation_msg)

                st.session_state['ai_ready'] = True
                st.rerun()
            else:
                # Error handling
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': result['response_message']
                })
                memory.add_message('assistant', result['response_message'])
                st.error(f"⚠️ {result.get('error', 'Terjadi kesalahan')}")

                col_retry, col_manual = st.columns(2)
                with col_retry:
                    if st.button("🔄 Coba Lagi"):
                        st.rerun()
                with col_manual:
                    if st.button("⚙️ Gunakan Mode Manual"):
                        st.session_state['use_ai_mode'] = False
                        st.rerun()

        # Clear chat button
        if st.session_state['chat_history']:
            if st.button("🗑️ Hapus Riwayat Chat", use_container_width=True):
                st.session_state['chat_history'] = []
                st.session_state['ai_filters'] = {}
                st.session_state['ai_weights'] = {}
                st.session_state['ai_ready'] = False
                # Reset conversation memory
                st.session_state['conversation_memory'] = ConversationMemory()
                st.rerun()

        # Show AI-generated weights summary
        if st.session_state.get('ai_weights'):
            st.markdown("""
            <div class="section-header">
                <div class="section-number">📊</div>
                <div class="section-title">Prioritas dari AI</div>
            </div>
            """, unsafe_allow_html=True)

            ai_w = st.session_state['ai_weights']
            labels = ['Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU']
            icons = ['💰', '🧠', '💾', '⭐', '🖥️', '🎮']
            weight_keys = ['price', 'ram', 'ssd', 'rating', 'display', 'gpu']

            weight_cols = st.columns(6)
            for col, label, icon, key in zip(weight_cols, labels, icons, weight_keys):
                with col:
                    stars = ai_w.get(key, 3)
                    star_display = '⭐' * stars + '☆' * (5 - stars)
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(30, 41, 59, 0.3));
                        border: 1px solid rgba(99, 102, 241, 0.3);
                        border-radius: 12px;
                        padding: 0.75rem;
                        text-align: center;
                    ">
                        <div style="font-size: 1.25rem;">{icon}</div>
                        <div style="font-size: 0.7rem; color: #fbbf24; margin: 0.25rem 0;">{star_display}</div>
                        <div style="font-size: 0.7rem; color: #94a3b8;">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ===== TAB 2: MANUAL FILTER =====
    with tab_manual:
        st.session_state['use_ai_mode'] = False

        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(236, 72, 153, 0.05));
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(99, 102, 241, 0.2);
        ">
            <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">
                🎯 <strong style="color: #fff;">Mode Manual:</strong> Atur filter range dan prioritas (bobot) untuk setiap kriteria.
                Prioritas 1-5 bintang menentukan seberapa penting kriteria tersebut dalam perhitungan SAW.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Price
            st.markdown("""
            <div class="criteria-card">
                <div class="criteria-header">
                    <div class="criteria-icon price">💰</div>
                    <span class="criteria-name">Harga / Budget</span>
                    <span class="criteria-type cost">COST</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_price_range, col_price_priority = st.columns([3, 1])
            with col_price_range:
                manual_price_range = st.slider(
                    "Range Harga " ,
                    min_value=price_min_idr,
                    max_value=price_max_idr,
                    value=(price_min_idr, price_max_idr),
                    step=1000000,
                    key="manual_filter_price"
                )
            with col_price_priority:
                price_priority = st.slider("⭐", 1, 5, 3, key="priority_price", help="Prioritas Harga")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #a5b4fc; margin-top: -0.5rem;">
                <span>Rp {manual_price_range[0]:,.0f} - Rp {manual_price_range[1]:,.0f}</span>
                <span style="color: #fbbf24;">{'⭐' * price_priority}{'☆' * (5-price_priority)}</span>
            </div>
            """.replace(",", "."), unsafe_allow_html=True)

            # RAM
            st.markdown("""
            <div class="criteria-card">
                <div class="criteria-header">
                    <div class="criteria-icon ram">🧠</div>
                    <span class="criteria-name">RAM / Memori</span>
                    <span class="criteria-type benefit">BENEFIT</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_ram_range, col_ram_priority = st.columns([3, 1])
            with col_ram_range:
                ram_options = data_stats['ram']['options']
                manual_ram_range = st.select_slider(
                    "Range RAM (GB)",
                    options=ram_options,
                    value=(min(ram_options), max(ram_options)),
                    key="manual_filter_ram"
                )
            with col_ram_priority:
                ram_priority = st.slider("⭐", 1, 5, 3, key="priority_ram", help="Prioritas RAM")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #a5b4fc;">
                <span>{manual_ram_range[0]}GB - {manual_ram_range[1]}GB</span>
                <span style="color: #fbbf24;">{'⭐' * ram_priority}{'☆' * (5-ram_priority)}</span>
            </div>
            """, unsafe_allow_html=True)

            # Storage
            st.markdown("""
            <div class="criteria-card">
                <div class="criteria-header">
                    <div class="criteria-icon storage">💾</div>
                    <span class="criteria-name">Storage / SSD</span>
                    <span class="criteria-type benefit">BENEFIT</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_ssd_range, col_ssd_priority = st.columns([3, 1])
            with col_ssd_range:
                ssd_options = data_stats['ssd']['options']
                manual_ssd_range = st.select_slider(
                    "Range SSD (GB)",
                    options=ssd_options,
                    value=(min(ssd_options), max(ssd_options)),
                    key="manual_filter_ssd"
                )
            with col_ssd_priority:
                ssd_priority = st.slider("⭐", 1, 5, 3, key="priority_ssd", help="Prioritas SSD")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #a5b4fc;">
                <span>{manual_ssd_range[0]}GB - {manual_ssd_range[1]}GB</span>
                <span style="color: #fbbf24;">{'⭐' * ssd_priority}{'☆' * (5-ssd_priority)}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Rating
            st.markdown("""
            <div class="criteria-card">
                <div class="criteria-header">
                    <div class="criteria-icon rating">⭐</div>
                    <span class="criteria-name">Rating / Penilaian</span>
                    <span class="criteria-type benefit">BENEFIT</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_rating_range, col_rating_priority = st.columns([3, 1])
            with col_rating_range:
                manual_rating_range = st.slider(
                    "Range Rating",
                    min_value=int(data_stats['rating']['min']),
                    max_value=int(data_stats['rating']['max']),
                    value=(int(data_stats['rating']['min']), int(data_stats['rating']['max'])),
                    key="manual_filter_rating"
                )
            with col_rating_priority:
                rating_priority = st.slider("⭐", 1, 5, 3, key="priority_rating", help="Prioritas Rating")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #a5b4fc;">
                <span>{manual_rating_range[0]} - {manual_rating_range[1]}</span>
                <span style="color: #fbbf24;">{'⭐' * rating_priority}{'☆' * (5-rating_priority)}</span>
            </div>
            """, unsafe_allow_html=True)

            # Display
            st.markdown("""
            <div class="criteria-card">
                <div class="criteria-header">
                    <div class="criteria-icon display">🖥️</div>
                    <span class="criteria-name">Ukuran Layar</span>
                    <span class="criteria-type benefit">BENEFIT</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_display_range, col_display_priority = st.columns([3, 1])
            with col_display_range:
                manual_display_range = st.slider(
                    "Range Display (inch)",
                    min_value=float(data_stats['display']['min']),
                    max_value=float(data_stats['display']['max']),
                    value=(float(data_stats['display']['min']), float(data_stats['display']['max'])),
                    step=0.1,
                    key="manual_filter_display"
                )
            with col_display_priority:
                display_priority = st.slider("⭐", 1, 5, 3, key="priority_display", help="Prioritas Display")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #a5b4fc;">
                <span>{manual_display_range[0]:.1f}" - {manual_display_range[1]:.1f}"</span>
                <span style="color: #fbbf24;">{'⭐' * display_priority}{'☆' * (5-display_priority)}</span>
            </div>
            """, unsafe_allow_html=True)

            # GPU
            st.markdown("""
            <div class="criteria-card">
                <div class="criteria-header">
                    <div class="criteria-icon gpu">🎮</div>
                    <span class="criteria-name">GPU / Kartu Grafis</span>
                    <span class="criteria-type benefit">BENEFIT</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_gpu_range, col_gpu_priority = st.columns([3, 1])
            with col_gpu_range:
                gpu_options = data_stats['gpu']['options']
                manual_gpu_range = st.select_slider(
                    "Range GPU VRAM (GB)",
                    options=gpu_options,
                    value=(min(gpu_options), max(gpu_options)),
                    format_func=lambda x: f"{x}GB" if x > 0 else "Integrated",
                    key="manual_filter_gpu"
                )
            with col_gpu_priority:
                gpu_priority = st.slider("⭐", 1, 5, 3, key="priority_gpu", help="Prioritas GPU")
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #a5b4fc;">
                <span>{f"{manual_gpu_range[0]}GB" if manual_gpu_range[0] > 0 else "Integrated"} - {manual_gpu_range[1]}GB</span>
                <span style="color: #fbbf24;">{'⭐' * gpu_priority}{'☆' * (5-gpu_priority)}</span>
            </div>
            """, unsafe_allow_html=True)

        # Weight Summary for Manual Mode
        st.markdown("""
        <div class="section-header" style="margin-top: 1.5rem;">
            <div class="section-number">📊</div>
            <div class="section-title">Ringkasan Bobot Kriteria</div>
        </div>
        """, unsafe_allow_html=True)

        # Calculate normalized weights from star ratings
        star_to_weight = {1: 0.05, 2: 0.10, 3: 0.15, 4: 0.20, 5: 0.25}
        raw_weights = {
            'price': star_to_weight[price_priority],
            'ram': star_to_weight[ram_priority],
            'ssd': star_to_weight[ssd_priority],
            'rating': star_to_weight[rating_priority],
            'display': star_to_weight[display_priority],
            'gpu': star_to_weight[gpu_priority]
        }
        total_weight = sum(raw_weights.values())
        normalized_weights = {k: v / total_weight for k, v in raw_weights.items()}

        # Display weight summary
        weight_cols = st.columns(6)
        labels = ['Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU']
        icons = ['💰', '🧠', '💾', '⭐', '🖥️', '🎮']
        weight_keys = ['price', 'ram', 'ssd', 'rating', 'display', 'gpu']
        priorities = [price_priority, ram_priority, ssd_priority, rating_priority, display_priority, gpu_priority]

        for col, label, icon, key, priority in zip(weight_cols, labels, icons, weight_keys, priorities):
            with col:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(30, 41, 59, 0.3));
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 12px;
                    padding: 0.75rem;
                    text-align: center;
                ">
                    <div style="font-size: 1.25rem;">{icon}</div>
                    <div style="font-size: 0.7rem; color: #fbbf24; margin: 0.25rem 0;">{'⭐' * priority}{'☆' * (5-priority)}</div>
                    <div style="font-size: 1rem; font-weight: bold; color: #a5b4fc;">{normalized_weights[key]*100:.1f}%</div>
                    <div style="font-size: 0.7rem; color: #94a3b8;">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        # Store manual filter ranges and weights
        if not st.session_state.get('use_ai_mode') or not st.session_state.get('ai_ready'):
            st.session_state['filters'] = {
                'price': (manual_price_range[0] / 192, manual_price_range[1] / 192),
                'ram': manual_ram_range,
                'ssd': manual_ssd_range,
                'rating': manual_rating_range,
                'display': manual_display_range,
                'gpu': manual_gpu_range
            }
            # Weights from star priorities
            st.session_state['weights'] = {
                'price_numeric': normalized_weights['price'],
                'ram_numeric': normalized_weights['ram'],
                'ssd_numeric': normalized_weights['ssd'],
                'rating_numeric': normalized_weights['rating'],
                'display_numeric': normalized_weights['display'],
                'gpu_numeric': normalized_weights['gpu']
            }

    # Get current weights for display
    weights = st.session_state.get('weights', {
        'price_numeric': 1/6, 'ram_numeric': 1/6, 'ssd_numeric': 1/6,
        'rating_numeric': 1/6, 'display_numeric': 1/6, 'gpu_numeric': 1/6
    })

    # ========== STEP 3: CALCULATE ==========
    st.markdown("""
    <div class="section-header">
        <div class="section-number">3</div>
        <div class="section-title">Dapatkan Rekomendasi</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        top_n = st.slider("Jumlah rekomendasi", 5, 30, 10, key="top_n")
        calculate = st.button("🚀 ANALISIS SEKARANG", use_container_width=True, type="primary")

    # ========== RESULTS ==========
    if calculate:
        filtered_df = filter_by_category(df, selected_cat)

        # Apply range filters
        filters = st.session_state.get('filters', {})
        if filters:
            # Price filter
            filtered_df = filtered_df[
                (filtered_df['price_numeric'] >= filters['price'][0]) &
                (filtered_df['price_numeric'] <= filters['price'][1])
            ]
            # RAM filter
            filtered_df = filtered_df[
                (filtered_df['ram_numeric'] >= filters['ram'][0]) &
                (filtered_df['ram_numeric'] <= filters['ram'][1])
            ]
            # SSD filter
            filtered_df = filtered_df[
                (filtered_df['ssd_numeric'] >= filters['ssd'][0]) &
                (filtered_df['ssd_numeric'] <= filters['ssd'][1])
            ]
            # Rating filter
            filtered_df = filtered_df[
                (filtered_df['rating_numeric'] >= filters['rating'][0]) &
                (filtered_df['rating_numeric'] <= filters['rating'][1])
            ]
            # Display filter
            filtered_df = filtered_df[
                (filtered_df['display_numeric'] >= filters['display'][0]) &
                (filtered_df['display_numeric'] <= filters['display'][1])
            ]
            # GPU filter
            filtered_df = filtered_df[
                (filtered_df['gpu_numeric'] >= filters['gpu'][0]) &
                (filtered_df['gpu_numeric'] <= filters['gpu'][1])
            ]

        if len(filtered_df) == 0:
            st.warning("Tidak ada laptop yang sesuai filter. Coba perluas range filter Anda.")
            return

        with st.spinner("🔄 Menganalisis data..."):
            scores, decision_matrix, normalized_matrix = calculate_saw_scores(filtered_df, weights, CRITERIA_CONFIG)
            ranked_df = rank_alternatives(filtered_df, scores, top_n)

        st.session_state['results'] = ranked_df
        st.session_state['normalized'] = normalized_matrix.loc[ranked_df.index]
        st.session_state['decision'] = decision_matrix.loc[ranked_df.index]
        st.session_state['weights'] = weights
        st.session_state['show_results'] = True

    if st.session_state.get('show_results', False):
        ranked_df = st.session_state['results']
        used_weights = st.session_state['weights']

        st.markdown("""
        <div class="section-header" style="margin-top: 3rem;">
            <div class="section-number">🏆</div>
            <div class="section-title">Top 3 Rekomendasi Terbaik</div>
        </div>
        """, unsafe_allow_html=True)

        # Top 3 Podium
        if len(ranked_df) >= 3:
            col_s, col_g, col_b = st.columns([1, 1.2, 1])

            # Silver (2nd)
            with col_s:
                laptop = ranked_df.iloc[1]
                st.markdown(f"""
                <div class="podium-card silver" style="margin-top: 40px;">
                    <div class="podium-rank silver">🥈</div>
                    <div class="podium-model">{laptop['Model'][:45]}{'...' if len(str(laptop['Model'])) > 45 else ''}</div>
                    <div class="podium-price">{format_price_display(laptop['Price'])}</div>
                    <div class="podium-specs">
                        <span>🧠 {laptop['Ram']}</span>
                        <span>💾 {laptop['SSD']}</span>
                        <span>⭐ Rating: {laptop['Rating']}</span>
                    </div>
                    <div class="podium-score">
                        <div class="podium-score-label">SAW Score</div>
                        <div class="podium-score-value">{laptop['SAW_Score']:.4f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Gold (1st)
            with col_g:
                laptop = ranked_df.iloc[0]
                st.markdown(f"""
                <div class="podium-card gold">
                    <div class="podium-rank gold">🥇</div>
                    <div class="podium-model">{laptop['Model'][:45]}{'...' if len(str(laptop['Model'])) > 45 else ''}</div>
                    <div class="podium-price">{format_price_display(laptop['Price'])}</div>
                    <div class="podium-specs">
                        <span>🧠 {laptop['Ram']}</span>
                        <span>💾 {laptop['SSD']}</span>
                        <span>🖥️ {str(laptop['Display'])[:25]}...</span>
                        <span>⭐ Rating: {laptop['Rating']}</span>
                    </div>
                    <div class="podium-score">
                        <div class="podium-score-label">SAW Score</div>
                        <div class="podium-score-value">{laptop['SAW_Score']:.4f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Bronze (3rd)
            with col_b:
                laptop = ranked_df.iloc[2]
                st.markdown(f"""
                <div class="podium-card bronze" style="margin-top: 40px;">
                    <div class="podium-rank bronze">🥉</div>
                    <div class="podium-model">{laptop['Model'][:45]}{'...' if len(str(laptop['Model'])) > 45 else ''}</div>
                    <div class="podium-price">{format_price_display(laptop['Price'])}</div>
                    <div class="podium-specs">
                        <span>🧠 {laptop['Ram']}</span>
                        <span>💾 {laptop['SSD']}</span>
                        <span>⭐ Rating: {laptop['Rating']}</span>
                    </div>
                    <div class="podium-score">
                        <div class="podium-score-label">SAW Score</div>
                        <div class="podium-score-value">{laptop['SAW_Score']:.4f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Full Table
        st.markdown("""
        <div class="section-header">
            <div class="section-number">📋</div>
            <div class="section-title">Ranking Lengkap</div>
        </div>
        """, unsafe_allow_html=True)

        display_df = ranked_df[['Rank', 'Model', 'Price', 'Ram', 'SSD', 'Graphics', 'Rating', 'SAW_Score']].copy()
        display_df['Price'] = display_df['Price'].apply(format_price_display)
        display_df['SAW_Score'] = display_df['SAW_Score'].apply(lambda x: f"{x:.4f}")
        display_df.columns = ['#', 'Model', 'Harga (Rp)', 'RAM', 'Storage', 'GPU', 'Rating', 'Score']

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

        # Charts
        st.markdown("""
        <div class="section-header">
            <div class="section-number">📈</div>
            <div class="section-title">Visualisasi Data</div>
        </div>
        """, unsafe_allow_html=True)

        chart1, chart2 = st.columns(2)

        with chart1:
            chart_data = ranked_df.head(10).copy()
            chart_data['Short'] = chart_data['Model'].apply(lambda x: x[:20] + '...' if len(str(x)) > 20 else x)

            fig = px.bar(
                chart_data, x='SAW_Score', y='Short', orientation='h',
                color='SAW_Score', color_continuous_scale='Purples',
                title='Top 10 SAW Scores'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8',
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with chart2:
            weight_data = pd.DataFrame({
                'Kriteria': ['Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU'],
                'Bobot': [used_weights[k] for k in keys]
            })

            fig2 = px.pie(
                weight_data, values='Bobot', names='Kriteria',
                title='Distribusi Bobot',
                color_discrete_sequence=px.colors.sequential.Purples_r
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#94a3b8',
                height=400
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig2, use_container_width=True)

        # SAW Details
        with st.expander("📖 Detail Perhitungan SAW"):
            st.markdown("### Matriks Keputusan")
            dec_display = st.session_state['decision'].head(10).copy()
            dec_display.insert(0, 'Model', ranked_df['Model'].values[:10])
            dec_display.columns = ['Model', 'Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU']
            st.dataframe(dec_display, use_container_width=True, hide_index=True)

            st.markdown("### Matriks Normalisasi")
            norm_display = st.session_state['normalized'].head(10).copy()
            norm_display.insert(0, 'Model', ranked_df['Model'].values[:10])
            for col in norm_display.columns[1:]:
                norm_display[col] = norm_display[col].apply(lambda x: f"{x:.4f}")
            norm_display.columns = ['Model', 'Harga', 'RAM', 'SSD', 'Rating', 'Display', 'GPU']
            st.dataframe(norm_display, use_container_width=True, hide_index=True)

            st.markdown("### Formula SAW")
            st.latex(r"V_i = \sum_{j=1}^{n} w_j \times r_{ij}")
            st.markdown("""
            - **Benefit** (higher is better): `r = value / max`
            - **Cost** (lower is better): `r = min / value`
            """)


if __name__ == "__main__":
    main()
