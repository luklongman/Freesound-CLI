# FreeSound CLI (Prototype)

Date: May 20, 2025 (Tue)  
Version: Prototype


https://github.com/user-attachments/assets/dd16a03d-7310-4eb0-8c4c-48a5ef04a3dd


## Overview

This project provides a command-line interface (CLI) to browse, preview, inspect, and download sounds from FreeSound.org. It's built with Python and utilizes `rich` for a user-friendly console experience and `sounddevice` for audio playback.

### Main Features:
* **Query**: Search for sounds using keywords.
* **Paginate**: Navigate through search results page by page.
* **Preview**: Play MP3 previews of sounds directly in the terminal, with seeking capabilities.
* **Sound Inspection**: View detailed information about a selected sound.
* **Download Sounds**: Download high-quality MP3 previews of sounds.

### Commands:
* `play #` or `p #`:      Play a sound by index.
* `play r` or `p r`:      Play a random sound from the current page.
* `inspect #` or `i #`:   View details of a sound by index.
* `download #` or `d #`:  Download a sound by index.
* `prev` or `<`:          Go to the previous page.
* `next` or `>`:          Go to the next page.
* `go #` or `g #`:        Go to a specific page.
* `go r` or `g r`:        Go to a random page.
* `restart` or `r`:       Start a new search.
* `quit` or `q`:          Exit the application.
* `clear` or `c`:         Clear the console screen.

## Installation and Prerequisites

Before running the FreeSound CLI, ensure you have Python 3.11 or newer installed.

### 1. Clone the repository:

```bash
git clone [https://github.com/luklongman/freesound-cli-prototype.git](https://github.com/luklongman/freesound-cli-prototype.git)
cd freesound-cli-prototype

### 2. Set up a virtual environment (recommended):
Bash

python -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate

3. Install project dependencies:

This project uses a requirements.txt file to manage its dependencies. Install them using pip:
Bash

pip install -r requirements.txt

This will install all required packages including requests, python-dotenv, rich, sounddevice, soundfile, and numpy.
4. Obtain a FreeSound API Key:

    Go to the FreeSound Developers website.

    Create a new application to obtain your API key.

    Create a file named .env in the root directory of the project (where requirements.txt is located).

    Add your API key to the .env file in the following format:

    FREESOUND_API_KEY=your_actual_api_key_here

5. Install PortAudio:

sounddevice relies on PortAudio. You'll need to install it separately depending on your operating system.

    macOS (using Homebrew):
    Bash

brew install portaudio

Debian/Ubuntu:
Bash

    sudo apt-get install libportaudio2

    Windows: You might need to download the PortAudio binaries and place them in your system's PATH or in the same directory as your Python script. Refer to the python-sounddevice documentation for more detailed instructions specific to Windows.
