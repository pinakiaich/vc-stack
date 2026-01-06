# ✅ Table Persistence & Auto-Fill Fix

## Critical Issues Fixed

### 1. ✅ Table Disappearing When Clicking Firm Name
**Problem:** Results table disappeared after clicking a firm name button.

**Root Cause:** 
- `st.rerun()` was called immediately after button click
- Results were not properly stored in session state before rerun
- DataFrame was not stored, so `get_company_data_from_df` couldn't access Excel data after rerun

**Solution:**
- **Store results BEFORE button click:** Results stored in `st.session_state['filter_results']` when filtering completes
- **Store DataFrame:** `st.session_state['filter_df']` stores the Excel DataFrame for data lookup
- **Always use stored results:** `display_results = st.session_state.get('filter_results', results)` ensures table always shows
- **Use stored DataFrame:** `display_df = st.session_state.get('filter_df', df)` for company data lookup

**Key Changes:**
```python
# Store results AND DataFrame when filtering
st.session_state['filter_results'] = results
st.session_state['filter_df'] = df

# Always use stored results for display
display_results = st.session_state.get('filter_results', results)
display_df = st.session_state.get('filter_df', df)
```

### 2. ✅ Firm Name Not Auto-Filling in Sidebar Form
**Problem:** Clicking firm name didn't populate the "Deal Name" field in sidebar.

**Root Cause:**
- Streamlit forms cache their initial values
- Form key wasn't changing properly when firm changed
- Form values read before `selected_firm` was set in session state

**Solution:**
- **Unique form key per firm:** `form_key = f"create_deal_form_{firm_name_for_key}"` changes when firm changes
- **Read session state INSIDE form:** `current_selected = st.session_state.get('selected_firm', {})` reads fresh value
- **Unique input keys:** Each input has unique key based on firm name to force update
- **Clear form submission flags:** Clears flags when new firm is selected to allow re-render
- **Rerun after selection:** `st.rerun()` after setting `selected_firm` to update form

**Key Changes:**
```python
# Read selected firm INSIDE form (after rerun)
current_selected = st.session_state.get('selected_firm', {})

# Use firm name in form key to force re-render
form_key = f"create_deal_form_{firm_name_for_key}"

# Unique keys for each input
deal_name = st.text_input("Deal Name *", value=default_name, key=f"deal_name_input_{firm_name_for_key}")
```

## How It Works Now

### Workflow:
1. **Filter Companies** → Results stored in `filter_results` and `filter_df` in session state
2. **Table Displays** → Uses stored results (always visible)
3. **Click Firm Name** → 
   - `selected_firm` stored in session state
   - Form submission flags cleared
   - Page reruns
4. **Form Re-renders** → 
   - New form instance created (different key)
   - Reads `selected_firm` from session state
   - Auto-fills all fields
5. **Table Stays Visible** → Uses stored `filter_results`

## Validation Checks

The code now ensures:
- ✅ Results stored before any button clicks
- ✅ DataFrame stored for data lookup
- ✅ Table always uses stored results
- ✅ Form key changes when firm changes
- ✅ Form reads fresh session state
- ✅ All inputs have unique keys
- ✅ Rerun triggers form update

## Testing

To verify:
1. Filter companies → Table appears
2. Click firm name → Table should STAY visible
3. Check sidebar → Form should auto-fill with firm name, sector, stage
4. Click different firm → Form should update, table should stay

## If Still Not Working

Check:
1. **Terminal logs** - Look for any errors
2. **Session state** - Use `st.write(st.session_state)` to debug
3. **Form key** - Should change when different firm is selected
4. **DataFrame** - Ensure Excel data has industry/stage columns

The fixes are comprehensive and should work. If issues persist, check terminal for specific error messages.
