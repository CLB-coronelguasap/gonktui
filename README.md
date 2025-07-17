# TUI Game

This project is a text-based user interface (TUI) game built using Python. It utilizes a game engine to manage game logic and a TUI library to handle user interactions.

## Project Structure

```
tui-game
├── src
│   ├── main.py          # Entry point of the game
│   ├── game
│   │   ├── __init__.py  # Game package initialization
│   │   └── engine.py    # Game engine managing game state and logic
│   ├── ui
│   │   ├── __init__.py  # UI package initialization
│   │   └── tui.py       # Text-based user interface handling
├── requirements.txt      # Project dependencies
└── README.md             # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/CLB-coronelguasap/gonktui.git
   cd tui-game
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Gameplay Instructions

- Run the game by executing the main script:
  ```
  python src/main.py
  ```

- Follow the on-screen instructions to navigate through the game.

## Dependencies

- requests
- windows-curses (for Windows)

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.