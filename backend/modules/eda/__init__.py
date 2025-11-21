"""Exploratory Data Analysis (EDA) module."""

from backend.modules.eda.eda_visualizer import (
    create_histogram,
    create_box_plot,
    create_correlation_matrix,
    create_missing_heatmap,
    create_scatter_plot,
    create_grouped_bar_chart,
    create_violin_plot,
    create_line_chart,
    create_area_chart,
    create_pie_chart,
    create_kde_plot,
    create_pair_plot,
    create_strip_plot,
    create_swarm_plot,
    create_ridge_plot
)
from backend.modules.eda.eda_analyzer import (
    calculate_correlations,
    detect_outliers,
    analyze_distributions,
    get_multivariate_stats
)
from backend.modules.eda.eda_llm_enhancer import (
    suggest_visualizations,
    interpret_analysis,
    suggest_next_steps_analysis
)

__all__ = [
    'create_histogram',
    'create_box_plot',
    'create_correlation_matrix',
    'create_missing_heatmap',
    'create_scatter_plot',
    'create_grouped_bar_chart',
    'create_violin_plot',
    'create_line_chart',
    'create_area_chart',
    'create_pie_chart',
    'create_kde_plot',
    'create_pair_plot',
    'create_strip_plot',
    'create_swarm_plot',
    'create_ridge_plot',
    'calculate_correlations',
    'detect_outliers',
    'analyze_distributions',
    'get_multivariate_stats',
    'suggest_visualizations',
    'interpret_analysis',
    'suggest_next_steps_analysis'
]

