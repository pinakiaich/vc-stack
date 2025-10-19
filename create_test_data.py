"""
Create sample test data for VC Stack testing
Run: python create_test_data.py
"""
import pandas as pd

# Create sample firm data
data = {
    'name': [
        'TechCorp AI', 
        'HealthVentures', 
        'FinTech Solutions', 
        'DataAnalytics Co', 
        'CloudServices Inc', 
        'AI Robotics', 
        'MedTech Innovations', 
        'CryptoExchange', 
        'SmartDevices Ltd', 
        'BioTech Labs'
    ],
    'description': [
        'AI-powered analytics platform for enterprise clients with machine learning',
        'Healthcare technology and telemedicine solutions for patients',
        'Financial services and payment processing for businesses',
        'Big data analytics and visualization tools for enterprises',
        'Cloud infrastructure and hosting services for startups',
        'Robotics and automation using artificial intelligence',
        'Medical devices and healthcare software for hospitals',
        'Cryptocurrency trading and blockchain services',
        'IoT devices and smart home technology',
        'Biotechnology research and drug development'
    ],
    'stage': [
        'Series A', 'Seed', 'Series B', 'Series A', 'Series C',
        'Seed', 'Series A', 'Series B', 'Seed', 'Series A'
    ],
    'revenue': [
        '2M ARR', 'Pre-revenue', '5M ARR', '1.5M ARR', '10M ARR',
        'Pre-revenue', '3M ARR', '8M ARR', '500K ARR', '4M ARR'
    ],
    'industry': [
        'Technology', 'Healthcare', 'Fintech', 'Technology', 'Technology',
        'AI/Robotics', 'Healthcare', 'Fintech', 'IoT', 'Biotech'
    ],
    'location': [
        'San Francisco', 'Boston', 'New York', 'Austin', 'Seattle',
        'San Francisco', 'Boston', 'Miami', 'Los Angeles', 'San Diego'
    ]
}

df = pd.DataFrame(data)
filename = 'test_firms.xlsx'
df.to_excel(filename, index=False)

print(f"✅ Successfully created {filename}")
print(f"📊 Total firms: {len(df)}")
print(f"📝 Columns: {', '.join(df.columns)}")
print(f"\n💡 Test searches:")
print("   - 'AI technology' (should match AI-related firms)")
print("   - 'Healthcare Boston' (should match healthcare in Boston)")
print("   - 'Series A revenue' (should match Series A firms)")
print("   - 'Fintech' (should match financial tech firms)")

