"""
SAW (Simple Additive Weighting) Method Module
Implements the SAW algorithm for multi-criteria decision making.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


# Criteria configuration
CRITERIA_CONFIG = {
    'price_numeric': {
        'name': 'Harga',
        'type': 'cost',  # Lower is better
        'weight_default': 0.25
    },
    'ram_numeric': {
        'name': 'RAM',
        'type': 'benefit',  # Higher is better
        'weight_default': 0.20
    },
    'ssd_numeric': {
        'name': 'Storage (SSD)',
        'type': 'benefit',
        'weight_default': 0.15
    },
    'rating_numeric': {
        'name': 'Rating',
        'type': 'benefit',
        'weight_default': 0.15
    },
    'display_numeric': {
        'name': 'Ukuran Layar',
        'type': 'benefit',
        'weight_default': 0.10
    },
    'gpu_numeric': {
        'name': 'GPU Memory',
        'type': 'benefit',
        'weight_default': 0.15
    }
}


def normalize_benefit(values: pd.Series) -> pd.Series:
    """
    Normalize benefit criteria (higher is better).
    Formula: r[i] = x[i] / max(x)
    """
    max_val = values.max()
    if max_val == 0:
        return pd.Series([0] * len(values), index=values.index)
    return values / max_val


def normalize_cost(values: pd.Series) -> pd.Series:
    """
    Normalize cost criteria (lower is better).
    Formula: r[i] = min(x) / x[i]
    """
    min_val = values.min()
    # Avoid division by zero
    values_safe = values.replace(0, 0.001)
    return min_val / values_safe


def create_decision_matrix(df: pd.DataFrame, criteria_columns: List[str]) -> pd.DataFrame:
    """
    Create the decision matrix from DataFrame.
    Returns DataFrame with only the criteria columns.
    """
    return df[criteria_columns].copy()


def normalize_matrix(decision_matrix: pd.DataFrame, criteria_config: Dict) -> pd.DataFrame:
    """
    Normalize the decision matrix based on criteria types.
    Returns normalized matrix.
    """
    normalized = pd.DataFrame(index=decision_matrix.index)

    for col in decision_matrix.columns:
        if col in criteria_config:
            if criteria_config[col]['type'] == 'benefit':
                normalized[col] = normalize_benefit(decision_matrix[col])
            else:  # cost
                normalized[col] = normalize_cost(decision_matrix[col])
        else:
            # Default to benefit if not specified
            normalized[col] = normalize_benefit(decision_matrix[col])

    return normalized


def calculate_saw_scores(
    df: pd.DataFrame,
    weights: Dict[str, float],
    criteria_config: Dict = None
) -> Tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """
    Calculate SAW scores for all alternatives.

    Args:
        df: DataFrame with preprocessed laptop data
        weights: Dictionary mapping criteria column to weight
        criteria_config: Configuration for criteria (type: benefit/cost)

    Returns:
        Tuple of (scores Series, decision matrix, normalized matrix)
    """
    if criteria_config is None:
        criteria_config = CRITERIA_CONFIG

    # Get criteria columns that exist in DataFrame
    criteria_columns = [col for col in weights.keys() if col in df.columns]

    # Create decision matrix
    decision_matrix = create_decision_matrix(df, criteria_columns)

    # Normalize matrix
    normalized_matrix = normalize_matrix(decision_matrix, criteria_config)

    # Calculate weighted scores
    scores = pd.Series(0.0, index=df.index)

    for col in criteria_columns:
        weight = weights.get(col, 0)
        scores += normalized_matrix[col] * weight

    return scores, decision_matrix, normalized_matrix


def rank_alternatives(
    df: pd.DataFrame,
    scores: pd.Series,
    top_n: int = None
) -> pd.DataFrame:
    """
    Rank alternatives based on SAW scores.

    Args:
        df: Original DataFrame
        scores: SAW scores for each alternative
        top_n: Number of top results to return (None for all)

    Returns:
        Ranked DataFrame with scores and rank column
    """
    # Add scores to DataFrame
    result = df.copy()
    result['SAW_Score'] = scores

    # Sort by score descending
    result = result.sort_values('SAW_Score', ascending=False)

    # Add rank column
    result['Rank'] = range(1, len(result) + 1)

    # Return top N if specified
    if top_n is not None:
        result = result.head(top_n)

    return result


def validate_weights(weights: Dict[str, float], tolerance: float = 0.01) -> Tuple[bool, float]:
    """
    Validate that weights sum to 1.0 (within tolerance).

    Returns:
        Tuple of (is_valid, total_weight)
    """
    total = sum(weights.values())
    is_valid = abs(total - 1.0) <= tolerance
    return is_valid, total


def get_default_weights() -> Dict[str, float]:
    """Return default weights from criteria configuration."""
    return {col: config['weight_default'] for col, config in CRITERIA_CONFIG.items()}


def format_score(score: float) -> str:
    """Format SAW score for display."""
    return f"{score:.4f}"


def get_criteria_names() -> Dict[str, str]:
    """Return mapping of column names to display names."""
    return {col: config['name'] for col, config in CRITERIA_CONFIG.items()}


def calculate_detailed_scores(
    df: pd.DataFrame,
    weights: Dict[str, float],
    criteria_config: Dict = None
) -> pd.DataFrame:
    """
    Calculate detailed SAW scores showing contribution of each criterion.

    Returns DataFrame with normalized values and weighted contributions.
    """
    if criteria_config is None:
        criteria_config = CRITERIA_CONFIG

    scores, decision_matrix, normalized_matrix = calculate_saw_scores(
        df, weights, criteria_config
    )

    # Create detailed results
    detailed = pd.DataFrame(index=df.index)

    for col in weights.keys():
        if col in normalized_matrix.columns:
            # Add normalized value
            detailed[f'{col}_normalized'] = normalized_matrix[col]
            # Add weighted contribution
            detailed[f'{col}_weighted'] = normalized_matrix[col] * weights[col]

    detailed['SAW_Score'] = scores

    return detailed
