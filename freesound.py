import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

# --- Local Imports ---
# Assuming both in the same directory
from rich_util_freesound import (
    get_query, get_user_input, print_success, 
    print_error, format_table, format_panel, 
    get_command, console
)
from audio_player import play_preview_with_seek

# --- Global variables ---
load_dotenv()
API_KEY = os.getenv("FREESOUND_API_KEY")
if not API_KEY: # Initial check for API_KEY, more robust message in __main__
    print("Warning: FREESOUND_API_KEY not found during initial load. Ensure it's in .env or environment variables.")

BASE_URL = "https://freesound.org/apiv2"
PAGE_SIZE = 30 # Number of results per page

def search_freesound(query: str, page: int = 1) -> Tuple[Optional[List[Dict[str, Any]]], int]:
    """
    Searches FreeSound for sounds based on a query.
    Args:
        query (str): The search term.
        page (int): The page number to fetch.
    Returns:
        tuple: (A list of sound result dictionaries, total number of pages) or (None, 0) on error.
    """
    if not API_KEY:
        print_error("API key is not configured. Cannot perform search.")
        return None, 0
        
    search_url = f"{BASE_URL}/search/text/"
    params = {
        "query": query,
        "token": API_KEY,
        "page_size": PAGE_SIZE,
        "page": page,
        "fields": "id,username,created,name,category,subcategory,tags,description,license,"
                 "is_remix,was_remixed,pack,is_geotagged,type,duration,bitdepth,bitrate,samplerate,"
                 "filesize,channels,md5,num_downloads,avg_rating,num_ratings,num_comments,previews"
    }

    try:
        response = requests.get(search_url, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        total_results = data.get("count", 0)
        # Ensure total_pages is at least 1 if there are results, or 0 if no results.
        total_pages = (total_results + PAGE_SIZE - 1) // PAGE_SIZE if total_results > 0 else 0
        return data.get("results"), total_pages
    except requests.exceptions.RequestException as e:
        print_error(f"Error searching FreeSound: {e}")
        return None, 0
    except json.JSONDecodeError:
        print_error("Error decoding JSON response from FreeSound.")
        return None, 0

def download_sound(sound_id: str, results: List[Dict[str, Any]]) -> bool:
    """
    Downloads a sound file from Freesound.
    This function attempts to download the high-quality MP3 preview.
    Args:
        sound_id (str): The ID of the sound to download.
        results (List[Dict[str, Any]]): The list of search results.
    Returns:
        bool: True if download was successful, False otherwise.
    """
    if not API_KEY:
        print_error("API key is not configured. Cannot download sound.")
        return False

    selected_sound = None
    for sound_item in results:
        if str(sound_item["id"]) == str(sound_id):
            selected_sound = sound_item
            break
    
    if not selected_sound:
        print_error(f"Sound ID {sound_id} not found in current results.")
        return False

    download_url = selected_sound["previews"].get("preview-hq-mp3") 
    
    if not download_url:
        print_error(f"No suitable download URL (preview-hq-mp3) found for sound '{selected_sound['name']}'.")
        return False

    try:
        headers = {"Authorization": f"Token {API_KEY}"}
        
        response = requests.get(download_url, headers=headers, stream=True, timeout=30) 
        response.raise_for_status()
        
        # Sanitize filename: replace slashes and backslashes to prevent path issues
        filename_base = selected_sound['name'].replace('/', '_').replace('\\', '_')
        # Ensure filename doesn't exceed common length limits, though this is a basic trim
        filename_base = (filename_base[:200] + '...') if len(filename_base) > 200 else filename_base
        filename = f"{filename_base}.mp3" 
        
        # Save the downloaded file
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)
        print_success(f"Downloaded '{filename}'")
        return True
    except requests.exceptions.RequestException as e:
        print_error(f"Error downloading sound: {e}")
        return False
    except IOError as e: # Catch errors during file writing (e.g., disk full, permissions)
        print_error(f"Error writing file '{filename}': {e}")
        return False
    except Exception as e: # Catch any other unexpected errors
        print_error(f"An unexpected error occurred during download: {e}")
        return False

# The original play_preview function is now replaced by play_preview_with_seek from audio_player.py

