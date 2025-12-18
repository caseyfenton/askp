__version__ = "2.4.5"

# Don't import cli.py components directly in __init__.py
# This prevents circular imports and the "found in sys.modules" RuntimeWarning

# Only import core functionality that won't cause circular imports
from askp.api import search_perplexity
from askp.codecheck import handle_code_check
from askp.formatters import format_json, format_markdown, format_text
from askp.file_utils import format_path, get_file_stats, generate_cat_commands
from askp.utils import (format_size, sanitize_filename, load_api_key, get_model_info, 
                    normalize_model_name, estimate_cost, get_output_dir, generate_combined_filename, 
                    generate_unique_id)

# Delay importing of cli and executor modules to avoid circular dependencies
# These will be imported when explicitly needed