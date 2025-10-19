# 🔍 Code Walkthrough - VC Firm Filter

This document explains each code block and its functionality in the VC Firm Filter application.

## 📁 File Structure Overview

```
vc-stack/
├── streamlit_app.py          # Main UI (95 lines)
├── data_processor.py         # Excel handling (95 lines) 
├── ai_filter.py             # AI filtering (95 lines)
├── config.py                # Configuration (95 lines)
├── backend/app/main.py       # API endpoints (66 lines)
├── backend/app/models.py     # Database models (25 lines)
└── backend/app/core/db.py    # Database config (9 lines)
```

## 🎯 streamlit_app.py - Main Application (95 lines)

### Purpose
Main Streamlit application that orchestrates the entire user experience.

### Key Blocks

```python
# Lines 1-11: Imports and Page Config
import streamlit as st
import pandas as pd
from data_processor import ExcelProcessor
from ai_filter import AIFilter
from config import Config

st.set_page_config(
    page_title="VC Firm Filter",
    page_icon="🎯",
    layout="wide"
)
```
**What it does**: Imports all modules and sets up the Streamlit page configuration.

```python
# Lines 13-25: Main Function Setup
def main():
    st.title("🎯 VC Firm Filter")
    st.markdown("Upload Excel sheet with firms and enter heuristics to filter top 10 matches")
    
    # Initialize components
    config = Config()
    
    # Setup API keys if needed
    if not config.setup_api_keys_ui():
        st.stop()
    
    processor = ExcelProcessor()
    ai_filter = AIFilter(config)
```
**What it does**: Initializes all components and ensures API keys are configured before proceeding.

```python
# Lines 27-35: File Upload UI
uploaded_file = st.file_uploader(
    "Upload Excel file with firms data",
    type=['xlsx', 'xls'],
    help="Excel file should contain firm information"
)
```
**What it does**: Creates the file upload widget for Excel files.

```python
# Lines 37-45: Data Processing
if uploaded_file is not None:
    try:
        # Process Excel file
        df = processor.process_excel(uploaded_file)
        st.success(f"✅ Loaded {len(df)} firms from Excel")
        
        # Display sample data
        with st.expander("📊 Sample Data"):
            st.dataframe(df.head())
```
**What it does**: Processes the uploaded Excel file and displays success message with sample data preview.

```python
# Lines 47-58: Heuristics Input
st.subheader("🎯 Enter Filtering Heuristics")
heuristics = st.text_area(
    "Describe what you're looking for in firms:",
    placeholder="e.g., 'Looking for AI/ML startups with revenue >$1M, Series A stage, B2B focus'",
    height=100
)
```
**What it does**: Creates a text area for users to enter their filtering criteria.

```python
# Lines 60-78: Filtering and Results
if st.button("🔍 Filter Top 10 Firms", type="primary"):
    if heuristics.strip():
        with st.spinner("Analyzing firms..."):
            results = ai_filter.filter_firms(df, heuristics)
            
            st.subheader("🏆 Top 10 Matching Firms")
            for i, firm in enumerate(results, 1):
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{i}. {firm['name']}**")
                        st.markdown(f"📋 **Reason:** {firm['reason']}")
                    with col2:
                        st.markdown(f"**Score: {firm['score']:.1f}%**")
                    st.divider()
```
**What it does**: Handles the filtering process and displays results in a formatted layout with scores and reasons.

## 📊 data_processor.py - Excel Processing (95 lines)

### Purpose
Handles Excel file processing, data cleaning, and validation.

### Key Blocks

```python
# Lines 8-23: Excel Processing Method
def process_excel(self, uploaded_file) -> pd.DataFrame:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        # Clean and validate data
        df = self._clean_data(df)
        df = self._add_missing_columns(df)
        
        return df
```
**What it does**: Main entry point that reads Excel files and applies cleaning operations.

```python
# Lines 25-40: Data Cleaning
def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
    # Remove empty rows
    df = df.dropna(how='all')
    
    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()
    
    # Fill missing values
    df = df.fillna('')
    
    # Convert to string for consistency
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    return df
```
**What it does**: Standardizes column names, removes empty rows, and ensures consistent data types.

```python
# Lines 42-58: Missing Column Handling
def _add_missing_columns(self, df: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        'name': 'name',
        'description': 'description', 
        'stage': 'stage',
        'revenue': 'revenue',
        'industry': 'industry',
        'location': 'location'
    }
```
**What it does**: Ensures all required columns exist, mapping similar column names when possible.

## 🤖 ai_filter.py - AI Filtering (95 lines)

### Purpose
AI-powered firm filtering using OpenAI GPT to analyze and rank firms based on heuristics.

### Key Blocks

```python
# Lines 15-30: Main Filtering Method
def filter_firms(self, df: pd.DataFrame, heuristics: str, top_n: int = 10) -> List[Dict[str, Any]]:
    try:
        # Prepare firm data for AI analysis
        firm_data = self._prepare_firm_data(df)
        
        # Get AI analysis
        ai_results = self._analyze_with_ai(firm_data, heuristics)
        
        # Process and rank results
        ranked_firms = self._rank_firms(ai_results, top_n)
        
        return ranked_firms
```
**What it does**: Orchestrates the entire AI filtering process from data preparation to final ranking.

```python
# Lines 32-45: Data Preparation
def _prepare_firm_data(self, df: pd.DataFrame) -> List[Dict[str, str]]:
    firms = []
    
    for _, row in df.iterrows():
        firm = {
            'name': str(row.get('name', 'Unknown')),
            'description': str(row.get('description', 'No description')),
            'stage': str(row.get('stage', 'Unknown')),
            'revenue': str(row.get('revenue', 'Unknown')),
            'industry': str(row.get('industry', 'Unknown')),
            'location': str(row.get('location', 'Unknown'))
        }
        firms.append(firm)
    
    return firms
```
**What it does**: Converts DataFrame rows into structured dictionaries for AI processing.

