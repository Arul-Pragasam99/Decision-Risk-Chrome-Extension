"""Background analysis runner for local development and testing.

This file is for local testing and prototyping only.
For the Chrome extension, all runtime logic is in JavaScript.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from ai_models.price_risk_model import estimate_price_history, price_risk_score
from ai_models.resale_value_model import predict_resale_value, extract_brand
from ai_models.subscription_detector import analyze_subscription_risk, find_subscription_terms
from ai_models.dark_pattern_detector import detect_dark_patterns, analyze_checkout_manipulation


def analyze_product_page(title: str, price: float, page_text: str, category: str = 'default'):
    """Analyze a product page and return risk assessments."""
    
    # Price risk analysis
    history = estimate_price_history(price)
    price_risk = price_risk_score(history)
    
    # Resale value prediction
    brand = extract_brand(title)
    resale = predict_resale_value(title, price, category)
    
    # Subscription detection
    subscription_terms = find_subscription_terms(page_text)
    subscription_risk = analyze_subscription_risk(page_text)
    
    # Dark pattern detection
    dark_patterns = detect_dark_patterns(page_text)
    checkout_manipulation = analyze_checkout_manipulation(page_text)
    
    return {
        'product': {
            'title': title,
            'price': price,
            'category': category,
            'brand': brand
        },
        'price_risk': {
            'score': price_risk.score,
            'level': price_risk.risk_level,
            'recommendation': price_risk.recommendation,
            'details': price_risk.details
        },
        'resale_value': {
            'score': resale.score,
            'level': resale.risk_level,
            'retention_rate': resale.retention_rate,
            'estimated_value': resale.estimated_value,
            'recommendation': resale.recommendation
        },
        'subscription': {
            'risk_level': subscription_risk['risk_level'],
            'score': subscription_risk['score'],
            'has_trial': subscription_risk['has_trial'],
            'auto_renewal': subscription_risk['auto_renewal'],
            'found_terms': subscription_risk['found_terms'],
            'recommendation': subscription_risk['recommendation']
        },
        'dark_patterns': {
            'patterns': dark_patterns,
            'checkout_manipulation': checkout_manipulation,
            'count': len(dark_patterns)
        }
    }


def print_analysis(analysis: dict):
    """Pretty print analysis results."""
    print("\n" + "="*60)
    print(f"📦 PRODUCT ANALYSIS")
    print("="*60)
    
    prod = analysis['product']
    print(f"\n📱 Product: {prod['title']}")
    print(f"💰 Price: ₹{prod['price']:,.2f}")
    print(f"📂 Category: {prod['category']}")
    print(f"🏷️  Brand: {prod['brand']}")
    
    print("\n" + "-"*60)
    print("📊 RISK ASSESSMENTS")
    print("-"*60)
    
    price = analysis['price_risk']
    print(f"\n💵 PRICE RISK: {price['level']}")
    print(f"   Score: {price['score']:.2f}")
    print(f"   {price['recommendation']}")
    print(f"   {price['details']}")
    
    resale = analysis['resale_value']
    print(f"\n📈 RESALE VALUE: {resale['level']} RISK")
    print(f"   Score: {resale['score']:.2f}")
    print(f"   Retention: {resale['retention_rate']*100:.1f}% after 1 year")
    print(f"   Est. value: ₹{resale['estimated_value']:,.2f}")
    print(f"   {resale['recommendation']}")
    
    sub = analysis['subscription']
    print(f"\n🔄 SUBSCRIPTION RISK: {sub['risk_level']}")
    print(f"   Score: {sub['score']:.2f}")
    print(f"   Trial: {'⚠️ Yes' if sub['has_trial'] else '✅ No'}")
    print(f"   Auto-renewal: {'⚠️ Yes' if sub['auto_renewal'] else '✅ No'}")
    if sub['found_terms']:
        print(f"   Terms found: {', '.join(sub['found_terms'][:3])}")
    print(f"   {sub['recommendation']}")
    
    patterns = analysis['dark_patterns']
    print(f"\n🎭 DARK PATTERNS: {patterns['count']} detected")
    if patterns['patterns']:
        for pattern in patterns['patterns']:
            print(f"   • {pattern}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    # Test cases
    
    # Test 1: Electronics product with subscription
    print("\n🔍 TEST CASE 1: Smartphone with subscription offer")
    sample_title = "Samsung Galaxy M32 5G (128GB)"
    sample_price = 18999.0
    sample_text = """
    Limited time offer! Buy now at just ₹18,999. Free 3-month subscription to Samsung Premium 
    included (auto-renews at ₹299/month after trial). Only 5 units left! Hurry! 
    EMI options available. Free shipping on orders above ₹499.
    """
    result = analyze_product_page(sample_title, sample_price, sample_text, 'mobile')
    print_analysis(result)
    
    # Test 2: Fashion item
    print("\n🔍 TEST CASE 2: Fashion item")
    sample_title = "Levi's Men's Slim Fit Jeans"
    sample_price = 2499.0
    sample_text = """
    End of season sale! 40% off on select styles. Limited sizes available. 
    Buy 2 get 10% off. Free shipping on orders above ₹999. Easy returns.
    """
    result = analyze_product_page(sample_title, sample_price, sample_text, 'fashion')
    print_analysis(result)
    
    # Test 3: Subscription service
    print("\n🔍 TEST CASE 3: Streaming service")
    sample_title = "Premium Video Streaming - Annual Plan"
    sample_price = 999.0
    sample_text = """
    Start your 7-day free trial today! After trial, ₹999/year. Auto-renews annually. 
    Cancel anytime before renewal. Payment method required for trial. 
    Limited time offer: Get 3 months free with annual subscription!
    """
    result = analyze_product_page(sample_title, sample_price, sample_text, 'default')
    print_analysis(result)