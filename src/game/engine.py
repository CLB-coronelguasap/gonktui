import requests
import random
import time


class GameEngine:
    def __init__(self, categories=None):
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.lives = 5
        self.categories = categories or []
        self.token = self.get_token()

    def get_token(self):
        print("[*] Requesting session token...")
        resp = requests.get("https://opentdb.com/api_token.php?command=request")
        data = resp.json()
        token = data.get("token")
        print(f"[*] Received token: {token}")
        return token

    def start_game(self):
        self.lives = 5
        self.score = 0
        self.current_index = 0
        self.fetch_questions()

    def fetch_questions(self, amount=10):
        all_questions = []
        if self.categories:
            for cat in self.categories:
                url = f"https://opentdb.com/api.php?amount={amount}&type=multiple&category={cat}&token={self.token}"
                response = requests.get(url)
                data = response.json()
                questions = data.get("results", [])
                all_questions.extend(questions)
                time.sleep(5)
        else:
            url = f"https://opentdb.com/api.php?amount={amount}&type=multiple&token={self.token}"
            response = requests.get(url)
            data = response.json()
            all_questions = data.get("results", [])
        random.shuffle(all_questions)
        self.questions = all_questions
        self.current_index = 0

    def update(self):
        # Only fetch if there are no questions and lives remain
        if not self.questions and self.lives > 0:
            self.fetch_questions()
        # If out of questions but still have lives, fetch more
        elif self.current_index >= len(self.questions) and self.lives > 0:
            self.questions = []
            self.fetch_questions()
            self.current_index = 0

    def get_game_state(self):
        if self.lives <= 0:
            return {"finished": True, "score": self.score, "lives": self.lives}
        if not self.questions:
            return {"loading": True, "score": self.score, "lives": self.lives}
        if self.current_index < len(self.questions):
            q = self.questions[self.current_index]
            return {
                "question": q["question"],
                "choices": q["incorrect_answers"] + [q["correct_answer"]],
                "score": self.score,
                "index": self.current_index + 1,
                "total": len(self.questions),
                "lives": self.lives,
                "correct_answer": q["correct_answer"],
            }
        else:
            # Out of questions, but update() will fetch more
            return {"loading": True, "score": self.score, "lives": self.lives}

    def handle_input(self, user_input, correct_answer):
        if self.lives <= 0 or self.current_index >= len(self.questions):
            return
        if user_input is None:
            self.lives -= 1
        else:
            if user_input.strip().lower() == correct_answer.strip().lower():
                self.score += 1
            else:
                self.lives -= 1
        self.current_index += 1
