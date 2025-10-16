"""
Create sample Excel data for testing the VC Firm Filter
"""

import pandas as pd

def create_sample_firms():
    """Create sample firm data for testing"""
    sample_data = {
        'name': [
            'TechCorp AI', 'HealthTech Solutions', 'FinTech Pro', 'GreenEnergy Inc',
            'EdTech Startup', 'RetailAI', 'MedDevice Corp', 'CyberSec Ltd',
            'AgriTech Farms', 'LogisticsAI', 'RealEstate Pro', 'TravelTech',
            'FoodTech Innovations', 'SportsTech', 'GamingCorp', 'MusicAI'
        ],
        'description': [
            'AI-powered analytics platform for enterprise customers',
            'Healthcare AI solutions for patient diagnosis and treatment',
            'Digital banking and payment solutions for SMEs',
            'Renewable energy solutions and smart grid technology',
            'Online learning platform with AI tutoring capabilities',
            'AI-driven inventory management for retail chains',
            'Medical device manufacturing with IoT integration',
            'Cybersecurity solutions for enterprise and government',
            'Precision agriculture using AI and IoT sensors',
            'AI-powered logistics optimization and route planning',
            'PropTech solutions for real estate management',
            'Travel booking platform with AI recommendations',
            'Food delivery optimization using machine learning',
            'Sports analytics and performance tracking platform',
            'Mobile gaming studio with AI-powered features',
            'Music streaming platform with AI curation'
        ],
        'stage': [
            'Series A', 'Seed', 'Series B', 'Series A', 'Pre-seed', 'Series A',
            'Series B', 'Series A', 'Seed', 'Series A', 'Series B', 'Seed',
            'Series A', 'Pre-seed', 'Seed', 'Series B'
        ],
        'revenue': [
            '$2M ARR', 'Pre-revenue', '$5M ARR', '$1.5M ARR', 'Pre-revenue',
            '$3M ARR', '$8M ARR', '$2.5M ARR', 'Pre-revenue', '$4M ARR',
            '$6M ARR', 'Pre-revenue', '$1M ARR', 'Pre-revenue', 'Pre-revenue',
            '$7M ARR'
        ],
        'industry': [
            'Technology', 'Healthcare', 'Fintech', 'Clean Energy', 'Education',
            'Retail', 'Healthcare', 'Cybersecurity', 'Agriculture', 'Logistics',
            'Real Estate', 'Travel', 'Food & Beverage', 'Sports', 'Gaming',
            'Entertainment'
        ],
        'location': [
            'San Francisco, CA', 'Boston, MA', 'New York, NY', 'Austin, TX',
            'Seattle, WA', 'Chicago, IL', 'San Diego, CA', 'Washington, DC',
            'Denver, CO', 'Atlanta, GA', 'Los Angeles, CA', 'Miami, FL',
            'Portland, OR', 'Nashville, TN', 'Salt Lake City, UT', 'Phoenix, AZ'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    return df

if __name__ == "__main__":
    # Create and save sample data
    df = create_sample_firms()
    df.to_excel('sample_firms.xlsx', index=False)
    print("✅ Sample firms data created: sample_firms.xlsx")
    print(f"📊 Created {len(df)} sample firms")
    
    # Display sample
    print("\n📋 Sample data:")
    print(df.head())
