from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.text import Text
from datetime import datetime
import random

# Initialize console and styles once as module-level constants
console = Console()
SUCCESS_STYLE = Style(color="green")
ERROR_STYLE = Style(color="red")
COMMAND_STYLE = Style(color="yellow")

def print_success(message):
    """Print a success message in green."""
    console.print(message, style=SUCCESS_STYLE)

def print_error(message):
    """Print an error message in red."""
    console.print(message, style=ERROR_STYLE)

def get_user_input(prompt, default=None):
    """Get user input with Rich prompt."""
    return Prompt.ask(prompt, default=default)

def get_command(max_index, current_page=1, total_pages=1):
    """Get user's main actions."""
    print_success("Commands: play #/r, inspect #, download #, prev, next, go #/r, restart, quit, clear (r for random)")

    while True:
        choice_input = get_user_input("Enter command")
        if choice_input is None:
            continue

        choice = choice_input.lower().strip()

        # Handle simple commands first
        if choice in ['q', 'quit']:
            return 'quit', None
        elif choice in ['r', 'restart']:
            return 'restart', None
        elif choice in ['prev', '<']:
            return 'prev', None  # Trigger reprinting
        elif choice in ['next', '>']:
            return 'next', None  # Trigger reprinting
        elif choice in ['c', 'clear']:
            return 'clear_screen', None # New command to clear and reprint

        # Split command and arguments
        parts = choice.split()
        if not parts:
            print_error("Please enter a command")
            continue

        cmd = parts[0]
        args = parts[1:]

        # Handle commands that need a number or 'r'
        if cmd in ['g', 'go']:
            if not args:
                page_input = get_user_input("Enter page number or 'r' for random")
                if page_input is None:
                    continue
                arg = page_input.strip().lower()
            else:
                arg = args[0].strip().lower()

            if arg == 'r':
                if total_pages > 0:
                    page = random.randint(1, total_pages)
                    return 'go', page  # Trigger reprinting
                else:
                    print_error("No pages available to go to a random page.")
                    continue
            else:
                try:
                    page = int(arg)
                    if 1 <= page <= total_pages:
                        return 'go', page  # Trigger reprinting
                    else:
                        print_error(f"Please enter a page number between 1 and {total_pages}")
                        continue
                except ValueError:
                    print_error("Please enter a valid number or 'r'")
                    continue

        elif cmd in ['p', 'play', 'i', 'inspect', 'd', 'download']:
            # Map short commands to full commands
            cmd_map = {
                'p': 'play',
                'i': 'inspect',
                'd': 'download'
            }

            # Convert short command to full command
            full_cmd = cmd_map.get(cmd, cmd)

            if not args:
                num_input = get_user_input(f"Enter sound number (1-{max_index}) or 'r' for random")
                if num_input is None:
                    continue
                arg = num_input.strip().lower()
            else:
                arg = args[0].strip().lower()

            if arg == 'r':
                if max_index > 0:
                    num = random.randint(0, max_index - 1)
                    if full_cmd == 'play':
                        return 'y', num  # Do not trigger reprinting
                    else:
                        return full_cmd[0], num  # Do not trigger reprinting
                else:
                    print_error("No sounds available on this page.")
                    continue
            else:
                try:
                    num = int(arg)
                except ValueError:
                    print_error("Please enter a valid number or 'r'")
                    continue

                if 1 <= num <= max_index:
                    if full_cmd == 'play':
                        return 'y', num - 1  # Do not trigger reprinting
                    else:
                        return full_cmd[0], num - 1  # Do not trigger reprinting
                else:
                    print_error(f"Please enter a number between 1 and {max_index}")
                    continue
        else:
            print_error("Invalid command")

def format_table(results, current_page=1, total_pages=1, per_page=30):
    table = Table(title=f"FreeSound.org Search Results - Page {current_page}/{total_pages}")
    table.add_column("#", style="yellow", justify="right")
    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Name", style="yellow", width=40)
    table.add_column("Dur.", style="magenta", justify="right")
    table.add_column("Upload Date", style="blue", justify="center")
    table.add_column("User", style="green")
    table.add_column("Tags", style="green", width=30)

    # 'results' already contains only the items for the current page.
    # 'start_idx' is used to ensure the '#' column shows the correct absolute item number.
    #start_idx_for_enumeration = (current_page - 1) * per_page

    for local_idx, sound in enumerate(results): # Iterate directly over the paged results
        # Calculate the absolute index for display
        #absolute_idx = start_idx_for_enumeration + local_idx + 1
        
        date = datetime.fromisoformat(sound['created'].replace('Z', '+00:00'))
        date_str = date.strftime('%Y-%m')
        tags = ', '.join(sound['tags'][:3]) if sound['tags'] else 'No tags'

        table.add_row(
            # str(absolute_idx), # Use the calculated absolute index
            str(local_idx+1), # relative index from 1
            str(sound["id"]),
            sound["name"][:40],
            f"{sound['duration']:.1f}s",
            date_str,
            sound["username"],
            tags
        )
    return table

def format_panel(sound):
    """Create a detailed panel for a single sound result."""
    """ MOre data to be added here"""
    created_str = datetime.fromisoformat(sound['created'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
    tags_str = ', '.join(sound['tags'][:5]) if sound['tags'] else 'No tags'
    desc_str = sound['description'][:100] + '...' if sound['description'] else 'No description'
    
    details = f"""[cyan]ID:[/cyan] {sound['id']}
[cyan]Name:[/cyan] {sound['name']}
[cyan]Created:[/cyan] {created_str}
[cyan]Type:[/cyan] {sound['type']}
[cyan]Duration:[/cyan] {sound['duration']:.2f}s
[cyan]Tags:[/cyan] {tags_str}
[cyan]Preview:[/cyan] Available - type p # to play
[cyan]Description:[/cyan] {desc_str}
[cyan]License:[/cyan] {sound['license']}"""

    return Panel(
        details,
        title=f"[yellow]{sound['username']}[/yellow]'s Sound",
        border_style="blue"
    )

def get_query():
    """Return dictionary of search prompts."""
    return {
        "query": "Enter query"
    }