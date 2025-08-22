from game.engine import GameEngine
from ui.tui import TUI

def main():
    tui = TUI()
    while True:
        # Show menu and get categories and difficulty
        result = tui.display_menu()
        if result is None:
            print("Goodbye!")
            break
        categories, difficulty = result

        # Start a new game with selected categories and difficulty
        engine = GameEngine(categories, difficulty)
        engine.fetch_questions()

        # Game loop
        while engine.lives > 0:
            # If out of questions, fetch more
            if engine.current_index >= len(engine.questions):
                engine.fetch_questions()
                if not engine.questions:
                    print("No more questions available. Restarting game.")
                    break

            state = engine.get_game_state()
            if state.get("finished"):
                print(f"Game over! Your score: {state['score']}")
                break

            answer = tui.render_game_state(state)
            engine.handle_input(answer, state["correct_answer"])

        # Ask if user wants to play again
        play_again = input("Play again? (y/n): ").strip().lower()
        if play_again != "y":
            print("Thanks for playing!")
            break

if __name__ == "__main__":
    main()
