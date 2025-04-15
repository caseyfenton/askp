__version__ = "2.4.1"
from askp.cli import cli, main
from askp.api import search_perplexity
from askp.codecheck import handle_code_check
from askp.executor import execute_query, handle_multi_query, output_result, output_multi_results
from askp.formatters import format_json, format_markdown, format_text
from askp.file_utils import format_path, get_file_stats, generate_cat_commands
from askp.utils import (format_size, sanitize_filename, load_api_key, get_model_info, 
                    normalize_model_name, estimate_cost, get_output_dir, generate_combined_filename, 
                    generate_unique_id)