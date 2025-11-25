"""Visualization functions for EDA module supporting multiple libraries."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')


def sample_dataframe_for_visualization(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
    """
    Sample dataframe for visualization if it's too large.
    
    Args:
        df: DataFrame to sample
        max_rows: Maximum number of rows to keep
        
    Returns:
        Sampled DataFrame
    """
    if len(df) <= max_rows:
        return df
    
    # Use stratified sampling if possible, otherwise random sampling
    try:
        # Try to maintain distribution by sampling proportionally
        sample_size = min(max_rows, len(df))
        sampled_df = df.sample(n=sample_size, random_state=42)
        return sampled_df
    except:
        # Fallback to simple random sampling
        return df.sample(n=min(max_rows, len(df)), random_state=42)


def create_histogram(
    df: pd.DataFrame,
    column: str,
    library: str = 'plotly',
    bins: int = 30,
    title: Optional[str] = None,
    max_rows: int = 10000
) -> Any:
    """
    Create histogram for a numeric column.
    
    Args:
        df: DataFrame
        column: Column name
        library: Visualization library ('matplotlib', 'plotly', 'seaborn', 'streamlit')
        bins: Number of bins
        title: Chart title
        max_rows: Maximum rows to use for visualization (sampling for large datasets)
        
    Returns:
        Visualization object (varies by library)
    """
    if column not in df.columns:
        return None
    
    # Sample data if too large
    df_sampled = sample_dataframe_for_visualization(df, max_rows)
    
    col_data = df_sampled[column].dropna()
    
    if len(col_data) == 0:
        return None
    
    if title is None:
        title = f'{column} Dağılımı'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.histogram(
                df_sampled,
                x=column,
                nbins=bins,
                title=title,
                labels={column: column}
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                template='plotly_white'
            )
            return fig
        except ImportError:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(col_data, bins=bins, edgecolor='black', alpha=0.7)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(column, fontsize=12)
            ax.set_ylabel('Frekans', fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.histplot(data=df, x=column, bins=bins, ax=ax, kde=True)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'streamlit':
        # Return data for Streamlit's built-in chart
        return col_data
    
    return None


def create_box_plot(
    df: pd.DataFrame,
    column: str,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """
    Create box plot for a numeric column.
    
    Args:
        df: DataFrame
        column: Column name
        library: Visualization library
        title: Chart title
        
    Returns:
        Visualization object
    """
    if column not in df.columns:
        return None
    
    col_data = df[column].dropna()
    
    if len(col_data) == 0:
        return None
    
    if title is None:
        title = f'{column} Box Plot'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.box(
                df,
                y=column,
                title=title,
                labels={column: column}
            )
            fig.update_layout(
                showlegend=False,
                height=400,
                template='plotly_white'
            )
            return fig
        except ImportError:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.boxplot(col_data, vert=True)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_ylabel(column, fontsize=12)
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.boxplot(data=df, y=column, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'streamlit':
        return col_data
    
    return None


def create_correlation_matrix(
    df: pd.DataFrame,
    library: str = 'plotly',
    method: str = 'pearson',
    title: Optional[str] = None
) -> Any:
    """
    Create correlation matrix heatmap.
    
    Args:
        df: DataFrame
        library: Visualization library
        method: Correlation method ('pearson', 'kendall', 'spearman')
        title: Chart title
        
    Returns:
        Visualization object
    """
    # Select numeric columns using pandas dtype detection
    numeric_cols = df.select_dtypes(include=['number']).columns
    
    if len(numeric_cols) < 2:
        return None
    
    # Sabit sütunları filtrele (tüm değerleri aynı olan sütunlar)
    valid_numeric_cols = []
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            # Eğer sütunun tüm değerleri aynıysa (sabit sütun), atla
            if col_data.nunique() > 1:
                valid_numeric_cols.append(col)
    
    if len(valid_numeric_cols) < 2:
        return None
    
    corr_matrix = df[valid_numeric_cols].corr(method=method)
    
    if title is None:
        title = f'Korelasyon Matrisi ({method})'
    
    if library == 'plotly':
        try:
            import plotly.graph_objects as go
            import numpy
            
            # Text annotations için değerleri hazırla (numpy array olarak)
            text_values = numpy.empty_like(corr_matrix.values, dtype=object)
            for i in range(len(corr_matrix.columns)):
                for j in range(len(corr_matrix.columns)):
                    text_values[i, j] = f'{corr_matrix.iloc[i, j]:.2f}'
            
            # go.Heatmap ile text annotations ekle
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns.tolist(),
                y=corr_matrix.columns.tolist(),
                colorscale='RdBu',
                text=text_values,
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="Korelasyon"),
                zmid=0,
                zmin=-1,
                zmax=1,
                hovertemplate='%{y} vs %{x}<br>Korelasyon: %{z:.3f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=title,
                xaxis_title="Sütun",
                yaxis_title="Sütun",
                height=600,
                template='plotly_white'
            )
            return fig
        except ImportError:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 10))
            im = ax.imshow(corr_matrix, cmap='RdBu', aspect='auto', vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr_matrix.columns)))
            ax.set_yticks(range(len(corr_matrix.columns)))
            ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
            ax.set_yticklabels(corr_matrix.columns)
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            
            # Add text annotations (her kutucuğa değer yazdır)
            for i in range(len(corr_matrix.columns)):
                for j in range(len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    # Text rengini korelasyon değerine göre ayarla (koyu arka plan için beyaz, açık için siyah)
                    text_color = 'white' if abs(corr_value) > 0.5 else 'black'
                    text = ax.text(j, i, f'{corr_value:.2f}',
                                 ha="center", va="center", color=text_color, fontsize=8, fontweight='bold')
            
            plt.colorbar(im, ax=ax)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(
                corr_matrix,
                annot=True,
                fmt='.2f',
                cmap='RdBu',
                center=0,
                square=True,
                linewidths=0.5,
                cbar_kws={"shrink": 0.8},
                ax=ax
            )
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'streamlit':
        return corr_matrix
    
    return None


def create_missing_heatmap(
    df: pd.DataFrame,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """
    Create heatmap showing missing values pattern.
    
    Args:
        df: DataFrame
        library: Visualization library
        title: Chart title
        
    Returns:
        Visualization object or None if no missing values
    """
    if title is None:
        title = 'Eksik Değerler Haritası'
    
    # Eksik değer kontrolü - eğer hiç eksik değer yoksa None döndür
    if df.isnull().sum().sum() == 0:
        return None
    
    missing_matrix = df.isnull().astype(int)
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.imshow(
                missing_matrix,
                title=title,
                color_continuous_scale='Reds',
                aspect='auto',
                labels=dict(x="Sütun", y="Satır", color="Eksik")
            )
            fig.update_layout(height=600, template='plotly_white')
            return fig
        except ImportError:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 8))
            im = ax.imshow(missing_matrix, cmap='Reds', aspect='auto')
            ax.set_xticks(range(len(missing_matrix.columns)))
            ax.set_xticklabels(missing_matrix.columns, rotation=45, ha='right')
            ax.set_yticks(range(0, len(missing_matrix), max(1, len(missing_matrix) // 10)))
            ax.set_ylabel('Satır', fontsize=12)
            ax.set_xlabel('Sütun', fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            plt.colorbar(im, ax=ax)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(
                missing_matrix,
                cbar=True,
                cmap='Reds',
                yticklabels=False,
                ax=ax
            )
            ax.set_xticklabels(missing_matrix.columns, rotation=45, ha='right')
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'streamlit':
        return missing_matrix
    
    return None


def create_scatter_plot(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    library: str = 'plotly',
    color_column: Optional[str] = None,
    title: Optional[str] = None,
    max_rows: int = 10000
) -> Any:
    """
    Create scatter plot for two numeric columns.
    
    Args:
        df: DataFrame
        x_column: X-axis column
        y_column: Y-axis column
        library: Visualization library
        color_column: Optional column for color coding
        title: Chart title
        max_rows: Maximum rows to use for visualization (sampling for large datasets)
        
    Returns:
        Visualization object
    """
    if x_column not in df.columns or y_column not in df.columns:
        return None
    
    # Sample data if too large
    df_sampled = sample_dataframe_for_visualization(df, max_rows)
    
    if title is None:
        title = f'{x_column} vs {y_column}'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if color_column and color_column in df_sampled.columns:
                fig = px.scatter(
                    df_sampled,
                    x=x_column,
                    y=y_column,
                    color=color_column,
                    title=title,
                    labels={x_column: x_column, y_column: y_column}
                )
            else:
                fig = px.scatter(
                    df_sampled,
                    x=x_column,
                    y=y_column,
                    title=title,
                    labels={x_column: x_column, y_column: y_column}
                )
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            if color_column and color_column in df_sampled.columns:
                scatter = ax.scatter(df_sampled[x_column], df_sampled[y_column], c=df_sampled[color_column], cmap='viridis', alpha=0.6)
                plt.colorbar(scatter, ax=ax)
            else:
                ax.scatter(df_sampled[x_column], df_sampled[y_column], alpha=0.6)
            ax.set_xlabel(x_column, fontsize=12)
            ax.set_ylabel(y_column, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            if color_column and color_column in df_sampled.columns:
                sns.scatterplot(data=df_sampled, x=x_column, y=y_column, hue=color_column, ax=ax)
            else:
                sns.scatterplot(data=df_sampled, x=x_column, y=y_column, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
    
    return None


def create_grouped_bar_chart(
    df: pd.DataFrame,
    category_column: str,
    value_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """
    Create grouped bar chart for categorical data.
    
    Args:
        df: DataFrame
        category_column: Categorical column for grouping (x-axis)
        value_column: Optional column for values (y-axis). If None, counts are used.
        library: Visualization library
        title: Chart title
        
    Returns:
        Visualization object
    """
    if category_column not in df.columns:
        return None
    
    if title is None:
        if value_column:
            title = f'{category_column} vs {value_column}'
        else:
            title = f'{category_column} Dağılımı'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            
            # Eğer value_column varsa, cross-tabulation yap
            if value_column and value_column in df.columns:
                # Cross-tabulation oluştur
                try:
                    crosstab = pd.crosstab(df[category_column], df[value_column])
                    crosstab_melted = crosstab.reset_index().melt(
                        id_vars=category_column,
                        var_name=value_column,
                        value_name='count'
                    )
                    fig = px.bar(
                        crosstab_melted,
                        x=category_column,
                        y='count',
                        color=value_column,
                        title=title,
                        labels={category_column: category_column, 'count': 'Sayı', value_column: value_column},
                        barmode='group'
                    )
                except Exception as e:
                    # Cross-tabulation başarısız olursa, sadece category_column göster
                    value_counts = df[category_column].value_counts().reset_index()
                    value_counts.columns = [category_column, 'count']
                    fig = px.bar(
                        value_counts,
                        x=category_column,
                        y='count',
                        title=title,
                        labels={category_column: category_column, 'count': 'Sayı'}
                    )
            else:
                # Sadece category_column için count plot
                value_counts = df[category_column].value_counts().reset_index()
                value_counts.columns = [category_column, 'count']
                fig = px.bar(
                    value_counts,
                    x=category_column,
                    y='count',
                    title=title,
                    labels={category_column: category_column, 'count': 'Sayı'}
                )
            
            fig.update_layout(
                height=500,
                template='plotly_white',
                showlegend=True if value_column else False
            )
            return fig
        except ImportError:
            return None
        except Exception as e:
            # Hata durumunda None döndür
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Grouped bar chart hatası: {str(e)}")
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            
            if value_column and value_column in df.columns:
                # Cross-tabulation
                crosstab = pd.crosstab(df[category_column], df[value_column])
                fig, ax = plt.subplots(figsize=(12, 6))
                crosstab.plot(kind='bar', ax=ax, width=0.8)
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.set_xlabel(category_column, fontsize=12)
                ax.set_ylabel('Sayı', fontsize=12)
                ax.legend(title=value_column)
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                return fig
            else:
                # Value counts
                value_counts = df[category_column].value_counts()
                fig, ax = plt.subplots(figsize=(10, 6))
                value_counts.plot(kind='bar', ax=ax, width=0.8)
                ax.set_title(title, fontsize=14, fontweight='bold')
                ax.set_xlabel(category_column, fontsize=12)
                ax.set_ylabel('Sayı', fontsize=12)
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                return fig
        except ImportError:
            return None
        except Exception as e:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if value_column and value_column in df.columns:
                # Cross-tabulation
                crosstab = pd.crosstab(df[category_column], df[value_column])
                crosstab.plot(kind='bar', ax=ax, width=0.8)
            else:
                # Value counts
                value_counts = df[category_column].value_counts()
                sns.barplot(x=value_counts.index, y=value_counts.values, ax=ax)
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(category_column, fontsize=12)
            ax.set_ylabel('Sayı', fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception as e:
            return None
    
    return None


def create_violin_plot(
    df: pd.DataFrame,
    column: str,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create violin plot for a numeric column."""
    if column not in df.columns:
        return None
    
    col_data = df[column].dropna()
    if len(col_data) == 0:
        return None
    
    if title is None:
        title = f'{column} Violin Plot'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.violin(df, y=column, title=title, labels={column: column})
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.violinplot(data=df, y=column, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_line_chart(
    df: pd.DataFrame,
    x_column: str,
    y_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create line chart."""
    if x_column not in df.columns:
        return None
    
    if title is None:
        title = f'{x_column} Line Chart' if not y_column else f'{x_column} vs {y_column}'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if y_column and y_column in df.columns:
                fig = px.line(df, x=x_column, y=y_column, title=title)
            else:
                value_counts = df[x_column].value_counts().sort_index()
                fig = px.line(x=value_counts.index, y=value_counts.values, title=title)
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            if y_column and y_column in df.columns:
                ax.plot(df[x_column], df[y_column])
            else:
                value_counts = df[x_column].value_counts().sort_index()
                ax.plot(value_counts.index, value_counts.values)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.set_xlabel(x_column, fontsize=12)
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_area_chart(
    df: pd.DataFrame,
    x_column: str,
    y_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create area chart."""
    if x_column not in df.columns:
        return None
    
    if title is None:
        title = f'{x_column} Area Chart' if not y_column else f'{x_column} vs {y_column}'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if y_column and y_column in df.columns:
                fig = px.area(df, x=x_column, y=y_column, title=title)
            else:
                value_counts = df[x_column].value_counts().sort_index()
                fig = px.area(x=value_counts.index, y=value_counts.values, title=title)
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_pie_chart(
    df: pd.DataFrame,
    column: str,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create pie chart for categorical data."""
    if column not in df.columns:
        return None
    
    if title is None:
        title = f'{column} Distribution'
    
    value_counts = df[column].value_counts()
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.pie(values=value_counts.values, names=value_counts.index, title=title)
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'matplotlib':
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_kde_plot(
    df: pd.DataFrame,
    column: str,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create KDE (Kernel Density Estimation) plot."""
    if column not in df.columns:
        return None
    
    col_data = df[column].dropna()
    if len(col_data) == 0 or not pd.api.types.is_numeric_dtype(col_data):
        return None
    
    if title is None:
        title = f'{column} KDE Plot'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.histogram(df, x=column, nbins=30, histnorm='probability density', title=title)
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.kdeplot(data=df, x=column, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_pair_plot(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create pair plot for multiple numeric columns."""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if columns:
        numeric_cols = [c for c in columns if c in numeric_cols]
    
    if len(numeric_cols) < 2:
        return None
    
    # Limit to first 5 columns for performance
    numeric_cols = numeric_cols[:5]
    
    if title is None:
        title = 'Pair Plot'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.scatter_matrix(df[numeric_cols], title=title)
            fig.update_layout(height=800, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig = sns.pairplot(df[numeric_cols])
            fig.fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)
            plt.tight_layout()
            return fig.fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_strip_plot(
    df: pd.DataFrame,
    x_column: str,
    y_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create strip plot."""
    if x_column not in df.columns:
        return None
    
    if title is None:
        title = f'{x_column} Strip Plot' if not y_column else f'{x_column} vs {y_column}'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if y_column and y_column in df.columns:
                fig = px.strip(df, x=x_column, y=y_column, title=title)
            else:
                fig = px.box(df, y=x_column, title=title)
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            if y_column and y_column in df.columns:
                sns.stripplot(data=df, x=x_column, y=y_column, ax=ax)
            else:
                sns.stripplot(data=df, y=x_column, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_swarm_plot(
    df: pd.DataFrame,
    x_column: str,
    y_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create swarm plot."""
    if x_column not in df.columns:
        return None
    
    if title is None:
        title = f'{x_column} Swarm Plot' if not y_column else f'{x_column} vs {y_column}'
    
    if library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            if y_column and y_column in df.columns:
                sns.swarmplot(data=df, x=x_column, y=y_column, ax=ax)
            else:
                sns.swarmplot(data=df, y=x_column, ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    # Plotly doesn't have swarm plot, use strip plot instead
    return create_strip_plot(df, x_column, y_column, library='plotly', title=title)


def create_ridge_plot(
    df: pd.DataFrame,
    value_column: str,
    category_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create ridge plot (distribution plot for multiple categories)."""
    if value_column not in df.columns:
        return None
    
    if not pd.api.types.is_numeric_dtype(df[value_column]):
        return None
    
    if title is None:
        title = f'{value_column} Ridge Plot'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if category_column and category_column in df.columns:
                fig = px.violin(df, x=category_column, y=value_column, title=title, box=True)
            else:
                fig = px.violin(df, y=value_column, title=title, box=True)
            fig.update_layout(height=500, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            if category_column and category_column in df.columns:
                for cat in df[category_column].unique():
                    data = df[df[category_column] == cat][value_column]
                    sns.kdeplot(data=data, ax=ax, label=cat)
            else:
                sns.kdeplot(data=df[value_column], ax=ax)
            ax.set_title(title, fontsize=14, fontweight='bold')
            ax.legend()
            plt.tight_layout()
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_heatmap(
    df: pd.DataFrame,
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    value_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create general heatmap (not just correlation)."""
    if title is None:
        title = 'Heatmap'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if x_column and y_column and value_column:
                # Pivot table for heatmap
                pivot_df = df.pivot_table(values=value_column, index=y_column, columns=x_column, aggfunc='mean')
                fig = px.imshow(
                    pivot_df,
                    title=title,
                    color_continuous_scale='Viridis',
                    aspect='auto',
                    labels=dict(x=x_column, y=y_column, color=value_column)
                )
            else:
                # Use correlation matrix as fallback
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) >= 2:
                    corr_matrix = df[numeric_cols].corr()
                    fig = px.imshow(
                        corr_matrix,
                        title=title,
                        color_continuous_scale='RdBu',
                        aspect='auto'
                    )
                else:
                    return None
            fig.update_layout(height=600, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_sunburst(
    df: pd.DataFrame,
    path_columns: List[str],
    value_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create sunburst chart for hierarchical data."""
    if not path_columns or len(path_columns) < 1:
        return None
    
    if title is None:
        title = 'Sunburst Chart'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if value_column and value_column in df.columns:
                fig = px.sunburst(df, path=path_columns, values=value_column, title=title)
            else:
                # Count values
                df_count = df.groupby(path_columns).size().reset_index(name='count')
                fig = px.sunburst(df_count, path=path_columns, values='count', title=title)
            fig.update_layout(height=600, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_parallel_coordinates(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    color_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create parallel coordinates plot."""
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if columns:
        numeric_cols = [c for c in columns if c in numeric_cols]
    
    if len(numeric_cols) < 2:
        return None
    
    # Limit to 10 columns for performance
    numeric_cols = numeric_cols[:10]
    
    if title is None:
        title = 'Parallel Coordinates'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            if color_column and color_column in df.columns:
                fig = px.parallel_coordinates(
                    df[numeric_cols + [color_column]],
                    dimensions=numeric_cols,
                    color=color_column,
                    title=title
                )
            else:
                fig = px.parallel_coordinates(
                    df[numeric_cols],
                    dimensions=numeric_cols,
                    title=title
                )
            fig.update_layout(height=600, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_facet_grid(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    facet_column: str,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create facet grid (multiple plots in grid)."""
    if x_column not in df.columns or y_column not in df.columns or facet_column not in df.columns:
        return None
    
    if title is None:
        title = f'{y_column} vs {x_column} by {facet_column}'
    
    if library == 'plotly':
        try:
            import plotly.express as px
            fig = px.scatter(
                df,
                x=x_column,
                y=y_column,
                facet_col=facet_column,
                title=title
            )
            fig.update_layout(height=600, template='plotly_white')
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    elif library == 'seaborn':
        try:
            import seaborn as sns
            import matplotlib.pyplot as plt
            g = sns.FacetGrid(df, col=facet_column)
            g.map(plt.scatter, x_column, y_column)
            g.fig.suptitle(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            return g.fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None


def create_radar_chart(
    df: pd.DataFrame,
    categories: List[str],
    values_column: Optional[str] = None,
    library: str = 'plotly',
    title: Optional[str] = None
) -> Any:
    """Create radar chart (spider chart)."""
    if not categories or len(categories) < 3:
        return None
    
    if title is None:
        title = 'Radar Chart'
    
    if library == 'plotly':
        try:
            import plotly.graph_objects as go
            
            # Prepare data
            if values_column and values_column in df.columns:
                values = df[values_column].values
            else:
                # Use first numeric column or mean of categories
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    values = df[numeric_cols[0]].values
                else:
                    return None
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Values'
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True
                    )),
                showlegend=True,
                title=title,
                height=500,
                template='plotly_white'
            )
            return fig
        except ImportError:
            return None
        except Exception:
            return None
    
    return None

