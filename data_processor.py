"""
Data Processor Module
Handles data loading, cleaning, and preprocessing for the Laptop DSS.
"""

import pandas as pd
import numpy as np
import re


def load_data(filepath: str) -> pd.DataFrame:
    """Load CSV data with proper encoding handling."""
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding='latin-1')
    return df


def clean_price(price_str) -> float:
    """
    Convert price string to numeric value.
    Example: "₹50,399" -> 50399.0
    """
    if pd.isna(price_str):
        return np.nan

    # Convert to string if not already
    price_str = str(price_str)

    # Remove currency symbol, commas, and whitespace
    cleaned = re.sub(r'[₹,\s]', '', price_str)

    try:
        return float(cleaned)
    except ValueError:
        return np.nan


def extract_ram(ram_str) -> int:
    """
    Extract RAM size in GB from string.
    Example: "8 GB DDR4 RAM" -> 8
    """
    if pd.isna(ram_str):
        return 0

    ram_str = str(ram_str)

    # Match patterns like "8 GB", "16GB", "32 GB"
    match = re.search(r'(\d+)\s*GB', ram_str, re.IGNORECASE)

    if match:
        return int(match.group(1))
    return 0


def extract_ssd(ssd_str) -> int:
    """
    Extract SSD/storage size in GB from string.
    Example: "512 GB SSD" -> 512
    Example: "1 TB SSD" -> 1024
    """
    if pd.isna(ssd_str):
        return 0

    ssd_str = str(ssd_str)

    # Check for TB first
    tb_match = re.search(r'(\d+)\s*TB', ssd_str, re.IGNORECASE)
    if tb_match:
        return int(tb_match.group(1)) * 1024

    # Check for GB
    gb_match = re.search(r'(\d+)\s*GB', ssd_str, re.IGNORECASE)
    if gb_match:
        return int(gb_match.group(1))

    return 0


def extract_display_size(display_str) -> float:
    """
    Extract display size in inches from string.
    Example: "15.6 inches, 1920 x 1080 pixels" -> 15.6
    """
    if pd.isna(display_str):
        return 0.0

    display_str = str(display_str)

    # Match patterns like "15.6 inches", "14 inches", "13.3 inches"
    match = re.search(r'(\d+\.?\d*)\s*inch', display_str, re.IGNORECASE)

    if match:
        return float(match.group(1))
    return 0.0


def extract_gpu_memory(graphics_str) -> int:
    """
    Extract GPU memory in GB from string.
    Returns 0 for integrated graphics.
    Example: "4 GB NVIDIA GeForce RTX 2050" -> 4
    Example: "Intel UHD Graphics" -> 0
    """
    if pd.isna(graphics_str):
        return 0

    graphics_str = str(graphics_str)

    # Check for integrated graphics keywords
    integrated_keywords = ['Intel', 'Integrated', 'UHD', 'Iris', 'AMD Radeon Graphics',
                          'Apple', 'Core GPU', 'Radeon Graphics']

    # If it contains GB before the graphics name, it's dedicated
    gb_match = re.search(r'(\d+)\s*GB', graphics_str, re.IGNORECASE)

    if gb_match:
        return int(gb_match.group(1))

    # Check if it's integrated
    for keyword in integrated_keywords:
        if keyword.lower() in graphics_str.lower():
            return 0

    return 0


def categorize_laptop(row) -> str:
    """
    Categorize laptop based on specifications.
    Categories:
    - Gaming: Has dedicated GPU (>=4GB) OR "Gaming" in model name
    - Student: Price < 40000 AND integrated graphics (GPU = 0)
    - Office: Everything else
    """
    model = str(row.get('Model', '')).lower()
    price = row.get('price_numeric', 0)
    gpu = row.get('gpu_numeric', 0)

    # Gaming category
    if 'gaming' in model or gpu >= 4:
        return 'Gaming'

    # Student category
    if price > 0 and price < 40000 and gpu == 0:
        return 'Student'

    # Office category (default)
    return 'Office'


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all preprocessing steps to the DataFrame.
    Returns cleaned DataFrame with numeric columns and category.
    """
    # Create a copy to avoid modifying original
    df = df.copy()

    # Extract numeric values
    df['price_numeric'] = df['Price'].apply(clean_price)
    df['ram_numeric'] = df['Ram'].apply(extract_ram)
    df['ssd_numeric'] = df['SSD'].apply(extract_ssd)
    df['display_numeric'] = df['Display'].apply(extract_display_size)
    df['gpu_numeric'] = df['Graphics'].apply(extract_gpu_memory)

    # Handle missing Rating values - fill with median
    df['rating_numeric'] = pd.to_numeric(df['Rating'], errors='coerce')
    median_rating = df['rating_numeric'].median()
    df['rating_numeric'] = df['rating_numeric'].fillna(median_rating)

    # Categorize laptops
    df['Category'] = df.apply(categorize_laptop, axis=1)

    # Remove rows with missing essential data
    df = df.dropna(subset=['price_numeric'])

    # Replace 0 values with small number to avoid division by zero in SAW
    for col in ['ram_numeric', 'ssd_numeric', 'display_numeric']:
        df[col] = df[col].replace(0, 0.1)

    return df


def filter_by_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    Filter DataFrame by laptop category.
    If category is 'Semua' or 'All', return all laptops.
    """
    if category.lower() in ['semua', 'all', 'semua laptop']:
        return df

    return df[df['Category'] == category]


def get_category_counts(df: pd.DataFrame) -> dict:
    """Return count of laptops in each category."""
    return df['Category'].value_counts().to_dict()
