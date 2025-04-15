# ASKP CLI Enhancement Implementation Plan

## Background
We need to enhance the ASKP CLI tool with several improvements:
1. Show expanded queries in the output
2. Add file statistics (size in bytes, line count)
3. Generate efficient viewing commands (cat commands with line limits)
4. Compress vertical whitespace
5. Enforce 400 character max line length

## Implementation Approach

### Following Large File Change Safety Protocol
1. ✅ Create backup of original cli.py file
2. ✅ Create new cli.py.new file for modifications
3. ⬜ Implement changes to cli.py.new
4. ⬜ Generate diff for review
5. ⬜ After approval, apply changes

### Required Function Additions
1. `get_file_stats(filepath)` - Calculate file size and line count
2. `generate_cat_commands(filepath, line_count)` - Create efficient viewing commands
3. Modify `output_multi_results()` to include:
   - Track expanded queries and display them
   - Add file statistics section
   - Enforce 400 character line limit
   - Generate viewing commands

### Type Annotations
- Add `Tuple[int, int]` for file stats return type
- Add `List[str]` for cat commands return type

## Safety Measures
- All substantial file operations are preceded by backups
- Changes will be staged in .new files
- Diffs will be produced for approval
- Original backups will be preserved

## Risks and Rollback
If the changes cause issues, rollback procedure:
```bash
mv cli.py.bak cli.py
```
