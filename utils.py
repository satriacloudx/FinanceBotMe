"""
Utility functions untuk formatting, chart generation, dan export
"""
import io
from typing import List, Tuple, Dict
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Backend non-GUI untuk server
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set style untuk chart yang lebih estetik
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def format_currency(amount: float) -> str:
    """Format angka menjadi format Rupiah"""
    return f"Rp {amount:,.0f}".replace(',', '.')


def generate_pie_chart(data: List[Tuple], title: str) -> io.BytesIO:
    """
    Generate Pie Chart dari data kategori
    Returns BytesIO object yang bisa langsung dikirim ke Telegram
    """
    if not data:
        return None
    
    try:
        # Prepare data
        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Color palette yang menarik
        colors = sns.color_palette("husl", len(categories))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            amounts, 
            labels=categories,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11}
        )
        
        # Styling
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Save to BytesIO
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    except Exception as e:
        print(f"Error generating pie chart: {e}")
        return None


def generate_bar_chart(data: List[Tuple], title: str, xlabel: str = "Kategori", 
                       ylabel: str = "Nominal (Rp)") -> io.BytesIO:
    """
    Generate Bar Chart dari data kategori
    Returns BytesIO object yang bisa langsung dikirim ke Telegram
    """
    if not data:
        return None
    
    try:
        # Prepare data
        categories = [row[0] for row in data]
        amounts = [row[1] for row in data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Color palette
        colors = sns.color_palette("viridis", len(categories))
        
        # Create bar chart
        bars = ax.bar(categories, amounts, color=colors, edgecolor='black', linewidth=0.5)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{format_currency(height)}',
                   ha='center', va='bottom', fontsize=9, rotation=0)
        
        # Styling
        ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Rotate x labels if too many categories
        if len(categories) > 5:
            plt.xticks(rotation=45, ha='right')
        
        # Grid
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        # Save to BytesIO
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return buf
    except Exception as e:
        print(f"Error generating bar chart: {e}")
        return None


def export_to_csv(data: List[Dict]) -> io.BytesIO:
    """
    Export data ke CSV format
    Returns BytesIO object
    """
    if not data:
        return None
    
    try:
        df = pd.DataFrame(data)
        buf = io.BytesIO()
        df.to_csv(buf, index=False, encoding='utf-8-sig')
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return None


def export_to_excel(data: List[Dict], sheet_name: str = "Transaksi") -> io.BytesIO:
    """
    Export data ke Excel format dengan styling
    Returns BytesIO object
    """
    if not data:
        return None
    
    try:
        df = pd.DataFrame(data)
        buf = io.BytesIO()
        
        # Create Excel writer
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Auto-adjust column width
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        return None


def get_current_month_name() -> str:
    """Mendapatkan nama bulan saat ini dalam Bahasa Indonesia"""
    months = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
        'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ]
    return months[datetime.now().month - 1]


def validate_amount(text: str) -> Tuple[bool, float]:
    """
    Validasi input nominal
    Returns (is_valid, amount)
    """
    try:
        # Remove common separators
        cleaned = text.replace('.', '').replace(',', '').replace(' ', '')
        amount = float(cleaned)
        
        if amount <= 0:
            return False, 0
        
        return True, amount
    except:
        return False, 0
