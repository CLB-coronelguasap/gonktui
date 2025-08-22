import curses
import random
import html
import time
import requests
import os
import json

# ASCII art logo for the main menu
GONKWARE_ART = [
    " ██████╗  ██████╗ ███╗   ██╗██╗  ██╗██╗    ██╗ █████╗ ██████╗ ███████╗",
    "██╔════╝ ██╔═══██╗████╗  ██║██║ ██╔╝██║    ██║██╔══██╗██╔══██╗██╔════╝",
    "██║  ███╗██║   ██║██╔██╗ ██║█████╔╝ ██║ █╗ ██║███████║██████╔╝█████╗  ",
    "██║   ██║██║   ██║██║╚██╗██║██╔═██╗ ██║███╗██║██╔══██║██╔══██╗██╔══╝  ",
    "╚██████╔╝╚██████╔╝██║ ╚████║██║  ██╗╚███╔███╔╝██║  ██║██║  ██║███████╗",
    " ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝"
]

PREFS_FILE = os.path.expanduser("~/.gonkware_prefs.json")

def fetch_categories():
    """Fetches trivia categories from the Open Trivia DB API."""
    url = "https://opentdb.com/api_category.php"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return data.get("trivia_categories", [])
    except Exception:
        return []

class TUI:
    """Simple Text User Interface for the trivia game."""
    def __init__(self):
        self.selected_categories = set()
        self.load_preferences()

    def load_preferences(self):
        """Loads user category preferences from a local file."""
        if os.path.exists(PREFS_FILE):
            try:
                with open(PREFS_FILE, "r") as f:
                    data = json.load(f)
                    self.selected_categories = set(data.get("categories", []))
            except Exception:
                self.selected_categories = set()

    def save_preferences(self):
        """Saves user category preferences to a local file."""
        try:
            with open(PREFS_FILE, "w") as f:
                json.dump({"categories": list(self.selected_categories)}, f)
        except Exception:
            pass

    def _init_colors(self):
        """Initializes color pairs for the TUI."""
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)      # Logo
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)   # Subtitle
        curses.init_pair(3, curses.COLOR_YELLOW, -1)    # Highlight
        curses.init_pair(4, curses.COLOR_GREEN, -1)     # Selected
        curses.init_pair(5, curses.COLOR_RED, -1)       # Error

    def display_menu(self):
        """Displays the main menu and returns the selected categories or None if exited."""
        return curses.wrapper(self._main_menu)

    def _main_menu(self, stdscr):
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()

        # Draw ASCII art logo at the top
        for i, line in enumerate(GONKWARE_ART):
            stdscr.addstr(2 + i, max_x // 2 - len(line) // 2, line, curses.color_pair(1) | curses.A_BOLD)

        subtitle = "Welcome to GONKWARE Trivia!"
        subtitle_y = 2 + len(GONKWARE_ART) + 1
        stdscr.addstr(subtitle_y, max_x // 2 - len(subtitle) // 2, subtitle, curses.color_pair(2) | curses.A_BOLD)

        menu_items = ["[Start Game]", "[Select Categories]", "[Exit]"]
        idx = 0

        while True:
            # Draw menu box border only
            box_top = subtitle_y + 2
            box_left = max_x // 2 - 20
            box_width = 40
            box_height = 8
            for y in range(box_top, box_top + box_height):
                if y == box_top or y == box_top + box_height - 1:
                    stdscr.addstr(y, box_left, "+" + "-" * (box_width - 2) + "+")
                else:
                    stdscr.addstr(y, box_left, "|" + " " * (box_width - 2) + "|")

            # Draw menu items
            for i, item in enumerate(menu_items):
                y = box_top + 2 + i * 2
                x = max_x // 2 - len(item) // 2
                attr = curses.color_pair(3) | curses.A_BOLD if i == idx else curses.color_pair(4)
                stdscr.addstr(y, x, item, attr)

            stdscr.refresh()
            key = stdscr.getch()
            if key in [curses.KEY_UP, ord('k')]:
                idx = (idx - 1) % len(menu_items)
            elif key in [curses.KEY_DOWN, ord('j')]:
                idx = (idx + 1) % len(menu_items)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                if idx == 2:  # Exit
                    return None
                elif idx == 1:  # Select Categories
                    self._category_menu(stdscr)
                elif idx == 0:  # Start Game
                    if not self.selected_categories:
                        stdscr.addstr(box_top + box_height - 2, box_left + 2, "Please select at least one category.", curses.color_pair(5) | curses.A_BOLD)
                        stdscr.refresh()
                        curses.napms(1200)
                        stdscr.addstr(box_top + box_height - 2, box_left + 2, " " * (box_width - 4))
                        continue
                    return list(self.selected_categories)

    def _category_menu(self, stdscr):
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()
        categories = fetch_categories()
        menu_items = [cat["name"] for cat in categories]
        idx = 0
        scroll = 0
        visible_items = min(len(menu_items), max_y - 10)
        box_top = 4
        box_left = max_x // 2 - 30
        box_width = 60
        box_height = visible_items + 4

        # Draw border for category box
        for y in range(box_top, box_top + box_height):
            if y == box_top or y == box_top + box_height - 1:
                stdscr.addstr(y, box_left, "+" + "-" * (box_width - 2) + "+")
            else:
                stdscr.addstr(y, box_left, "|" + " " * (box_width - 2) + "|")

        stdscr.addstr(2, max_x // 2 - 10, "Select Categories", curses.color_pair(2) | curses.A_BOLD)
        while True:
            stdscr.addstr(box_top, box_left + 2, "Use SPACE to toggle. ENTER to return.", curses.color_pair(1) | curses.A_DIM)

            # Draw category selection inside the box with scrolling
            for i in range(visible_items):
                item_idx = scroll + i
                if item_idx >= len(menu_items):
                    break
                item = menu_items[item_idx]
                x = box_left + 4
                y = box_top + 2 + i
                cat_id = categories[item_idx]["id"]
                prefix = "[x] " if cat_id in self.selected_categories else "[ ] "
                display = prefix + item
                attr = curses.color_pair(3) | curses.A_BOLD if item_idx == idx else curses.color_pair(4)
                stdscr.addstr(y, x, display[:box_width - 8], attr)
            stdscr.refresh()
            key = stdscr.getch()
            if key in [curses.KEY_UP, ord('k')]:
                if idx > 0:
                    idx -= 1
                if idx < scroll:
                    scroll -= 1
            elif key in [curses.KEY_DOWN, ord('j')]:
                if idx < len(menu_items) - 1:
                    idx += 1
                if idx >= scroll + visible_items:
                    scroll += 1
            elif key == ord(' '):
                cat_id = categories[idx]["id"]
                if cat_id in self.selected_categories:
                    self.selected_categories.remove(cat_id)
                else:
                    self.selected_categories.add(cat_id)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                break
        self.save_preferences()
        stdscr.clear()
        stdscr.border(0)

    def render_game_state(self, game_state):
        """Renders the current game state (question, choices, score, lives)."""
        if game_state.get("loading"):
            self.display_loading()
            return None
        return curses.wrapper(self._render, game_state)

    def _render(self, stdscr, game_state):
        stdscr.clear()
        stdscr.border()
        max_y, max_x = stdscr.getmaxyx()

        def safe_addstr(y, x, text, attr=curses.A_NORMAL):
            if y < max_y - 1 and x < max_x - 1:
                stdscr.addstr(y, x, text[:max_x - x - 1], attr)

        if game_state.get("finished"):
            safe_addstr(2, 4, "Game Over!", curses.A_BOLD)
            safe_addstr(4, 4, f"Your score: {game_state['score']}", curses.A_BOLD)
            safe_addstr(6, 4, "Press any key to exit.", curses.A_DIM)
            stdscr.refresh()
            stdscr.getch()
            return None

        question = html.unescape(game_state["question"])
        choices = [html.unescape(c) for c in game_state["choices"]]
        random.shuffle(choices)
        score = game_state["score"]
        index = game_state["index"]
        total = game_state["total"]
        lives = game_state["lives"]

        safe_addstr(2, 4, f"Question {index}/{total}", curses.A_BOLD)
        safe_addstr(3, 4, f"Lives: {'♥'*lives}", curses.A_BOLD)
        safe_addstr(4, 4, f"Score: {score}", curses.A_DIM)
        safe_addstr(6, 4, question, curses.A_UNDERLINE)

        selected = 0
        stdscr.timeout(7000)  # 7 seconds timer
        start_time = time.time()
        while True:
            for i, choice in enumerate(choices):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                safe_addstr(8 + i, 6, f"{i+1}. {choice}", attr)
            remaining = max(0, 7 - int(time.time() - start_time))
            safe_addstr(8 + len(choices) + 2, 6, f"Time left: {remaining}s", curses.A_DIM)
            stdscr.refresh()
            key = stdscr.getch()
            if key == -1:  # Timeout
                return None
            if key in [curses.KEY_UP, ord('k')]:
                selected = (selected - 1) % len(choices)
            elif key in [curses.KEY_DOWN, ord('j')]:
                selected = (selected + 1) % len(choices)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                return choices[selected]

    def display_loading(self):
        """Displays a simple loading screen."""
        curses.wrapper(self._loading_screen)

    def _loading_screen(self, stdscr):
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()
        msg = "Loading questions..."
        stdscr.addstr(max_y // 2, max_x // 2 - len(msg) // 2, msg, curses.color_pair(2) | curses.A_BOLD)
        stdscr.refresh()
        time.sleep(2)