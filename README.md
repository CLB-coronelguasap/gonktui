# TUI Game

This project is a text-based user interface (TUI) game built using Python. It utilizes a game engine to manage game logic and a TUI library to handle user interactions.

## Setup Instructions

1. **Install Python 3.11**  
   Download and install Python 3.11 from [python.org](https://www.python.org/downloads/release/python-3110/).

2. **Create a virtual environment with Python 3.11**  
   ```
   python3.11 -m venv venv
   ```

3. **Activate the virtual environment**  
   - On Linux/macOS:
     ```
     source venv/bin/activate
     ```
   - On Windows:
     ```
     venv\Scripts\activate
     ```

4. **Install the required dependencies**  
   ```
   pip install -r requirements.txt
   ```

5. **Run the game**  
   ```
   python main.py
   ```

## Dependencies

- requests
- windows-curses (only needed on Windows)

## Notes

- On Windows, `windows-curses` is required for TUI support.
- Python 3.12+ is not supported by `windows-curses` as of July 2025.