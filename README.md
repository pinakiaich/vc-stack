# 🎯 VC Firm Filter

A Streamlit application that filters venture capital firms based on AI-powered heuristics. Upload an Excel sheet with firm data, enter your criteria, and get the top 10 matching firms with detailed reasoning.

## 🚀 Features

- **Excel Upload**: Process firm data from Excel files
- **AI-Powered Filtering**: Use OpenAI GPT to analyze and rank firms
- **Heuristic-Based**: Enter custom criteria for firm selection
- **Colab Compatible**: Runs seamlessly in Google Colab
- **Modular Architecture**: Clean, maintainable code structure
- **Fallback Filtering**: Works even without API keys

## 📁 Project Structure

```
vc-stack/
├── streamlit_app.py          # Main Streamlit application (95 lines)
├── data_processor.py         # Excel processing module (95 lines)
├── ai_filter.py             # AI filtering logic (95 lines)
├── config.py                # Configuration management (95 lines)
├── colab_setup.py           # Google Colab setup script
├── requirements_colab.txt   # Colab-compatible dependencies
├── env_example.txt          # Environment variables template
├── backend/                 # FastAPI backend
│   └── app/
│       ├── main.py          # API endpoints
│       ├── models.py        # Database models
│       └── core/
│           └── db.py        # Database configuration
└── README.md               # This file
```

## 🛠️ Installation & Setup

### Local Development

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd vc-stack
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements_colab.txt
```

3. **Setup environment variables:**
```bash
cp env_example.txt .env
# Edit .env with your API keys
```

4. **Run the application:**
```bash
streamlit run streamlit_app.py
```

### Google Colab

1. **Upload files to Colab:**
   - Upload `streamlit_app.py`, `data_processor.py`, `ai_filter.py`, `config.py`

2. **Run setup cell:**
```python
# Install dependencies
!pip install streamlit pandas openpyxl openai google-generativeai numpy python-dotenv

# Set your API key
import os
os.environ['OPENAI_API_KEY'] = 'your_openai_api_key_here'
```

3. **Run the app:**
```bash
!streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

## 📊 Excel File Format

Your Excel file should contain these columns (case-insensitive):

| Column | Description | Example |
|--------|-------------|---------|
| `name` | Firm name | "TechCorp Inc" |
| `description` | Business description | "AI-powered analytics platform" |
| `stage` | Funding stage | "Series A", "Seed" |
| `revenue` | Revenue information | "$1M ARR", "Pre-revenue" |
| `industry` | Industry sector | "Healthcare", "Fintech" |
| `location` | Company location | "San Francisco, CA" |

## 🎯 Usage

1. **Upload Excel File**: Select your firm data file
2. **Enter Heuristics**: Describe what you're looking for:
   - "AI startups with >$1M revenue, Series A stage"
   - "B2B SaaS companies in healthcare"
   - "Early-stage fintech startups in Europe"
3. **Get Results**: View top 10 matching firms with scores and reasoning

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./local.db
MAX_FIRMS_BATCH=50
AI_MODEL=gpt-3.5-turbo
```

### API Keys

- **OpenAI**: Get from [platform.openai.com](https://platform.openai.com/api-keys)
- **Gemini**: Get from [makersuite.google.com](https://makersuite.google.com/app/apikey)

## 🏗️ Architecture

### Code Organization

- **streamlit_app.py**: Main UI and user interaction
- **data_processor.py**: Excel file handling and data cleaning
- **ai_filter.py**: AI-powered firm analysis and ranking
- **config.py**: Environment configuration and API key management

### Design Principles

- ✅ **No Fallbacks**: Each module has a single responsibility
- ✅ **Minimal Code**: Each file under 100 lines
- ✅ **Clean Code**: Clear naming and structure
- ✅ **Modular**: Independent, testable components
- ✅ **Least Lines**: Concise, efficient implementation

## 🧪 Testing

Test the application with sample data:

```python
import pandas as pd

# Create sample data
sample_data = {
    'name': ['TechCorp', 'HealthAI', 'FinTech Pro'],
    'description': ['AI platform', 'Healthcare AI', 'Financial services'],
    'stage': ['Series A', 'Seed', 'Series B'],
    'revenue': ['$1M ARR', 'Pre-revenue', '$5M ARR'],
    'industry': ['Technology', 'Healthcare', 'Fintech'],
    'location': ['San Francisco', 'Boston', 'New York']
}

df = pd.DataFrame(sample_data)
df.to_excel('sample_firms.xlsx', index=False)
```

## 🚀 Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Set environment variables in dashboard
4. Deploy

### Docker
```dockerfile
FROM python:3.9-slim
COPY requirements_colab.txt .
RUN pip install -r requirements_colab.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

## 📈 Backend API

The FastAPI backend provides:

- `GET /health` - Health check
- `POST /companies` - Create company
- `GET /companies` - List companies
- `POST /filter-results` - Save filter results

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the coding principles
4. Test thoroughly
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code documentation
3. Create an issue on GitHub

---

**Built with ❤️ following clean coding principles**
