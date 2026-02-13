"""
Smart NLP Parser - Extract transaction data from natural language
Handles: "Makan siang 50rb di soto lamongan", "Gaji 5jt", "Bensin 100k"
"""
import re
from typing import Optional, Dict

class TransactionParser:
    """Parse natural language transaction input"""
    
    # Regex patterns untuk amount
    AMOUNT_PATTERNS = [
        r'(\d+(?:[.,]\d+)?)\s*(?:jt|juta|million)',  # 5jt, 5.5juta
        r'(\d+(?:[.,]\d+)?)\s*(?:rb|ribu|k)',         # 50rb, 50k
        r'(\d+(?:[.,]\d+)?)\s*(?:rp|rupiah)',         # 50000rp
        r'(\d{1,3}(?:[.,]\d{3})*)',                   # 50.000, 50,000
    ]
    
    # Category keywords mapping
    CATEGORY_KEYWORDS = {
        'Makan': ['makan', 'lunch', 'dinner', 'breakfast', 'sarapan', 'siang', 'malam', 'nasi', 'soto', 'bakso', 'ayam'],
        'Transport': ['bensin', 'grab', 'gojek', 'taxi', 'ojek', 'parkir', 'tol', 'transport'],
        'Belanja': ['belanja', 'beli', 'shopping', 'tokopedia', 'shopee', 'lazada'],
        'Tagihan': ['listrik', 'air', 'internet', 'wifi', 'pulsa', 'token', 'pln', 'tagihan'],
        'Hiburan': ['nonton', 'cinema', 'game', 'spotify', 'netflix', 'hiburan'],
        'Kesehatan': ['dokter', 'obat', 'rumah sakit', 'apotek', 'kesehatan'],
        'Gaji': ['gaji', 'salary', 'income', 'pendapatan'],
        'Investasi': ['investasi', 'saham', 'crypto', 'reksadana'],
        'Lainnya': []  # Default fallback
    }
    
    @classmethod
    def parse_transaction(cls, text: str) -> Optional[Dict]:
        """
        Parse transaction from natural language
        
        Returns:
            {
                'amount': float,
                'category': str,
                'description': str
            }
        """
        if not text or len(text.strip()) < 3:
            return None
        
        text_lower = text.lower().strip()
        
        # Extract amount
        amount = cls._extract_amount(text_lower)
        if not amount:
            return None
        
        # Extract category
        category = cls._extract_category(text_lower)
        
        # Clean description (remove amount part)
        description = cls._clean_description(text, amount)
        
        return {
            'amount': amount,
            'category': category,
            'description': description
        }
    
    @classmethod
    def _extract_amount(cls, text: str) -> Optional[float]:
        """Extract amount from text"""
        for pattern in cls.AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '.')
                amount = float(amount_str)
                
                # Handle multipliers
                if 'jt' in text or 'juta' in text or 'million' in text:
                    amount *= 1_000_000
                elif 'rb' in text or 'ribu' in text or 'k' in text:
                    amount *= 1_000
                
                return amount
        
        return None
    
    @classmethod
    def _extract_category(cls, text: str) -> str:
        """Extract category based on keywords"""
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'Lainnya'
    
    @classmethod
    def _clean_description(cls, original_text: str, amount: float) -> str:
        """Clean description by removing amount patterns"""
        # Remove amount patterns
        cleaned = original_text
        for pattern in cls.AMOUNT_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove common words
        cleaned = re.sub(r'\b(jt|juta|rb|ribu|rp|rupiah|k)\b', '', cleaned, flags=re.IGNORECASE)
        
        # Clean whitespace
        cleaned = ' '.join(cleaned.split()).strip()
        
        return cleaned if cleaned else f"Transaksi {amount}"

# Convenience function
def parse_transaction(text: str) -> Optional[Dict]:
    """Parse transaction from text"""
    return TransactionParser.parse_transaction(text)
