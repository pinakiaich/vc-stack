# 🔍 Form Auto-Fill Debugging Guide

## Issue: Stage Field Not Filling

The form is now enhanced with better debugging to help identify why stage might not be filling.

## What Was Added

### 1. Enhanced Stage Extraction
- **More robust column detection**: Checks for columns containing 'stage', 'round', 'series', 'funding', 'financing', 'capital'
- **Better value validation**: Filters out 'nan', 'none', 'n/a', 'null', 'undefined'
- **Improved normalization**: Handles variations like "Series A", "SeriesA", "series a", etc.
- **Logging**: Logs when stage is found and which column it came from

### 2. UI Feedback
When you click a company name, you'll now see:
- ✅ **Success message**: Shows what was extracted (e.g., "Extracted from Excel: sector, stage")
- ⚠️ **Warning if stage missing**: Shows which Excel columns might contain stage data
- 📊 **Debug info**: Shows extracted stage value in the form

### 3. Form-Level Debugging
In the form itself:
- Shows "✅ Stage auto-filled: [value]" if stage was found
- Shows "⚠️ Stage not found in Excel" if stage is missing

## How to Debug

### Step 1: Check What Was Extracted
When you click a company name, look for:
- Green success message showing extracted fields
- Warning message if stage is missing
- List of columns that might contain stage

### Step 2: Check Excel Column Names
The agent looks for columns containing these keywords:
- `stage`
- `round`
- `series`
- `funding`
- `financing`
- `capital`

**Common Excel column names that should work:**
- "Stage"
- "Funding Stage"
- "Round"
- "Series"
- "Investment Stage"
- "Capital Stage"

### Step 3: Check Excel Data
Make sure:
1. The Excel sheet has a column with stage information
2. The column name contains one of the keywords above
3. The cell for that company has a value (not empty)

### Step 4: Check Terminal/Logs
The agent logs:
- When stage is found: `Found stage 'Series A' in column 'stage'`
- When stage is missing: `Stage not found. Available columns: [...]`

## Common Issues & Solutions

### Issue 1: Column Name Doesn't Match
**Problem**: Excel column is named "Funding Round" but agent looks for "funding stage"

**Solution**: The agent now checks for ANY column containing keywords like 'stage', 'round', 'series', 'funding'. It should find it automatically.

### Issue 2: Stage Value is Empty
**Problem**: Excel has a stage column but the cell is empty for that company

**Solution**: The agent will show a warning. You'll need to manually enter the stage in the form.

### Issue 3: Stage Value Format
**Problem**: Excel has "SeriesA" but agent expects "Series A"

**Solution**: The normalization now handles variations like "SeriesA", "series a", "SERIES A", etc.

## Testing

1. **Upload Excel** with a "Stage" or "Funding Stage" column
2. **Filter companies** → Get top 10
3. **Click a company name** → 
   - Should see extraction message
   - Should see stage value if found
   - Should see warning if not found
4. **Check form** → Stage field should be filled

## If Stage Still Not Filling

1. **Check the extraction message**: Does it say "Extracted from Excel: sector, stage" or just "sector"?
2. **Check the warning**: What columns does it suggest?
3. **Check terminal logs**: What does the agent log say?
4. **Check Excel**: Does the company row actually have a stage value?

The enhanced debugging should help identify exactly where the issue is! 🔍