if __name__ == "__main__":
    # More robust API Key check at the start of execution
    if not API_KEY:
        # Use console from rich_util for styled output if available
        # This assumes console is initialized in rich_util_freesound
        try:
            console.print("[bold red]FREESOUND_API_KEY is not set.[/bold red]")
            console.print("Please create a [yellow].env[/yellow] file in the script's directory with your API key,")
            console.print("or set it as an environment variable.")
            console.print("Example .env file content:\nFREESOUND_API_KEY=your_actual_api_key_here")
        except NameError: # Fallback if console is not yet defined or rich_util is problematic
            print("ERROR: FREESOUND_API_KEY is not set.")
            print("Please create a .env file with your API key or set it as an environment variable.")
            print("Example .env file content:\nFREESOUND_API_KEY=your_actual_api_key_here")
        exit(1) # Exit if API key is crucial and not found

    prompts = get_query()
    while True:
        query_input = get_user_input(prompts["query"], default="birdsong")
        search_query = query_input.strip() if query_input is not None else "birdsong"
        print_success(f"Searching for '{search_query}'...")

        current_page = 1
        skip_print_table = False
        results, total_pages = search_freesound(search_query, current_page)
        
        
        if results is not None and len(results) > 0:
            while True:  # Results navigation and action loop
                if not skip_print_table:
                    console.print(format_table(results, current_page=current_page, total_pages=total_pages, per_page=PAGE_SIZE))
                command, value = get_command(len(results), current_page, total_pages)
                skip_print_table = True # Default to not reprinting unless a navigation command changes the page

                if command == 'quit':
                    print_success("Exiting FreeSound CLI. Goodbye!")
                    exit(0)
                elif command == 'restart':
                    print_success("Restarting search...")
                    break # Breaks inner loop to re-enter search query
                elif command == 'prev':
                    if current_page > 1:
                        current_page -= 1
                        new_results, new_total_pages = search_freesound(search_query, current_page)
                        if new_results is not None:
                            results, total_pages = new_results, new_total_pages
                            skip_print_table = False 
                        else:
                            print_error("Error fetching previous page. Staying on current page.")
                            current_page +=1 # Revert page change
                    else:
                        print_error("Already on the first page.")
                elif command == 'next':
                    if current_page < total_pages:
                        current_page += 1
                        new_results, new_total_pages = search_freesound(search_query, current_page)
                        if new_results is not None:
                            results, total_pages = new_results, new_total_pages
                            skip_print_table = False
                        else:
                            print_error("Error fetching next page. Staying on current page.")
                            current_page -=1 # Revert page change
                    else:
                        print_error("Already on the last page.")
                elif command == 'go' and value is not None:
                    if 1 <= value <= total_pages:
                        current_page = value
                        new_results, new_total_pages = search_freesound(search_query, current_page)
                        if new_results is not None:
                            results, total_pages = new_results, new_total_pages
                            skip_print_table = False
                        else:
                            print_error(f"Error fetching page {value}. Staying on previous page.")
                            # Need to know previous page or re-fetch current to be robust
                            # For simplicity, we'll just not change `results` here.
                            # A better approach might be to store old_current_page.
                    else:
                        print_error(f"Page number out of range. Please enter a page between 1 and {total_pages}.")
                elif command == 'clear_screen':
                    console.clear()
                    skip_print_table = False 
                elif command == 'y' and value is not None and results is not None:  # Play sound
                    if 0 <= value < len(results):
                        sound_to_play = results[value]
                        sound_id_to_play = str(sound_to_play["id"])
                        # play_preview_with_seek handles its own print messages
                        if not play_preview_with_seek(sound_id_to_play, results, console, API_KEY):
                            # Error messages are printed within play_preview_with_seek
                            # console.print("") # Optional: add a newline if desired after playback attempt
                            pass 
                        # skip_print_table remains True (no need to reprint table after playback)
                    else:
                        print_error(f"Invalid sound number. Please choose between 1 and {len(results)}.")
                elif command == 'i' and value is not None and results is not None:  # Inspect sound
                    if 0 <= value < len(results):
                        console.print(format_panel(results[value]))
                        console.print("") # Add a newline for better spacing
                    else:
                        print_error(f"Invalid sound number. Please choose between 1 and {len(results)}.")
                elif command == 'd' and value is not None and results is not None:  # Download sound
                     if 0 <= value < len(results):
                        sound_to_download = results[value]
                        sound_id_to_download = str(sound_to_download["id"])
                        print_success(f"Attempting to download sound #{value + 1}: '{sound_to_download['name']}'...")
                        if not download_sound(sound_id_to_download, results): # API_KEY is used internally by download_sound
                            # download_sound prints its own error messages
                            pass
                     else:
                        print_error(f"Invalid sound number. Please choose between 1 and {len(results)}.")
                # else: # An unknown command or an issue with arguments (get_command should catch most)
                    # if command not in ['prev', 'next', 'quit', 'restart', 'clear_screen', 'go']:
                         # print_error(f"Unknown command or issue: '{command}{' ' + str(value) if value is not None else ''}'")
                    # if not skip_print_table: # If navigation happened, table will be reprinted.
                        # pass
                    # else: # If it was an invalid action, prompt again without reprinting.
                        # skip_print_table = True


        elif results is None: # Error occurred during search (search_freesound returned None for results)
            print_error("An error occurred while searching. Please check your connection or API key.")
            user_choice = get_user_input("Try searching again? (y/n)", default="y")
            if user_choice != 'y':
                print_success("Exiting due to search error. Goodbye!")
                break # Exit main application loop
            # else: continue to the next iteration of the main loop to prompt for search again
        else: # No results found (results is an empty list)
            print_error(f"No results found for '{search_query}'. Try a different search term.")
            # Loop will continue to prompt for a new search query
