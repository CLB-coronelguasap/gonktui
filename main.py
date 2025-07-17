from game.engine import GameEngine
from ui.tui import TUI

def main():
    tui = TUI()
    selected_categories = tui.display_menu()
    if selected_categories is None:
        print("[*] User exited from main menu.")
        return

    print(f"[*] Selected categories: {selected_categories}")
    game_engine = GameEngine(selected_categories)
    print("[*] Starting game...")
    tui.display_loading_and_fetch(game_engine)  # Loads questions with animated screen

    while True:
        game_state = game_engine.get_game_state()
        if game_state.get("loading"):
            # No need to fetch here, already done in loading screen
            continue
        print("[*] Rendering game state...")
        user_input = tui.render_game_state(game_state)
        if game_state.get("finished"):
            print("[*] Game finished.")
            break
        correct_answer = game_state.get("correct_answer")
        print(f"[*] User input: {user_input}, Correct answer: {correct_answer}")
        game_engine.handle_input(user_input, correct_answer)

if __name__ == "__main__":
    main()
