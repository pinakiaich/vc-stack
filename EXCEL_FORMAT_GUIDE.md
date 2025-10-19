# 📊 Excel File Format Guide

## Your Issue: Metadata Rows Being Read as Company Names

### What Happened
Your Excel file has metadata rows at the top (like "Downloaded on:", "Created for:", "Search Link:", etc.) that were being read as company data.

### ✅ Fixed!
The app now:
1. **Auto-detects** metadata rows and skips them
2. **Removes** rows that look like metadata or IDs
3. **Validates** that data looks like actual companies
4. **Warns** you if something looks wrong

---

## 🎯 Ideal Excel Format

Your Excel file should have:

### Row 1: Column Headers
```
| Company Name | Description | Industry | Stage | Revenue | Valuation | Investors | Location |
```

### Row 2+: Company Data
```
| Acme AI Corp | Enterprise AI platform... | Artificial Intelligence | Series B | $10M ARR | $250M | Sequoia, a16z | San Francisco |
| TechCo Inc   | Machine learning SaaS...  | AI/ML                   | Series C | $15M ARR | $300M | Accel, GV    | New York      |
```

---

## 🚫 Common Problems & Solutions

### Problem 1: Metadata Rows at Top

**Your file looks like:**
```
Downloaded on: 2024-10-19
Created for: John Doe
Search Link: https://...
Search Criteria: AI companies

Company Name | Description | Industry | ...
Acme AI Corp | Enterprise... | AI       | ...
```

**Solution:** 
✅ **The app now auto-removes these!** Just re-upload your file.

If auto-detection doesn't work:
1. Open "⚙️ Advanced: Skip metadata rows"
2. Count how many metadata rows are at the top (e.g., 4 rows)
3. Enter that number
4. Re-process

---

### Problem 2: ID Numbers as Company Names

**Your results show:**
```
1. 466959-97
2. 59199-40
3. 63690-94
```

**This means:**
- These are company IDs, not names
- The "Company Name" column might be missing
- Or IDs are in the first column

**Solution:**
1. Open your Excel file
2. Make sure "Company Name" or "Name" is the **first column**
3. If you have an ID column, move it to the right
4. Re-upload

**Or manually fix in Excel:**
- Delete the ID column, OR
- Move company names to the first column

---

### Problem 3: Wrong Column Order

**App expects this order (flexible, but helpful):**
```
Name → Description → Industry → Stage → Revenue → Valuation → Investors → Location
```

**Your file might have:**
```
ID → Search Link → Company Name → Description → ...
```

**Solution:**
1. Re-arrange columns in Excel
2. Put "Company Name" or "Name" as **first column**
3. Put important fields (Description, Industry) early
4. Re-upload

---

## 🔧 Using the "Skip Rows" Feature

### When to Use:
- You see metadata like "Downloaded on:" in results
- Company IDs show up as names
- First few results don't look like companies

### How to Use:

1. **Click "⚙️ Advanced: Skip metadata rows"**

2. **Count metadata rows in your Excel:**
   - Open your Excel file
   - Count rows before the actual header row
   - Example:
     ```
     Row 1: Downloaded on: 2024-10-19    ← metadata
     Row 2: Created for: User            ← metadata  
     Row 3: (empty)                      ← metadata
     Row 4: Company Name | Description   ← THIS IS THE HEADER
     Row 5: Acme Corp | AI platform      ← actual data
     ```
   - In this example, skip **3 rows** (rows 1-3)

3. **Enter the number** in "Number of rows to skip"

4. **Re-process** - Upload button will reset, upload again

---

## ✨ New Auto-Detection Features

The app now automatically:

### 1. Finds Header Row
- Searches for rows with keywords: "name", "company", "firm", "description"
- Skips rows with: "downloaded", "created", "search", "criteria"

### 2. Removes Metadata Rows
- Filters out rows like "Downloaded on:", "Created for:"
- Removes rows with ID patterns (e.g., "466959-97")
- Removes very short names (< 3 characters)

### 3. Validates Data
- Checks if data looks like company names
- Warns if something seems wrong
- Shows data quality metrics

---

## 📋 Checklist: Preparing Your Excel File

Before uploading:

- [ ] First row has column headers (Name, Description, etc.)
- [ ] Company names are in the first column
- [ ] No metadata rows at the top (or you know how many to skip)
- [ ] No completely empty rows in the middle
- [ ] At least these columns exist:
  - [ ] Name/Company Name
  - [ ] Description
  - [ ] Industry
  - [ ] Stage (e.g., Series A, Series B)
  - [ ] Revenue (e.g., $5M ARR)

