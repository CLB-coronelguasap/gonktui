import curses
import random
import html
import time
import requests
import json
import os

# ASCII art logo for the main menu
GONKWARE_ART = [
    " ██████╗  ██████╗ ███╗   ██╗██╗  ██╗██╗    ██╗ █████╗ ██████╗ ███████╗",
    "██╔════╝ ██╔═══██╗████╗  ██║██║ ██╔╝██║    ██║██╔══██╗██╔══██╗██╔════╝",
    "██║  ███╗██║   ██║██╔██╗ ██║█████╔╝ ██║ █╗ ██║███████║██████╔╝█████╗  ",
    "██║   ██║██║   ██║██║╚██╗██║██╔═██╗ ██║███╗██║██╔══██║██╔══██╗██╔══╝  ",
    "╚██████╔╝╚██████╔╝██║ ╚████║██║  ██╗╚███╔███╔╝██║  ██║██║  ██║███████╗",
    " ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝"
]

# Path for saving user preferences
PREFS_FILE = os.path.expanduser("~/.gonkware_prefs.json")

def fetch_categories():
    """
    Fetches trivia categories from the Open Trivia DB API.
    Returns a list of category dictionaries.
    """
    url = "https://opentdb.com/api_category.php"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return data.get("trivia_categories", [])
    except Exception:
        return []

