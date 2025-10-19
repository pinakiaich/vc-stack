# VC Stack - Quick Start Guide

## 🚀 Getting Started

### 1. Install Dependencies

```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
pip install streamlit pandas openpyxl openai numpy python-dotenv
```

### 2. Run the Application

```bash
streamlit run streamlit_app.py
```

## 🔑 Using the Application

### Step 1: Enter Your OpenAI API Key

When you first open the app, you'll see a prominent API key input section at the top:

1. **Enter your OpenAI API Key** in the text field
2. **Click "Save API Key"** button
3. ✅ You'll see a success message when saved

**Where to get your API key:**
- Visit: https://platform.openai.com/api-keys
- Sign up/Login to OpenAI
- Create a new API key
- Copy and paste it into the app

**Note:** Your API key is only stored in your browser session and never shared.

### Step 2: Upload Your Excel File

1. Click **"Browse files"** or drag & drop your Excel file
2. Supported formats: `.xlsx`, `.xls`
3. The app will show a success message with the number of firms loaded

**Required Excel Columns:**
- `name` - Company/firm name
- `description` - Business description
- `stage` - Funding stage (e.g., "Series A", "Seed")
- `revenue` - Revenue information
- `industry` - Industry sector
- `location` - Company location

### Step 3: Enter Your Filtering Heuristics

Describe what you're looking for in the text area. Examples:

```
"AI/ML startups with revenue >$1M, Series A stage, B2B focus"
"Healthcare companies in early stage with presence in California"
"Fintech startups with $500K+ revenue, seed to Series A"
```

### Step 4: Get Results

1. Click **"🔍 Filter Top 10 Firms"**
2. Wait for AI analysis (usually 5-10 seconds)
3. View the top 10 matching firms with:
   - Match score (0-100%)
   - Detailed reasoning for each match

## 🎯 Features

### AI-Powered Filtering (with API Key)
- Uses GPT-3.5-turbo for intelligent analysis
- Understands natural language criteria
- Provides detailed reasoning for each match
- Highly accurate matching

### Fallback Mode (without API Key)
- Basic keyword matching
- Works without internet connection
- No API costs
- Good for simple filtering

### Seamless Experience
- Upload files before entering API key
- Change API key anytime
- Clear status indicators
- Helpful error messages

## 💡 Tips

1. **Be Specific:** More detailed heuristics = better results
2. **Use Numbers:** Include revenue thresholds, stages, etc.
3. **Mention Industries:** Specific industries help narrow down matches
4. **Location Matters:** Include geographic preferences if important
5. **Test First:** Try with sample data to understand the format

## ❓ Troubleshooting

### "Invalid API key format"
- Make sure your key starts with `sk-`
- Copy the entire key without spaces
- Generate a new key if needed

### "No matching firms found"
- Try broader heuristics
- Check your Excel file has the required columns
- Verify data quality in Excel file

### File Upload Issues
- Check file format is `.xlsx` or `.xls`
- Ensure file isn't corrupted
- Try with a smaller file first

## 📊 Sample Excel File

Create a test file with this structure:

| name | description | stage | revenue | industry | location |
|------|-------------|-------|---------|----------|----------|
| TechCorp | AI analytics platform | Series A | $2M ARR | Technology | San Francisco |
| HealthAI | Healthcare AI solutions | Seed | Pre-revenue | Healthcare | Boston |
| FinPro | Financial services platform | Series B | $5M ARR | Fintech | New York |

## 🔐 Security

- API keys are stored in browser session only
- Keys are never logged or transmitted elsewhere
- Session data clears when you close the browser
- Safe to use with sensitive data

## 🆘 Need Help?

1. Check the sidebar instructions in the app
2. Review this guide
3. Check the main README.md for detailed documentation
4. Verify your API key is valid and has credits

---

**Enjoy using VC Stack! 🎯**

