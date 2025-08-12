import os
import sys
from autocomplete import CACHE_FILE

def initialize_autocomplete_system(acs):
    """
    Initialize the autocomplete system instance.
    If cache exists, load it.
    Otherwise, build index from folder provided as command line argument, then save cache.
    Args:
        acs: instance of AutoCompleteSystem
    """
    if not os.path.exists(CACHE_FILE):
        if len(sys.argv) < 2:
            print("Usage: python main.py <root_folder_to_index>")
            sys.exit(1)
        folder = sys.argv[1]
        acs.build_from_folder(folder)
        acs.save_cache()
    else:
        acs.load_cache()