class TUI:
    """
    Text User Interface class for the GONKWARE trivia game.
    Handles menus, category selection, loading screens, and game rendering.
    """
    def __init__(self):
        self.screen = None
        self.selected_categories = set()
        self.load_preferences()

    def load_preferences(self):
        """
        Loads user category preferences from a local file.
        """
        if os.path.exists(PREFS_FILE):
            try:
                with open(PREFS_FILE, "r") as f:
                    data = json.load(f)
                    self.selected_categories = set(data.get("categories", []))
            except Exception:
                self.selected_categories = set()

    def save_preferences(self):
        """
        Saves user category preferences to a local file.
        """
        try:
            with open(PREFS_FILE, "w") as f:
                json.dump({"categories": list(self.selected_categories)}, f)
        except Exception:
            pass

    def _init_colors(self):
        """
        Initializes color pairs for the TUI.
        """
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)      # Logo
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)   # Subtitle
        curses.init_pair(3, curses.COLOR_YELLOW, -1)    # Highlight
        curses.init_pair(4, curses.COLOR_GREEN, -1)     # Selected
        curses.init_pair(5, curses.COLOR_RED, -1)       # Error
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE) # Menu box

    def display_menu(self):
        """
        Displays the main menu and returns the selected categories or None if exited.
        """
        return curses.wrapper(self._main_menu)

    def _main_menu(self, stdscr):
        """
        Internal method to render the main menu.
        """
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()

        # Draw ASCII art logo at the top with color
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

            # Draw menu items (no blue background)
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

    def display_loading(self, fetching=False):
        """
        Displays a stylized loading screen with technical messages and spinner.
        """
        curses.wrapper(self._loading_screen, fetching)

    def _loading_screen(self, stdscr, fetching):
        """
        Internal method for the loading screen animation.
        """
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()
        messages = [
            "[gonkware] Initializing trivia subsystem...",
            "[gonkware] Allocating session token buffer...",
            "[gonkware] Connecting to Open Trivia DB @ 104.21.234.61:443...",
            "[gonkware] Performing TLS handshake...",
            "[gonkware] HTTP GET /api_token.php?command=request",
            "[gonkware] Session token received.",
            "[gonkware] Setting up category cache...",
            "[gonkware] HTTP GET /api_category.php",
            "[gonkware] Parsing category list...",
            "[gonkware] Building question request queue...",
            "[gonkware] Checking API rate limits...",
            "[gonkware] Spawning worker thread [pid 1423]...",
            "[gonkware] Allocating question buffer...",
            "[gonkware] HTTP GET /api.php?amount=10&type=multiple&category=...",
            "[gonkware] Waiting for API rate limit (5s)...",
            "[gonkware] HTTP 200 OK",
            "[gonkware] Decoding JSON payload...",
            "[gonkware] Extracting questions...",
            "[gonkware] Validating question objects...",
            "[gonkware] Shuffling question buffer...",
            "[gonkware] Initializing answer cache...",
            "[gonkware] Setting up game state...",
            "[gonkware] Loading UI theme...",
            "[gonkware] Checking system entropy...",
            "[gonkware] Trivia engine ready.",
        ]
        y_start = 2
        x_left = 2
        spinner = ['|', '/', '-', '\\']
        for i, msg in enumerate(messages):
            y = y_start + i
            color = curses.color_pair(2) if i < len(messages) - 1 else curses.color_pair(4) | curses.A_BOLD
            stdscr.addstr(y, x_left, msg, color)
            stdscr.refresh()
            # Spinner animation for technical steps
            if fetching and ("Fetching questions" in msg or "Waiting for API rate limit" in msg or "HTTP GET" in msg):
                for spin in range(15):
                    stdscr.addstr(y, x_left + len(msg) + 2, spinner[spin % 4], curses.color_pair(3) | curses.A_BOLD)
                    stdscr.refresh()
                    time.sleep(0.08)
                stdscr.addstr(y, x_left + len(msg) + 2, " ", curses.color_pair(3))
            else:
                time.sleep(0.18 if i < len(messages) - 2 else 0.5)
        time.sleep(0.5)

    def render_game_state(self, game_state):
        """
        Renders the current game state (question, choices, score, lives).
        """
        if game_state.get("loading"):
            self.display_loading()
            return None
        return curses.wrapper(self._render, game_state)

    def _render(self, stdscr, game_state):
        """
        Internal method to render the question and choices.
        """
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

    def get_user_input(self):
        """
        Not needed, handled in render_game_state.
        """
        pass

    def display_loading_and_fetch(self, engine):
        """
        Displays the animated loading screen and fetches questions per category.
        """
        curses.wrapper(self._loading_and_fetch, engine)

    def _loading_and_fetch(self, stdscr, engine):
        """
        Internal method for loading screen with real-time question fetching.
        """
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()
        categories = engine.categories
        total = len(categories)
        all_questions = []
        spinner = ['|', '/', '-', '\\']
        messages = [
            "[gonkware] Initializing trivia subsystem...",
            "[gonkware] Allocating session token buffer...",
            "[gonkware] Connecting to Open Trivia DB...",
            "[gonkware] Building question request queue...",
            "[gonkware] Fetching questions from categories...",
        ]
        x_left = 2
        y_start = 2

        # Show initial messages at the top left
        for i, msg in enumerate(messages):
            y = y_start + i
            stdscr.addstr(y, x_left, msg, curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.25)

        # Fetch questions per category with progress
        category_map = {str(cat['id']): cat['name'] for cat in fetch_categories()}
        for idx, cat in enumerate(categories):
            cat_name = category_map.get(str(cat), f"Category {cat}")
            msg = f"[gonkware] Fetching: {cat_name} [{idx+1}/{total}]"
            y = y_start + len(messages) + idx
            stdscr.addstr(y, x_left, msg, curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()
            # Spinner animation while fetching
            for spin in range(20):
                stdscr.addstr(y, x_left + len(msg) + 2, spinner[spin % 4], curses.color_pair(4) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(0.08)
            stdscr.addstr(y, x_left + len(msg) + 2, " ", curses.color_pair(4))
            # Actually fetch questions for this category
            url = f"https://opentdb.com/api.php?amount=10&type=multiple&category={cat}&token={engine.token}"
            response = requests.get(url)
            data = response.json()
            questions = data.get("results", [])
            all_questions.extend(questions)
            stdscr.addstr(y, x_left + len(msg) + 5, f"[{len(questions)} loaded]", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.2)
            if idx < total - 1:
                # Rate limit message on a new line, top left
                rate_msg = "[gonkware] Waiting 5 seconds to avoid API rate limiting..."
                stdscr.addstr(y + 1, x_left, rate_msg, curses.color_pair(5))
                stdscr.refresh()
                time.sleep(5)
                stdscr.addstr(y + 1, x_left, " " * len(rate_msg), curses.color_pair(5))  # Clear after wait

        # Shuffle and assign questions
        random.shuffle(all_questions)
        engine.questions = all_questions
        engine.current_index = 0

        # Final message at the top left
        final_msg = "[gonkware] Trivia engine ready."
        y = y_start + len(messages) + total + 2
        stdscr.addstr(y, x_left, final_msg, curses.color_pair(4) | curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1)