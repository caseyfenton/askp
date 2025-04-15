# ASKP CLI Enhancement Implementation Plan

## Changes to be implemented:

1. **File Statistics Function**
   - Add function to calculate file size and line count
   - Already implemented in file_utils.py

2. **Cat Commands Generation**
   - Add function to generate optimal viewing commands
   - Already implemented in file_utils.py

3. **Output Enhancement**
   - Modify output_multi_results to return a string instead of None
   - Add expanded query information to filenames
   - Add section to display original and expanded queries
   - Enforce 400 character maximum line length
   - Add file statistics and viewing commands to output
   - Display file statistics on console

4. **Query Expansion Tracking**
   - Update CLI function to track original and expanded queries
   - Already implemented initial display in expand.py
   - Need to modify cli.py to maintain query tracking

## Implementation Approach (LFCP):

1. ✅ Created backup of original file (cli.py.bak)
2. ⬜ Create implementation file with all changes (cli.py.enhanced)
3. ⬜ Generate diff for review (cli.py.diff)
4. ⬜ Only proceed after review and approval
5. ⬜ Keep backup for potential rollback

## Verification:
1. ⬜ Confirm all functions are properly implemented
2. ⬜ Verify correct type annotations
3. ⬜ Test with expanded query generation
4. ⬜ Verify output formatting
