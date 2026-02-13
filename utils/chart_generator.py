"""
Chart Generator - Create beautiful visualizations
"""
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import pandas as pd
from config import config

# Set style
plt.style.use(config.CHART_STYLE)
sns.set_palette("husl")

class ChartGenerator:
    """Generate charts for financial data"""
    
    @staticmethod
    def generate_expense_pie_chart(data: Dict[str, float], filename: str = "expense_chart.png") -> str:
        """
        Generate pie chart for expenses by category
        
        Args:
            data: {'Category': amount, ...}
            filename: output filename
        
        Returns:
            filepath
        """
        if not data:
            return None
        
        fig, ax = plt.subplots(figsize=config.CHART_FIGSIZE)
        
        categories = list(data.keys())
        amounts = list(data.values())
        
        # Create pie chart
        colors = sns.color_palette('pastel')[0:len(categories)]
        wedges, texts, autotexts = ax.pie(
            amounts,
            labels=categories,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10}
        )
        
        # Beautify
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('📊 Pengeluaran per Kategori', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=config.CHART_DPI, bbox_inches='tight')
        plt.close()
        
        return filename
    
    @staticmethod
    def generate_monthly_bar_chart(data: List[Dict], filename: str = "monthly_chart.png") -> str:
        """
        Generate bar chart for monthly income vs expense
        
        Args:
            data: [{'month': 'Jan', 'income': 5000000, 'expense': 3000000}, ...]
            filename: output filename
        
        Returns:
            filepath
        """
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=config.CHART_FIGSIZE)
        
        x = range(len(df))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], df['income'], width, label='Pemasukan', color='#2ecc71')
        bars2 = ax.bar([i + width/2 for i in x], df['expense'], width, label='Pengeluaran', color='#e74c3c')
        
        ax.set_xlabel('Bulan', fontweight='bold')
        ax.set_ylabel('Jumlah (Rp)', fontweight='bold')
        ax.set_title('💰 Pemasukan vs Pengeluaran', fontsize=14, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(df['month'])
        ax.legend()
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height/1000)}k',
                       ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=config.CHART_DPI, bbox_inches='tight')
        plt.close()
        
        return filename

# Convenience functions
def generate_expense_chart(data: Dict[str, float], filename: str = "expense_chart.png") -> str:
    """Generate expense pie chart"""
    return ChartGenerator.generate_expense_pie_chart(data, filename)

def generate_income_chart(data: List[Dict], filename: str = "monthly_chart.png") -> str:
    """Generate monthly bar chart"""
    return ChartGenerator.generate_monthly_bar_chart(data, filename)
