from game.engine import GameEngine
from ui.tui import TUI

def main():
    # Initialize the Text User Interface
    tui = TUI()

    # Show the main menu and let the user select trivia categories
    selected_categories = tui.display_menu()
    if selected_categories is None:
        # User chose to exit from the menu
        print("[*] User exited from main menu.")
        return

    print(f"[*] Selected categories: {selected_categories}")

    # Initialize the game engine with the selected categories
    game_engine = GameEngine(selected_categories)
    print("[*] Starting game...")

    # Show the animated loading screen and fetch questions
    tui.display_loading_and_fetch(game_engine)

    # Main game loop
    while True:
        # Get the current game state (question, score, lives, etc.)
        game_state = game_engine.get_game_state()

        # If questions are still loading, skip rendering and wait
        if game_state.get("loading"):
            continue

        print("[*] Rendering game state...")

        # Render the current question and get user input
        user_input = tui.render_game_state(game_state)

        # If the game is finished, exit the loop
        if game_state.get("finished"):
            print("[*] Game finished.")
            break

        # Check the user's answer and update the game state
        correct_answer = game_state.get("correct_answer")
        print(f"[*] User input: {user_input}, Correct answer: {correct_answer}")
        game_engine.handle_input(user_input, correct_answer)

if __name__ == "__main__":
    main()
