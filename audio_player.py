# audio_player.py
import sounddevice as sd
import soundfile as sf
from tempfile import NamedTemporaryFile
from pathlib import Path
import time
import requests
from typing import List, Dict, Any, Optional

# Local import for console
try:
    from rich_util_freesound import console as default_console
except ImportError:
    class SimpleConsole:
        def print(self, message, *args, **kwargs):
            print(message)
    default_console = SimpleConsole()


def play_preview_with_seek(sound_id: str, results: List[Dict[str, Any]], console: Any = default_console, api_key: Optional[str] = None) -> bool:
    """
    Plays a sound preview with seeking (0-9) and stopping ('s') capabilities
    using blocking input(). Does not use the 'keyboard' library.

    Args:
        sound_id (str): The ID of the sound to play.
        results (List[Dict[str, Any]]): The list of search results containing sound details.
        console (Console): The Rich Console instance (or a similar object with a print method) for output.
        api_key (Optional[str]): The Freesound API key for fetching the preview.

    Returns:
        bool: True if playback was attempted, False on error before playback.
    """
    selected_sound = None
    for sound in results:
        if str(sound["id"]) == str(sound_id):
            selected_sound = sound
            break
    
    if not selected_sound:
        console.print(f"[red]Error: Sound ID {sound_id} not found in results.[/red]")
        return False

    preview_url = selected_sound["previews"].get("preview-hq-mp3")
    if not preview_url:
        console.print(f"[red]Error: No HQ MP3 preview URL found for sound {sound_id} ('{selected_sound.get('name', 'N/A')}').[/red]")
        return False
    
    temp_path: Optional[Path] = None

    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Token {api_key}"

        response = requests.get(preview_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        with NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_path = Path(temp_file.name)
        
        data, samplerate = sf.read(temp_path)
        total_frames = len(data)
        duration_seconds = total_frames / samplerate

        if total_frames == 0:
            console.print("[red]Error: Audio file is empty or could not be read.[/red]")
            return False

        console.print(f"[green]Playing: {selected_sound.get('name', 'Unknown Sound')} ({duration_seconds:.2f}s)[/green]")
        
        current_data_segment = data # Initially, play the whole file
        sd.play(current_data_segment, samplerate)

        while sd.get_stream().active:
            try:
                # Use Rich console.input if available, otherwise standard input
                if hasattr(console, 'input'):
                    user_input = console.input(
                        "[yellow] stop or seek <0-9>/10: [/yellow]"
                    ).strip().lower()
                else: # Fallback for basic print/input
                    user_input = input(
                        "[yellow] stop or seek <0-9>/10: [/yellow]"
                    ).strip().lower()

                if user_input == 's' or user_input == 'stop':
                    sd.stop()
                    console.print("\n[yellow]Playback stopped.[/yellow]")
                    break
                elif user_input.isdigit() and '0' <= user_input <= '9':
                    sd.stop() # Stop current playback before seeking
                    time.sleep(0.05) # Brief pause to ensure stream is fully stopped

                    percentage = int(user_input) / 10.0
                    start_frame = int(total_frames * percentage)
                    
                    if start_frame < total_frames:
                        console.print(f"\n[yellow]Seeking to {int(percentage*100)}%...[/yellow]")
                        current_data_segment = data[start_frame:]
                        sd.play(current_data_segment, samplerate)
                        # The loop will continue as long as the new sd.play() stream is active
                    else:
                        console.print("\n[yellow]Seek position is at or beyond the end of the audio. Stopping.[/yellow]")
                        # sd.stop() was already called
                        break 
                elif not user_input: # User just pressed Enter
                    # Let playback continue, sleep briefly to prevent tight loop if input is non-blocking
                    # (though standard input() is blocking)
                    time.sleep(0.1) 
                else:
                    console.print("\n[red]Invalid input. Playback continues. Use 0-9, 's', or Enter.[/red]")
            
            except KeyboardInterrupt: # Handle Ctrl+C
                sd.stop()
                console.print("\n[yellow]Playback interrupted by user (Ctrl+C).[/yellow]")
                break
            except Exception as e_loop: # Catch other errors during the input loop
                console.print(f"\n[red]Error during playback interaction: {e_loop}[/red]")
                sd.stop()
                break
        
        # After the loop, if not explicitly stopped by 's' or Ctrl+C, and stream is inactive
        if not sd.get_stream().active and user_input != 's':
             # Check if playback finished naturally
            # This condition might be tricky if seeking to the end effectively stops it
            # A more robust check might be needed if natural completion vs. seek-to-end needs differentiation
            console.print("\n[green]Playback finished or reached end of seekable segment.[/green]")

        return True

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error fetching preview for playback: {e}[/red]")
        return False
    except sf.LibsndfileError as e:
        console.print(f"[red]Error reading sound file (libsndfile): {e}. It might be corrupted or an unsupported format.[/red]")
        return False
    except sd.PortAudioError as e:
        console.print(f"[red]SoundDevice/PortAudio Error: {e}. Is a sound output device available and working?[/red]")
        return False
    except Exception as e:
        console.print(f"[red]An unexpected error occurred in play_preview: {e} (Type: {type(e).__name__})[/red]")
        return False
    finally:
        if sd.get_stream().active: # Ensure stream is stopped if an exception occurred mid-loop
            sd.stop()
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception as e_unlink:
                console.print(f"[yellow]Warning: Could not delete temporary file {temp_path}: {e_unlink}[/yellow]")