```python
# Lines 47-60: AI Analysis
def _analyze_with_ai(self, firms: List[Dict], heuristics: str) -> List[Dict]:
    try:
        prompt = self._build_analysis_prompt(firms, heuristics)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        return self._parse_ai_response(result_text)
```
**What it does**: Sends firm data and heuristics to OpenAI GPT for analysis and scoring.

```python
# Lines 62-85: Prompt Building
def _build_analysis_prompt(self, firms: List[Dict], heuristics: str) -> str:
    firms_text = "\n".join([
        f"Name: {f['name']}\n"
        f"Description: {f['description']}\n"
        f"Stage: {f['stage']}\n"
        f"Revenue: {f['revenue']}\n"
        f"Industry: {f['industry']}\n"
        f"Location: {f['location']}\n---"
        for f in firms
    ])
    
    return f"""
    Analyze these firms based on the heuristics and rank them:
    
    HEURISTICS: {heuristics}
    
    FIRMS:
    {firms_text}
    
    For each firm, provide:
    1. Match score (0-100)
    2. Reason for the score
    
    Return as JSON array with format:
    [{{"name": "firm_name", "score": 85, "reason": "explanation"}}]
    """
```
**What it does**: Constructs a detailed prompt for the AI with firm data and user heuristics.

## ⚙️ config.py - Configuration Management (95 lines)

### Purpose
Manages environment variables, API keys, and application configuration.

### Key Blocks

```python
# Lines 8-18: Environment Setup
def _setup_environment(self):
    # Set default logging level
    logging.basicConfig(level=logging.INFO)
    
    # Configure Streamlit secrets
    if hasattr(st, 'secrets'):
        self._load_streamlit_secrets()
```
**What it does**: Initializes logging and loads Streamlit secrets if available.

```python
# Lines 20-32: API Key Management
def get_openai_key(self) -> Optional[str]:
    # Priority order: env var > streamlit secrets > user input
    key = os.getenv('OPENAI_API_KEY')
    
    if not key and hasattr(self, 'openai_key') and self.openai_key:
        key = self.openai_key
    
    if not key:
        # Fallback to session state for user input
        key = st.session_state.get('openai_key')
    
    return key
```
**What it does**: Retrieves OpenAI API key from multiple sources with priority order.

```python
# Lines 47-65: API Key UI Setup
def setup_api_keys_ui(self) -> bool:
    openai_key = self.get_openai_key()
    
    if not openai_key:
        with st.sidebar:
            st.markdown("### 🔑 API Configuration")
            st.markdown("Enter your OpenAI API key to use AI filtering:")
            
            openai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="Get your key from https://platform.openai.com/api-keys"
            )
            
            if openai_key:
                st.session_state['openai_key'] = openai_key
                st.success("✅ API key saved!")
                return True
            else:
                st.warning("⚠️ API key required for AI filtering")
                return False
    
    return True
```
**What it does**: Creates a UI for users to input API keys when not available in environment.

## 🗄️ backend/app/models.py - Database Models (25 lines)

### Purpose
Defines SQLAlchemy models for storing company and filter result data.

### Key Blocks

```python
# Lines 5-15: Company Model
class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text)
    stage = Column(String(100))
    revenue = Column(String(100))
    industry = Column(String(100))
    location = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```
**What it does**: Defines the Company table structure with all firm-related fields.

```python
# Lines 17-24: Filter Result Model
class FilterResult(Base):
    __tablename__ = "filter_result"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, nullable=False)
    heuristics = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```
**What it does**: Defines the FilterResult table to store filtering history and results.

## 🚀 backend/app/main.py - API Endpoints (66 lines)

### Purpose
FastAPI backend providing REST endpoints for company and filter result management.

### Key Blocks

```python
# Lines 47-53: Company Creation
@app.post("/companies", response_model=CompanyOut)
def create_company(item: CompanyIn, db=Depends(get_db)):
    c = Company(**item.dict())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c
```
**What it does**: Creates new company records in the database.

```python
# Lines 59-65: Filter Result Saving
@app.post("/filter-results")
def save_filter_result(item: FilterResultIn, db=Depends(get_db)):
    result = FilterResult(**item.dict())
    db.add(result)
    db.commit()
    db.refresh(result)
    return {"id": result.id, "message": "Filter result saved"}
```
**What it does**: Saves filter results for historical tracking and analysis.

## 🔄 Data Flow

1. **Upload**: User uploads Excel file via Streamlit UI
2. **Process**: `data_processor.py` cleans and standardizes data
3. **Configure**: `config.py` manages API keys and settings
4. **Filter**: `ai_filter.py` sends data to OpenAI for analysis
5. **Display**: Results shown in Streamlit UI
6. **Store**: Optional backend storage via FastAPI

## 🎯 Modular Design Benefits

- **Single Responsibility**: Each file has one clear purpose
- **Easy Testing**: Components can be tested independently
- **Maintainable**: Changes in one module don't affect others
- **Reusable**: Components can be used in other projects
- **Scalable**: Easy to add new features or modify existing ones

## 🚀 Deployment Flow

1. **Local**: Run `streamlit run streamlit_app.py`
2. **Colab**: Upload files and run setup script
3. **Cloud**: Deploy to Streamlit Cloud or Docker
4. **Backend**: Optional FastAPI deployment for data persistence

