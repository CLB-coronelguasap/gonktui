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

def fetch_categories_with_progress(stdscr=None):
    """
    Fetches trivia categories from the Open Trivia DB API.
    If stdscr is provided, shows a loading bar.
    """
    url = "https://opentdb.com/api_category.php"
    try:
        if stdscr:
            stdscr.clear()
            stdscr.border(0)
            msg = "Loading categories from Open Trivia DB..."
            max_y, max_x = stdscr.getmaxyx()
            stdscr.addstr(max_y // 2 - 1, max_x // 2 - len(msg) // 2, msg, curses.A_BOLD)
            stdscr.refresh()
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return data.get("trivia_categories", [])
    except Exception:
        return []

class TUI:
    """
    Text User Interface class for the Game.
    Handles menus, category selection, loading screens, and game rendering.
    """
    def __init__(self):
        self.screen = None
        self.selected_categories = set()
        self.difficulty_options = ["Any", "Easy", "Medium", "Hard"]
        # Map display names to API values
        self.difficulty_api_map = {"Any": "", "Easy": "easy", "Medium": "medium", "Hard": "hard"}
        self.difficulty = "Any" # Default difficulty
        self.load_preferences()

    def load_preferences(self):
        """
        Loads user category and difficulty preferences from a local file.
        """
        if os.path.exists(PREFS_FILE):
            try:
                with open(PREFS_FILE, "r") as f:
                    data = json.load(f)
                    self.selected_categories = set(data.get("categories", []))
                    loaded_difficulty = data.get("difficulty", "Any")
                    if loaded_difficulty in self.difficulty_options:
                        self.difficulty = loaded_difficulty
                    else:
                        self.difficulty = "Any" # Fallback if loaded value is invalid
            except Exception:
                self.selected_categories = set()
                self.difficulty = "Any"

    def save_preferences(self):
        """
        Saves user category and difficulty preferences to a local file.
        """
        try:
            with open(PREFS_FILE, "w") as f:
                json.dump({
                    "categories": list(self.selected_categories),
                    "difficulty": self.difficulty
                }, f)
        except Exception:
            pass

    def _init_colors(self):
        """
        Initializes color pairs for TUI, For colorizing.
        """
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)      # Logo
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)   # Subtitle
        curses.init_pair(3, curses.COLOR_YELLOW, -1)    # Highlight
        curses.init_pair(4, curses.COLOR_GREEN, -1)     # Selected / Info
        curses.init_pair(5, curses.COLOR_RED, -1)       # Error
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE) # Menu box
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN) # Horizontal selector highlight
        curses.init_pair(8, curses.COLOR_WHITE, -1) # Horizontal selector unselected

    def display_menu(self):
        """
        Displays the main menu and returns the selected categories or None if exited.
        """
        return curses.wrapper(self._main_menu)

    def _draw_logo_and_subtitle(self, stdscr):
        """Draws the ASCII art logo and subtitle at the top of the screen."""
        max_y, max_x = stdscr.getmaxyx()
        for i, line in enumerate(GONKWARE_ART):
            stdscr.addstr(2 + i, max_x // 2 - len(line) // 2, line, curses.color_pair(1) | curses.A_BOLD)
        subtitle = "Welcome to GONKWARE Trivia!"
        subtitle_y = 2 + len(GONKWARE_ART) + 1
        stdscr.addstr(subtitle_y, max_x // 2 - len(subtitle) // 2, subtitle, curses.color_pair(2) | curses.A_BOLD)
        return subtitle_y

    def _main_menu(self, stdscr):
        """
        Internal method to render the main menu.
        """
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()
        menu_items = ["[Start Game]", "[Select Categories]", "[Exit]"]
        idx = 0

        while True:
            stdscr.clear()
            stdscr.border(0)
            subtitle_y = self._draw_logo_and_subtitle(stdscr)

            # Draw menu box border
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
        """Displays the category and difficulty selection menu."""
        self._init_colors()
        stdscr.clear()
        stdscr.border(0)
        max_y, max_x = stdscr.getmaxyx()

        # Show loading screen while fetching categories
        categories = fetch_categories_with_progress(stdscr)
        menu_items = [cat["name"] for cat in categories]
        category_ids = [cat["id"] for cat in categories]
        category_idx = 0
        category_scroll = 0
        difficulty_idx = self.difficulty_options.index(self.difficulty)
        category_box_top = 6
        category_box_left = max_x // 2 - 30
        category_box_width = 60
        visible_category_items = max(1, max_y - category_box_top - 12)
        category_box_height = visible_category_items + 4
        focus_on_difficulty = False

        warning_msg = "Warning: More categories = longer loading time!"
        info_msg = "Some categories may return zero questions."

        def redraw():
            # Only redraw the parts that change
            stdscr.erase()
            stdscr.border(0)
            # Warning about loading time
            stdscr.addstr(2, max_x // 2 - len(warning_msg) // 2, warning_msg, curses.color_pair(5) | curses.A_BOLD)
            stdscr.addstr(3, max_x // 2 - len(info_msg) // 2, info_msg, curses.color_pair(2) | curses.A_DIM)
            stdscr.addstr(4, max_x // 2 - 10, "Select Categories", curses.color_pair(2) | curses.A_BOLD)
            # Category box border
            for y in range(category_box_top, category_box_top + category_box_height):
                if y == category_box_top or y == category_box_top + category_box_height - 1:
                    stdscr.addstr(y, category_box_left, "+" + "-" * (category_box_width - 2) + "+")
                else:
                    stdscr.addstr(y, category_box_left, "|" + " " * (category_box_width - 2) + "|")
            stdscr.addstr(category_box_top, category_box_left + 2, "Use SPACE to toggle. ENTER to return.", curses.color_pair(1) | curses.A_DIM)
            stdscr.addstr(category_box_top + 1, category_box_left + 2, "UP/DOWN: categories, LEFT/RIGHT: difficulty.", curses.color_pair(1) | curses.A_DIM)
            # Category selection
            for i in range(visible_category_items):
                item_idx = category_scroll + i
                if item_idx >= len(menu_items):
                    break
                item = menu_items[item_idx]
                x = category_box_left + 4
                y = category_box_top + 3 + i
                cat_id = category_ids[item_idx]
                prefix = "[x] " if cat_id in self.selected_categories else "[ ] "
                display = prefix + item
                attr = curses.color_pair(3) | curses.A_BOLD if item_idx == category_idx and not focus_on_difficulty else curses.color_pair(4)
                stdscr.addstr(y, x, display[:category_box_width - 8], attr)
            # Difficulty selector
            difficulty_label = "Difficulty:"
            difficulty_label_y = category_box_top + category_box_height + 2
            difficulty_label_x = max_x // 2 - (len(difficulty_label) + sum(len(opt) for opt in self.difficulty_options) + (len(self.difficulty_options) - 1) * 3) // 2
            stdscr.addstr(difficulty_label_y, difficulty_label_x, difficulty_label, curses.color_pair(2) | curses.A_BOLD)
            current_x = difficulty_label_x + len(difficulty_label) + 2
            for i, option in enumerate(self.difficulty_options):
                if i == difficulty_idx and focus_on_difficulty:
                    stdscr.addstr(difficulty_label_y, current_x, f"< {option} >", curses.color_pair(7) | curses.A_BOLD)
                    current_x += len(option) + 5
                else:
                    stdscr.addstr(difficulty_label_y, current_x, f"  {option}  ", curses.color_pair(8))
                    current_x += len(option) + 5
            stdscr.refresh()

        redraw()
        while True:
            key = stdscr.getch()
            changed = False
            if key in [curses.KEY_UP, ord('k')]:
                if focus_on_difficulty:
                    focus_on_difficulty = False
                else:
                    if category_idx > 0:
                        category_idx -= 1
                        if category_idx < category_scroll:
                            category_scroll -= 1
                        changed = True
            elif key in [curses.KEY_DOWN, ord('j')]:
                if not focus_on_difficulty:
                    if category_idx < len(menu_items) - 1:
                        category_idx += 1
                        if category_idx >= category_scroll + visible_category_items:
                            category_scroll += 1
                        changed = True
            elif key == curses.KEY_LEFT:
                if focus_on_difficulty:
                    difficulty_idx = (difficulty_idx - 1 + len(self.difficulty_options)) % len(self.difficulty_options)
                    changed = True
                else:
                    focus_on_difficulty = True
                    changed = True
            elif key == curses.KEY_RIGHT:
                if focus_on_difficulty:
                    difficulty_idx = (difficulty_idx + 1) % len(self.difficulty_options)
                    changed = True
                else:
                    focus_on_difficulty = True
                    changed = True
            elif key == ord(' '):
                if not focus_on_difficulty:
                    cat_id = category_ids[category_idx]
                    if cat_id in self.selected_categories:
                        self.selected_categories.remove(cat_id)
                    else:
                        self.selected_categories.add(cat_id)
                    changed = True
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                self.difficulty = self.difficulty_options[difficulty_idx]
                self.save_preferences()
                break
            if changed:
                redraw()
        stdscr.clear()
        stdscr.border(0)

    def display_loading(self, fetching=False):
        """
        Displays loading screen with faux technical looking messages.
        """
        curses.wrapper(self._loading_screen, fetching)

    def _loading_screen(self, stdscr, fetching):
        """
        Internal method for animating the loading screen (I believe this is now obsolete, but keep it in incase it isn't.
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
        Internal method to render the question and choices, and show feedback after answering.
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
        correct_answer = html.unescape(game_state["correct_answer"])
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
        stdscr.timeout(10000)  # 10 seconds timer
        start_time = time.time()
        answer = None
        while True:
            for i, choice in enumerate(choices):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                safe_addstr(8 + i, 6, f"{i+1}. {choice}", attr)
            remaining = max(0, 10 - int(time.time() - start_time))
            safe_addstr(8 + len(choices) + 2, 6, f"Time left: {remaining} seconds", curses.A_DIM)
            stdscr.refresh()
            key = stdscr.getch()
            if key == -1:  # Timeout
                return None
            if key in [curses.KEY_UP, ord('k')]:
                selected = (selected - 1) % len(choices)
            elif key in [curses.KEY_DOWN, ord('j')]:
                selected = (selected + 1) % len(choices)
            elif key in [curses.KEY_ENTER, ord('\n'), ord('\r')]:
                answer = choices[selected]
                break

        # Show feedback screen
        stdscr.clear()
        stdscr.border()
        is_correct = (answer == correct_answer)
        tick = "✔" if is_correct else "✖"
        tick_color = curses.color_pair(4) if is_correct else curses.color_pair(5)
        feedback = "Correct!" if is_correct else "Incorrect!"
        safe_addstr(4, max_x // 2 - 2, tick, tick_color | curses.A_BOLD)
        safe_addstr(6, max_x // 2 - len(feedback) // 2, feedback, tick_color | curses.A_BOLD)
        safe_addstr(8, max_x // 2 - 15, f"Your answer:   {answer}", curses.color_pair(3 if is_correct else 5))
        safe_addstr(9, max_x // 2 - 15, f"Correct answer: {correct_answer}", curses.color_pair(4))
        safe_addstr(11, max_x // 2 - 12, "Press any key to continue...", curses.A_DIM)
        stdscr.refresh()
        stdscr.timeout(-1)
        stdscr.getch()
        return answer

    def get_user_input(self):
        """
        Not needed, handled in render_game_state, this is just in case I need it \(CLEANUP NEEDED\).
        """
        pass

    def display_loading_and_fetch(self, engine):
        """
        Displays the animated loading screen and fetches questions per category.
        Skips categories that return zero questions and shows a warning.
        """
        curses.wrapper(self._loading_and_fetch, engine)

    def _loading_and_fetch(self, stdscr, engine):
        """
        Internal method for loading screen, with robust fetching for categories that may return zero questions.
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

        # Show initial messages
        for i, msg in enumerate(messages):
            y = y_start + i
            stdscr.addstr(y, x_left, msg, curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.15)

        # Fetch questions per category with progress and fallback logic
        category_map = {str(cat['id']): cat['name'] for cat in fetch_categories()}
        zero_q_cats = []
        for idx, cat in enumerate(categories):
            cat_name = category_map.get(str(cat), f"Category {cat}")
            msg = f"[gonkware] Fetching: {cat_name} [{idx+1}/{total}]"
            y = y_start + len(messages) + idx
            stdscr.addstr(y, x_left, msg, curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()
            for spin in range(10):
                stdscr.addstr(y, x_left + len(msg) + 2, spinner[spin % 4], curses.color_pair(4) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(0.05)
            stdscr.addstr(y, x_left + len(msg) + 2, " ", curses.color_pair(4))

            # 1. Try with selected difficulty
            difficulty_param = self.difficulty_api_map.get(self.difficulty, "")
            url = f"https://opentdb.com/api.php?amount=10&type=multiple&category={cat}&token={engine.token}"
            if difficulty_param:
                url += f"&difficulty={difficulty_param}"
            response = requests.get(url)
            data = response.json()
            questions = data.get("results", [])

            # 2. If zero, try with "Any" difficulty
            if not questions and difficulty_param:
                url_any = f"https://opentdb.com/api.php?amount=10&type=multiple&category={cat}&token={engine.token}"
                response = requests.get(url_any)
                data = response.json()
                questions = data.get("results", [])

            # 3. If still zero, try with 5 questions
            if not questions:
                url_five = f"https://opentdb.com/api.php?amount=5&type=multiple&category={cat}&token={engine.token}"
                response = requests.get(url_five)
                data = response.json()
                questions = data.get("results", [])

            # 4. If still zero, warn but include category
            if not questions:
                zero_q_cats.append(cat_name)
                stdscr.addstr(y, x_left + len(msg) + 5, "[0 loaded]", curses.color_pair(5) | curses.A_BOLD)
            else:
                all_questions.extend(questions)
                stdscr.addstr(y, x_left + len(msg) + 5, f"[{len(questions)} loaded]", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.1)
            if idx < total - 1:
                rate_msg = "[gonkware] Waiting 2s to avoid API rate limiting..."
                stdscr.addstr(y + 1, x_left, rate_msg, curses.color_pair(5))
                stdscr.refresh()
                time.sleep(2)
                stdscr.addstr(y + 1, x_left, " " * len(rate_msg), curses.color_pair(5))
        random.shuffle(all_questions)
        engine.questions = all_questions
        engine.current_index = 0
        y = y_start + len(messages) + total + 2
        if zero_q_cats:
            warn = "Warning: No questions for: " + ", ".join(zero_q_cats)
            stdscr.addstr(y, x_left, warn[:max_x-4], curses.color_pair(5) | curses.A_BOLD)
            y += 2
        final_msg = "[gonkware] Trivia engine ready."
        stdscr.addstr(y, x_left, final_msg, curses.color_pair(4) | curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1)