**Nice to have:**
- [ ] Valuation
- [ ] Investors/VC names
- [ ] Location
- [ ] Website URL

---

## 🎯 Quick Fix for Your Current File

Based on your error, your Excel file likely looks like this:

```excel
Row 1: Downloaded on: [date]
Row 2: Created for: [name]  
Row 3: Search Link: [url]
Row 4: Search Criteria: [criteria]
Row 5: 
Row 6: Company ID | Company Name | Description | Industry | ...
Row 7: 466959-97 | Acme AI      | AI platform | AI       | ...
Row 8: 59199-40  | TechCo       | ML SaaS     | ML       | ...
```

**Two options:**

### Option A: Let Auto-Detection Work (Recommended)
1. Just re-upload your file
2. The new code should auto-skip rows 1-6
3. Check "📊 View Uploaded Data" to verify

### Option B: Manual Skip (If Option A fails)
1. Click "⚙️ Advanced: Skip metadata rows"
2. Enter **6** (skip first 6 rows)
3. Upload your file
4. Check results

### Option C: Clean Excel File (Best for reusability)
1. Open Excel file
2. Delete rows 1-5 (metadata rows)
3. Delete "Company ID" column (or move it to the end)
4. Make sure Row 1 has: `Company Name | Description | Industry | Stage | Revenue | ...`
5. Save and re-upload

---

## 🔍 Verifying Your Data

After uploading, **always check**:

1. **Click "📊 View Uploaded Data"**

2. **Look at "First 5 rows":**
   - Do these look like real company names?
   - Is the data in the right columns?

3. **Check "Data Summary":**
   - Does "Total Firms" make sense?
   - Do you have descriptions and industries?

4. **Review "Available Columns":**
   - Are all your columns listed?
   - Are column names correct?

---

## 💡 Pro Tips

### Tip 1: Use Descriptive Column Names
- ✅ Good: "Company Name", "Business Description", "Funding Stage"
- ❌ Bad: "Col1", "Field2", "Data3"

### Tip 2: Fill in Key Fields
Fillthese for best results:
- **Description**: Rich text about the company (most important!)
- **Industry**: Specific industry/sector
- **Revenue**: Actual numbers with currency
- **Stage**: Series A, B, C, Seed, etc.

### Tip 3: Remove Extra Sheets
- Keep only one sheet with company data
- Delete or hide summary/metadata sheets

### Tip 4: Test with Small Sample
- Try with 10-20 companies first
- Verify it works correctly
- Then upload full list

---

## 📞 Still Having Issues?

### Check These:

1. **File Format:**
   - Is it really .xlsx or .xls?
   - Not .csv renamed to .xlsx?

2. **Data Quality:**
   - Are company names present?
   - Is there actual text in Description?
   - Are columns labeled?

3. **File Size:**
   - Files with 1000s of companies might be slow
   - Try a smaller sample first

4. **Excel Versions:**
   - Modern Excel formats work best
   - If very old file, try opening and re-saving

### Debug Mode:

1. Upload file
2. Check "📊 View Uploaded Data"
3. Look at what actually loaded
4. Adjust "Skip rows" if needed
5. Try again

---

## 🎉 Summary

**Before:**
- Metadata rows were read as companies
- IDs showed up as company names  
- No way to skip problem rows

**Now:**
- ✅ Auto-detects and skips metadata
- ✅ Removes ID-only rows
- ✅ Manual skip option available
- ✅ Validates data quality
- ✅ Shows warnings if something's wrong

**Just re-upload your file and it should work!** 🚀

---

## Example: Good Excel File

```excel
| Company Name         | Description                                      | Industry      | Stage    | Revenue  | Valuation | Investors           |
|---------------------|--------------------------------------------------|---------------|----------|----------|-----------|---------------------|
| Acme AI Corp        | Enterprise AI platform for data analytics B2B    | AI/ML         | Series B | $10M ARR | $250M     | Sequoia, a16z       |
| TechVision Inc      | Computer vision AI for manufacturing B2B         | AI            | Series C | $15M ARR | $320M     | Accel, Google GV    |
| DataSmart Solutions | B2B machine learning SaaS for enterprises        | ML/SaaS       | Series B | $8M ARR  | $200M     | Intel Capital, NEA  |
```

This format will give you the **best results**! 💯

