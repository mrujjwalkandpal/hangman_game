import tkinter as tk
from tkinter import Entry
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import os
import random
import json
from datetime import datetime

# =============================================================================
# CLASS: GAME SCREEN (UI Rendering)
# =============================================================================
class GameScreen:
    def __init__(self, app):
        self.app = app
        self.canvas = app.canvas
        self.assets = app.assets
        self.scale = app.scale
        
        self.active_tooltip = None
        self.load_game_assets()

    # ---------------------------------------------------
    # LOAD ASSETS
    # ---------------------------------------------------
    def load_game_assets(self):
        base = getattr(self.app, "base_path", os.path.dirname(os.path.abspath(__file__)))

        # 1. Background
        bg_path = os.path.join(base, "background2.png")
        if os.path.exists(bg_path):
            img = Image.open(bg_path).resize((self.app.screen_width, self.app.screen_height), Image.Resampling.LANCZOS)
            self.assets["game_bg"] = ImageTk.PhotoImage(img)

        # 2. Hangman Stages
        h_h = int(self.app.screen_height * 0.80) 
        for i in range(1, 8):
            path = os.path.join(base, f"{i}.png")
            if os.path.exists(path):
                img = Image.open(path)
                ratio = img.width / img.height
                new_w = int(h_h * ratio)
                img = img.resize((new_w, h_h), Image.Resampling.LANCZOS)
                self.assets[f"hang_{i-1}"] = ImageTk.PhotoImage(img)

        # 3. Hearts
        for name in ["heart_filled", "heart_empty"]:
            path = os.path.join(base, f"{name}.png")
            if os.path.exists(path):
                size = int(32 * self.scale) 
                img = Image.open(path).resize((size, size), Image.Resampling.NEAREST)
                self.assets[name] = ImageTk.PhotoImage(img)

        # 4. Powerup Buttons
        btn_w = int(130 * self.scale)
        btn_h = int(110 * self.scale)
        boost_w = int(btn_w * 1.15)
        boost_h = int(btn_h * 1.15)

        for name in ["roulette", "freeze", "duality", "reveal", "filter"]:
            path = os.path.join(base, f"{name}_btn.png")
            if os.path.exists(path):
                raw_img = Image.open(path)
                img_std = raw_img.resize((btn_w, btn_h), Image.Resampling.LANCZOS)
                self.assets[f"icon_{name}_std"] = ImageTk.PhotoImage(img_std)
                img_hover = raw_img.resize((boost_w, boost_h), Image.Resampling.LANCZOS)
                self.assets[f"icon_{name}_hover"] = ImageTk.PhotoImage(img_hover)
                desaturator = ImageEnhance.Color(img_std)
                img_grey = desaturator.enhance(0.0)
                self.assets[f"icon_{name}_grey"] = ImageTk.PhotoImage(img_grey)

        # 5. Exit Button
        path = os.path.join(base, "exit_game_btn.png")
        if os.path.exists(path):
            size = int(50 * self.scale)
            img = Image.open(path).resize((size, size), Image.Resampling.LANCZOS)
            self.assets["exit_btn"] = ImageTk.PhotoImage(img)

        # 6. Generate Overlays
        self.generate_overlays()

    def generate_overlays(self):
        w, h = self.app.screen_width, self.app.screen_height
        
        red_ov = Image.new("RGBA", (w, h), (200, 0, 0, 0)) 
        draw_r = ImageDraw.Draw(red_ov)
        draw_r.rectangle([0, 0, w, h], fill=(139, 0, 0, 100))
        self.assets["overlay_red"] = ImageTk.PhotoImage(red_ov)

        green_ov = Image.new("RGBA", (w, h), (0, 200, 0, 0))
        draw_g = ImageDraw.Draw(green_ov)
        draw_g.rectangle([0, 0, w, h], fill=(0, 100, 0, 100)) 
        self.assets["overlay_green"] = ImageTk.PhotoImage(green_ov)

    # ---------------------------------------------------
    # DRAW FULL SCENE
    # ---------------------------------------------------
    def draw(self):
        self.app.clear_screen()
        self.app.current_state = "GAME"
        w, h = self.app.screen_width, self.app.screen_height

        if "game_bg" in self.assets:
            self.canvas.create_image(0, 0, image=self.assets["game_bg"], anchor="nw")

        split_x = int(w * 0.38)
        btn_strip_x = int(w * 0.85)
        self.paper_cx = split_x + (btn_strip_x - split_x) // 2
        left_cx = split_x // 2 + 25 
        
        # --- ADDED TAG 'main_hangman' FOR OPTIMIZED UPDATES ---
        hang_y = int(h * 0.55) 
        hang_key = f"hang_{self.app.wrong_guesses}"
        if hang_key in self.assets:
            self.canvas.create_image(left_cx, hang_y, image=self.assets[hang_key], tags="main_hangman")

        self.canvas.create_text(
            left_cx, h * 0.88,
            text=f"Score: {self.app.score}",
            fill="black", 
            font=("Ubuntu", int(28 * self.scale), "bold"),
            tags="score_text"  # Added tag
        )

        margin = int(25 * self.scale)
        if "exit_btn" in self.assets:
            img_id = self.canvas.create_image(w - margin, margin, image=self.assets["exit_btn"], anchor="ne", tags="exit_btn")
            self.canvas.tag_bind("exit_btn", "<Button-1>", lambda e: self.app.draw_main_menu())

        # 1. WORD
        word_y = int(h * 0.18)
        self.draw_responsive_word(self.paper_cx, word_y, btn_strip_x - split_x)
        
        # 2. HINT
        hint_y = word_y + int(60 * self.scale)
        self.canvas.create_text(
            self.paper_cx, hint_y,
            text=f"Hint: {self.app.current_hint}",
            fill="#555",
            font=("Ubuntu", int(15 * self.scale), "italic"),
            width=int((btn_strip_x - split_x) * 0.9),
            justify="center"
        )

        # 3. STATUS / HELP
        status_y = hint_y + int(60 * self.scale)
        status_text = ""
        status_color = "#333333"
        status_font_w = "normal"
        
        if self.app.roulette_step == "waiting_for_guess":
             status_text = "GAMBLE ACTIVE: Correct = +1 Lifelines | Wrong = -1 Lifelines"
             status_color = "#c0392b"
             status_font_w = "bold"
        elif self.app.duality_active:
             status_text = "SHIELD ACTIVE: Next wrong guess ignored!"
             status_color = "#27ae60"
             status_font_w = "bold"
        elif self.active_tooltip: 
             status_text = self.active_tooltip
             status_color = "#2980b9"
        
        self.canvas.create_text(
            self.paper_cx, status_y,
            text=status_text,
            fill=status_color,
            font=("Ubuntu", int(14 * self.scale), status_font_w),
            width=int((btn_strip_x - split_x) * 0.9),
            justify="center",
            tags="status_area"
        )

        # 4. KEYBOARD
        self.keyboard_y = int(h * 0.55)
        self.max_kb_width = (btn_strip_x - split_x) * 0.85 
        self.draw_themed_keyboard(self.paper_cx, self.keyboard_y, self.max_kb_width)

        # 5. HEARTS - ADDED TAGS FOR OPTIMIZATION
        hearts_y = int(h * 0.80)
        gap = int(45 * self.scale)
        start_hearts_x = self.paper_cx - (6 * gap) // 2 + (gap // 2)
        
        hp = 6 - self.app.wrong_guesses
        for i in range(6):
            key = "heart_filled" if i < hp else "heart_empty"
            if key in self.assets:
                self.canvas.create_image(
                    start_hearts_x + (i * gap), hearts_y, 
                    image=self.assets[key],
                    tags=f"heart_{i}" # Tag added for updating
                )

        # 6. TIMER
        if self.app.game_mode == "Hardest":
            timer_y = int(h * 0.90)
            t_color = "#c0392b" if self.app.time_left <= 5 else "black"
            timer_text = f"Time: {self.app.time_left}s"
            if self.app.freeze_active:
                 timer_text += " (FROZEN)"
                 t_color = "#2980b9"
            self.canvas.create_text(
                self.paper_cx, timer_y,
                text=timer_text, fill=t_color,
                font=("Ubuntu", int(24 * self.scale), "bold")
            )

        # 3. Powerups
        btn_cx = btn_strip_x + (w - btn_strip_x) // 2
        btn_start_y = int(h * 0.35) 
        self.draw_powerups_vertical(btn_cx, btn_start_y)

    def draw_responsive_word(self, cx, y, container_width):
        self.canvas.delete("word_layer")
        word_len = len(self.app.current_word)
        base_size = 55 
        
        if word_len > 10:
            font_size = int(base_size * (10 / word_len))
        else:
            font_size = base_size
            
        font_size = max(int(font_size * self.scale), 20)
        
        display_text = " ".join([l if l in self.app.guessed_letters else "_" for l in self.app.current_word])
        
        self.canvas.create_text(
            cx, y,
            text=display_text,
            fill="black",
            font=("Ubuntu", font_size, "bold"),
            tags="word_layer"
        )

    # ---------------------------------------------------
    # INITIAL KEYBOARD DRAWING (Only called once per game load)
    # ---------------------------------------------------
    def draw_themed_keyboard(self, cx, cy, max_width):
        self.canvas.delete("keyboard_layer")
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        base_key_size = 45 * self.scale 
        key_w = int(base_key_size); key_h = int(base_key_size); gap = int(10 * self.scale)
        
        row_max_chars = 10
        total_w_needed = row_max_chars * (key_w + gap)
        if total_w_needed > max_width:
            ratio = max_width / total_w_needed
            key_w = int(key_w * ratio); key_h = int(key_h * ratio); gap = int(gap * ratio)

        c_paper = "#f7f1e3"; c_ink = "#2f3542"; c_hover = "#ffeaa7"
        c_correct = "#55efc4"; c_wrong = "#ff7675"; c_used = "#dfe6e9"
        c_outline = "#a4b0be"; c_shadow = "#b2bec3"

        total_h = 3 * (key_h + gap)
        start_y = cy - total_h // 2

        for r_i, row_str in enumerate(rows):
            row_width = len(row_str) * (key_w + gap) - gap
            row_start_x = cx - row_width // 2
            
            for k_i, char in enumerate(row_str):
                x = row_start_x + k_i * (key_w + gap)
                y = start_y + r_i * (key_h + gap)
                
                group_tag = f"key_{char}"
                bg_tag = f"key_bg_{char}"
                
                bg_color = c_paper; fg_color = c_ink; outline_color = c_outline
                if char in self.app.guessed_letters:
                    outline_color = bg_color 
                    if char in self.app.current_word: bg_color = c_correct; fg_color = "white"
                    else: bg_color = c_wrong; fg_color = "white"
                elif char in self.app.disabled_keys:
                    bg_color = c_used; fg_color = "#b2bec3"

                self.canvas.create_rectangle(x+3, y+3, x+key_w+3, y+key_h+3, fill=c_shadow, outline="", tags=(group_tag, "keyboard_layer"))
                self.canvas.create_rectangle(x, y, x+key_w, y+key_h, fill=bg_color, outline=outline_color, width=1, tags=(group_tag, bg_tag, "keyboard_layer"))
                self.canvas.create_text(x+key_w/2, y+key_h/2, text=char, fill=fg_color, font=("Ubuntu", int(18 * self.scale), "bold"), tags=(group_tag, "keyboard_layer"))
                
                if char not in self.app.guessed_letters and char not in self.app.disabled_keys:
                    if hasattr(self.app, "handle_guess"):
                        self.canvas.tag_bind(group_tag, "<Button-1>", lambda e, c=char: self.app.handle_guess(c))
                    
                    def enter(e, t=bg_tag, b=bg_color): 
                        if b == c_paper: self.canvas.itemconfig(t, fill=c_hover)
                    def leave(e, t=bg_tag, b=bg_color): 
                        self.canvas.itemconfig(t, fill=b)
                    self.canvas.tag_bind(group_tag, "<Enter>", enter)
                    self.canvas.tag_bind(group_tag, "<Leave>", leave)

    # ---------------------------------------------------
    # NEW OPTIMIZED UPDATE FUNCTIONS (FIX FOR LAG)
    # ---------------------------------------------------
    def update_key_visual(self, char):
        # 1. Determine Color
        c_correct = "#55efc4"
        c_wrong = "#ff7675"
        
        bg_tag = f"key_bg_{char}"
        group_tag = f"key_{char}"
        
        if char in self.app.current_word:
            new_bg = c_correct
        else:
            new_bg = c_wrong
            
        # 2. Update Canvas Items (Instant)
        self.canvas.itemconfig(bg_tag, fill=new_bg, outline=new_bg)
        
        # 3. Find text item inside group and make it white
        # We rely on tag matching. The text item shares the 'key_char' tag.
        # But so does the background. However, text has a 'text' attribute, rect doesn't.
        # Simpler: Just config all items with that tag to have white fill, 
        # but rectangles ignore text-fill colors usually.
        # Safest way without complex ID lookups is just re-tagging properly or assuming standard behavior.
        # Actually, let's just use the group tag to unbind events first.
        
        self.canvas.tag_unbind(group_tag, "<Button-1>")
        self.canvas.tag_unbind(group_tag, "<Enter>")
        self.canvas.tag_unbind(group_tag, "<Leave>")
        
        # Make the text white. We iterate items with the group tag to find the text one.
        items = self.canvas.find_withtag(group_tag)
        for item in items:
            type_ = self.canvas.type(item)
            if type_ == "text":
                self.canvas.itemconfig(item, fill="white")
    
    def update_hangman_ui(self):
        # 1. Update Hangman Image
        hang_key = f"hang_{self.app.wrong_guesses}"
        if hang_key in self.assets:
            self.canvas.itemconfig("main_hangman", image=self.assets[hang_key])
            
        # 2. Update Hearts
        hp = 6 - self.app.wrong_guesses
        for i in range(6):
            key = "heart_filled" if i < hp else "heart_empty"
            if key in self.assets:
                self.canvas.itemconfig(f"heart_{i}", image=self.assets[key])
                
        # 3. Update Score text (in case logic changes score)
        self.canvas.itemconfig("score_text", text=f"Score: {self.app.score}")

    # ---------------------------------------------------

    def show_roulette_intro(self):
        if "overlay_red" in self.assets:
            self.canvas.create_image(0, 0, image=self.assets["overlay_red"], anchor="nw", tags="roulette_fx")
        cx, cy = self.app.screen_width // 2, self.app.screen_height // 2
        self.canvas.create_text(
            cx, cy, text="GAMBLE ACTIVATED", fill="#8B0000",
            font=("Chiller", int(60 * self.scale), "bold"), tags="roulette_fx"
        )

    def show_roulette_result(self, won):
        self.canvas.delete("roulette_fx") 
        overlay = "overlay_green" if won else "overlay_red"
        text = "ROULETTE WON!" if won else "ROULETTE LOST!"
        color = "#00FF00" if won else "#FF0000"
        
        if overlay in self.assets:
            self.canvas.create_image(0, 0, image=self.assets[overlay], anchor="nw", tags="roulette_res")
        cx, cy = self.app.screen_width // 2, self.app.screen_height // 2
        self.canvas.create_text(
            cx, cy, text=text, fill=color, 
            font=("Ubuntu", int(50 * self.scale), "bold"), tags="roulette_res"
        )

    def hide_overlays(self):
        self.canvas.delete("roulette_fx")
        self.canvas.delete("roulette_res")

    def draw_powerups_vertical(self, cx, start_y):
        names = ["roulette", "freeze", "duality", "reveal", "filter"]
        gap = int(75 * self.scale) 
        
        descriptions = {
            "roulette": "ROULETTE: 50/50 Chance. Win = +1 All Lifelines / Loss = -1 All Lifelines",
            "freeze": "FREEZE: Stops the timer for 5 seconds.",
            "duality": "DUALITY: Creates a shield. The next wrong guess is ignored.",
            "reveal": "REVEAL: Instantly uncovers one random correct letter.",
            "filter": "FILTER: Removes 3 incorrect letters from the keyboard."
        }

        current_idx = 0
        for name in names:
            if name == "freeze" and self.app.game_mode != "Hardest": continue

            y = start_y + current_idx * gap
            current_idx += 1 
            
            count = self.app.powerups.get(name, 0)
            btn_tag = f"btn_{name}"

            if count > 0:
                key_default = f"icon_{name}_std"
                key_hover = f"icon_{name}_hover"
            else:
                key_default = f"icon_{name}_grey"
                key_hover = None

            if key_default in self.assets:
                img_id = self.canvas.create_image(cx, y, image=self.assets[key_default], tags=btn_tag)
                
                if count > 0 and key_hover in self.assets:
                    if hasattr(self.app, "use_powerup"):
                          self.canvas.tag_bind(btn_tag, "<Button-1>", lambda e, n=name: self.app.use_powerup(n))
                    
                    img_normal_obj = self.assets[key_default]
                    img_hover_obj = self.assets[key_hover]
                    
                    def on_enter(e, _id=img_id, _img=img_hover_obj, _txt=descriptions[name]): 
                        self.canvas.itemconfig(_id, image=_img)
                        self.active_tooltip = _txt
                        self.update_help_text(_txt, "#2980b9")

                    def on_leave(e, _id=img_id, _img=img_normal_obj): 
                        self.canvas.itemconfig(_id, image=_img)
                        self.active_tooltip = None
                        self.update_help_text("", "#333")
                        if self.app.duality_active: self.update_help_text("SHIELD ACTIVE: Next wrong guess ignored!", "#27ae60")
                        if self.app.roulette_step == "waiting_for_guess": self.update_help_text("GAMBLE ACTIVE: Correct = +1 Lifelines | Wrong = -1 Lifelines", "#c0392b")

                    self.canvas.tag_bind(btn_tag, "<Enter>", on_enter)
                    self.canvas.tag_bind(btn_tag, "<Leave>", on_leave)

            if count >= 0:
                badge_x = cx + 35 * self.scale; badge_y = y - 20 * self.scale; r = 11 * self.scale
                self.canvas.create_oval(badge_x-r+2, badge_y-r+2, badge_x+r+2, badge_y+r+2, fill="#000000", outline="")
                self.canvas.create_oval(badge_x-r, badge_y-r, badge_x+r, badge_y+r, fill="#c0392b", outline="white", width=2)
                self.canvas.create_text(badge_x, badge_y, text=str(count), fill="white", font=("Ubuntu", int(11 * self.scale), "bold"))

    def update_help_text(self, text, color):
        self.canvas.delete("status_area")
        y = int(self.app.screen_height * 0.18) + int(60 * self.scale) + int(60 * self.scale)
        split_x = int(self.app.screen_width * 0.38)
        btn_strip_x = int(self.app.screen_width * 0.85)
        
        font_w = "bold" if text else "normal"
        self.canvas.create_text(
            self.paper_cx, y, text=text, fill=color,
            font=("Ubuntu", int(14 * self.scale), font_w),
            width=int((btn_strip_x - split_x) * 0.9), justify="center", tags="status_area"
        )


# =============================================================================
# CLASS: HANGMAN APP
# =============================================================================
class HangmanUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hangman Game")
        self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))

        ref_width = 900; ref_height = 650
        self.scale = min(self.screen_width / ref_width, self.screen_height / ref_height)

        self.canvas = tk.Canvas(root, width=self.screen_width, height=self.screen_height, highlightthickness=0, bg="#1a1a1a")
        self.canvas.pack(fill="both", expand=True)

        self.assets = {}
        self.words_data = {} 
        self.leaderboard_data = []
        self.load_words() 
        self.load_leaderboard()
        self.load_assets() 

        # Player Data
        self.player_name = ""
        self.entry_widget = None 

        # Game State
        self.game_mode = "Easy"
        self.score = 0
        self.streak = 0
        self.streak_counter = 0 
        self.current_word = ""
        self.current_hint = ""
        self.current_meaning = ""
        self.guessed_letters = []
        self.disabled_keys = []
        self.wrong_guesses = 0
        self.powerups = {"roulette": 1, "freeze": 1, "duality": 1, "reveal": 1, "filter": 1}
        
        self.time_left = 30
        self.timer_id = None
        self.freeze_active = False
        self.duality_active = False 
        self.roulette_step = "idle" 

        self.draw_main_menu()

    def get_path(self, filename): return os.path.join(self.base_path, filename)

    # --- LEADERBOARD & WORDS ---
    def load_words(self):
        try:
            with open(self.get_path("words.json"), "r") as f:
                self.words_data = json.load(f)
        except:
            self.words_data = {"Easy": [{"word": "APPLE", "meaning": "Red fruit", "hint": "Keeps doc away"}]}

    def load_leaderboard(self):
        try:
            with open(self.get_path("leaderboard.json"), "r") as f:
                self.leaderboard_data = json.load(f)
        except:
            self.leaderboard_data = []

    def update_leaderboard(self):
        if self.score > 0:
            entry = {"score": self.score, "mode": self.game_mode, "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "name": self.player_name}
            self.leaderboard_data.append(entry)
            self.leaderboard_data.sort(key=lambda x: x["score"], reverse=True)
            self.leaderboard_data = self.leaderboard_data[:10] 
            try:
                with open(self.get_path("leaderboard.json"), "w") as f:
                    json.dump(self.leaderboard_data, f)
            except: pass

    def save_leaderboard(self):
        # Already handled by update_leaderboard called in game_loss/close
        self.update_leaderboard()

    def get_word_by_difficulty(self, mode):
        key_map = {"Easiest": "Easy", "Medium": "Medium", "Hardest": "Hardest"}
        json_key = key_map.get(mode, "Easy")
        candidates = self.words_data.get(json_key, [])
        if not candidates: return ("ERROR", "Missing Data", "No Hint")
        choice = random.choice(candidates)
        return (choice["word"].upper(), choice["meaning"], choice.get("hint", "No hint available."))

    def load_assets(self):
        try:
            bg = Image.open(self.get_path("background.png")).resize((self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
            self.assets["bg"] = ImageTk.PhotoImage(bg)
        except: pass
        try:
            title = Image.open(self.get_path("hangman_title.png"))
            tw = int(self.screen_width * 0.69); th = int((title.height * tw) / title.width)
            self.assets["title"] = ImageTk.PhotoImage(title.resize((tw, th), Image.Resampling.LANCZOS))
        except: pass

        self.popup_w = int(self.screen_width * 0.7); self.popup_h = int(self.screen_height * 0.7)
        details_map = {"Easiest": "easiest_details.png", "Medium": "medium_details.png", "Hardest": "hardest_details.png"}
        for mode, fname in details_map.items():
            path = self.get_path(fname)
            if os.path.exists(path):
                self.assets[f"details_{mode}"] = ImageTk.PhotoImage(Image.open(path).resize((self.popup_w, self.popup_h), Image.Resampling.LANCZOS))

        for b in ["start", "rank", "info", "Easiest", "Medium", "Hardest", "play_next", "close", "try_again", "quit"]:
            self.load_btn_asset(b, f"{b.lower()}_btn.png", 0.8 if b in ["start", "rank", "info"] else 0.4 if b in ["Easiest", "Medium", "Hardest"] else 0.6)

    def load_btn_asset(self, name, filename, scale_fac):
        try:
            img = Image.open(self.get_path(filename))
            s = scale_fac * self.scale
            w, h = int(img.width * s * 0.5), int(img.height * s * 0.5)
            self.assets[f"{name}_norm"] = ImageTk.PhotoImage(img.resize((w, h), Image.Resampling.LANCZOS))
            self.assets[f"{name}_hover"] = ImageTk.PhotoImage(img.resize((int(w*1.05), int(h*1.05)), Image.Resampling.LANCZOS))
        except: pass

    # ---------------------------------------------------------
    # UI NAVIGATION
    # ---------------------------------------------------------
    def clear_screen(self):
        self.canvas.delete("all")
        if self.entry_widget: 
            self.entry_widget.destroy()
            self.entry_widget = None
        if "bg" in self.assets: self.canvas.create_image(0, 0, image=self.assets["bg"], anchor="nw")

    def create_btn(self, x, y, name, cmd, tag=None):
        if f"{name}_norm" not in self.assets: 
            t = tag if tag else "ui"
            self.canvas.create_text(x, y, text=f"[{name.upper()}]", fill="white", font=("Ubuntu", 20), tags=t)
            self.canvas.tag_bind(t, "<Button-1>", lambda e: cmd())
            return
        tag = tag if tag else f"btn_{id(cmd)}"
        bid = self.canvas.create_image(x, y, image=self.assets[f"{name}_norm"], tags=tag)
        self.canvas.tag_bind(bid, "<Button-1>", lambda e: cmd())
        self.canvas.tag_bind(bid, "<Enter>", lambda e: self.canvas.itemconfig(bid, image=self.assets[f"{name}_hover"]))
        self.canvas.tag_bind(bid, "<Leave>", lambda e: self.canvas.itemconfig(bid, image=self.assets[f"{name}_norm"]))

    def draw_main_menu(self):
        self.cancel_timer()
        self.clear_screen()
        self.score = 0 
        if "title" in self.assets:
            self.canvas.create_image(self.screen_width//2, int(self.screen_height*0.05), image=self.assets["title"], anchor="n")
        self.create_btn(self.screen_width//2, int(self.screen_height*0.58), "start", lambda: self.draw_difficulty_menu())
        self.create_btn(self.screen_width//2, int(self.screen_height*0.78), "rank", lambda: self.draw_leaderboard())
        self.create_btn(60*self.scale, self.screen_height-60*self.scale, "info", lambda: print("Info"))

    def draw_leaderboard(self):
        self.clear_screen()
        cx = self.screen_width // 2
        self.canvas.create_text(60*self.scale, 60*self.scale, text="< BACK", fill="white", font=("Ubuntu", int(20*self.scale), "bold"), tags="back")
        self.canvas.tag_bind("back", "<Button-1>", lambda e: self.draw_main_menu())

        self.canvas.create_text(cx, int(self.screen_height*0.1), text="HALL OF FAME", fill="#FFD700", font=("Ubuntu", int(40*self.scale), "bold"))
        
        panel_w = int(self.screen_width * 0.7)
        panel_h = int(self.screen_height * 0.7)
        panel_top = int(self.screen_height * 0.18)
        
        self.canvas.create_rectangle(
            cx - panel_w//2, panel_top, 
            cx + panel_w//2, panel_top + panel_h,
            fill="#1a1a1a", outline="#555", width=3, stipple="gray25"
        )

        header_y = panel_top + int(50*self.scale)
        col1 = cx - int(panel_w * 0.4) 
        col2 = cx - int(panel_w * 0.2) 
        col3 = cx + int(panel_w * 0.1) 
        col4 = cx + int(panel_w * 0.4) 
        
        headers = [("RANK", col1), ("NAME", col2), ("MODE", col3), ("SCORE", col4)]
        for txt, x_pos in headers:
            self.canvas.create_text(x_pos, header_y, text=txt, fill="#FFD700", font=("Ubuntu", 22, "bold"))
            
        line_y = header_y + int(30*self.scale)
        self.canvas.create_line(cx - panel_w//2 + 20, line_y, cx + panel_w//2 - 20, line_y, fill="#555", width=2)
        
        start_y = line_y + int(40*self.scale)
        gap = int(50 * self.scale)
        
        for i, entry in enumerate(self.leaderboard_data):
            y = start_y + (i * gap)
            if y > panel_top + panel_h - 40: break
            
            rank_txt = f"{i+1}."
            self.canvas.create_text(col1, y, text=rank_txt, fill="#ccc", font=("Ubuntu", 18, "bold"))
            self.canvas.create_text(col2, y, text=entry.get("name", "Unknown"), fill="white", font=("Ubuntu", 18))
            self.canvas.create_text(col3, y, text=entry.get("mode", "Easy"), fill="#aaa", font=("Ubuntu", 18))
            self.canvas.create_text(col4, y, text=str(entry["score"]), fill="#FFD700", font=("Ubuntu", 18, "bold"))

    def draw_difficulty_menu(self):
        self.clear_screen()
        self.canvas.create_text(60*self.scale, 60*self.scale, text="< BACK", fill="white", font=("Ubuntu", int(20*self.scale), "bold"), tags="back")
        self.canvas.tag_bind("back", "<Button-1>", lambda e: self.draw_main_menu())
        y0 = self.screen_height * 0.35
        for i, m in enumerate(["Easiest", "Medium", "Hardest"]):
            self.create_btn(self.screen_width//2, y0 + i*120*self.scale, m, lambda mode=m: self.open_popup(mode))

    def open_popup(self, mode):
        self.canvas.create_rectangle(0,0,self.screen_width,self.screen_height, fill="black", stipple="gray50", tags="pop")
        cx, cy = self.screen_width//2, self.screen_height//2
        if f"details_{mode}" in self.assets:
            self.canvas.create_image(cx, cy, image=self.assets[f"details_{mode}"], tags="pop")
        else:
            self.canvas.create_rectangle(cx-400, cy-300, cx+400, cy+300, fill="#222", outline="white", tags="pop")
        
        entry_bg_x, entry_bg_y = cx, cy + 200*self.scale
        entry_w, entry_h = 250, 45
        
        self.canvas.create_text(entry_bg_x, entry_bg_y - 35, text="ENTER YOUR NAME", fill="#FFD700", font=("Ubuntu", 12, "bold"), tags="pop")
        
        self.canvas.create_rectangle(
            entry_bg_x - entry_w/2 - 2, entry_bg_y - entry_h/2 - 2,
            entry_bg_x + entry_w/2 + 2, entry_bg_y + entry_h/2 + 2,
            fill="#FFD700", outline="", tags="pop"
        )
        
        self.entry_widget = Entry(self.root, font=("Ubuntu", 14), justify='center', bg="#222", fg="white", relief="flat", insertbackground="white")
        self.entry_widget.place(x=entry_bg_x - entry_w/2, y=entry_bg_y - entry_h/2, width=entry_w, height=entry_h)
        
        def validate_start():
            name = self.entry_widget.get().strip()
            if name:
                self.player_name = name
                self.start_game(mode)
            else:
                self.canvas.create_rectangle(
                    entry_bg_x - entry_w/2 - 4, entry_bg_y - entry_h/2 - 4,
                    entry_bg_x + entry_w/2 + 4, entry_bg_y + entry_h/2 + 4,
                    outline="#FF0000", width=3, tags="pop_err"
                )
                self.root.after(500, lambda: self.canvas.delete("pop_err"))

        play_btn_y = entry_bg_y + 80 * self.scale
        
        self.create_btn(cx+self.popup_w//2-60*self.scale, cy-self.popup_h//2+60*self.scale, "close", lambda: self.close_popup_logic(), tag="pop")
        self.create_btn(cx, play_btn_y, "play_next", validate_start, tag="pop")

    def close_popup_logic(self):
        self.canvas.delete("pop")
        self.canvas.delete("pop_err")
        if self.entry_widget:
            self.entry_widget.destroy()
            self.entry_widget = None

    def start_game(self, mode):
        self.close_popup_logic()
        self.game_mode = mode 
        word_tuple = self.get_word_by_difficulty(mode)
        self.current_word = word_tuple[0]
        self.current_meaning = word_tuple[1]
        self.current_hint = word_tuple[2]
        self.wrong_guesses = 0
        self.guessed_letters = []
        self.disabled_keys = [] 
        self.freeze_active = False
        self.duality_active = False
        self.roulette_step = "idle"
        self.time_left = 30 if mode == "Hardest" else 0
        
        self.game_screen = GameScreen(self)
        self.game_screen.draw()
        if mode == "Hardest": self.start_timer()

    def handle_guess(self, char):
        if self.roulette_step == "intro": return
        if char in self.guessed_letters or char in self.disabled_keys: return
        self.guessed_letters.append(char)
        is_correct = (char in self.current_word)
        
        # --- FIXED: Use light update instead of full redraw ---
        self.game_screen.update_key_visual(char)
        self.root.update_idletasks() 

        if self.roulette_step == "waiting_for_guess":
            self.resolve_roulette_guess(is_correct)
            self.roulette_step = "idle"
            self.game_screen.update_help_text("", "#333") 

        if not is_correct:
            if self.duality_active:
                self.duality_active = False 
                # Instead of full draw, just update status text
                self.game_screen.update_help_text("Shield Used! Wrong guess ignored.", "#e67e22")
            else:
                self.wrong_guesses += 1
                # --- FIXED: Only update hangman and hearts ---
                self.game_screen.update_hangman_ui()
        else:
            # --- FIX: Added missing arguments for width calculation ---
            w = self.screen_width
            split_x = int(w * 0.38)
            btn_strip_x = int(w * 0.85)
            container_w = btn_strip_x - split_x
            self.game_screen.draw_responsive_word(self.game_screen.paper_cx, int(self.screen_height * 0.18), container_w)

        self.check_game_over()

    def check_game_over(self):
        if all(c in self.guessed_letters for c in self.current_word):
            self.game_win()
        elif self.wrong_guesses >= 6:
            self.game_loss("Ran out of lives!")

    def game_win(self):
        self.cancel_timer()
        self.score += 100
        self.streak += 1
        self.streak_counter += 1
        msg = "YOU WON!"
        if self.streak_counter >= 5:
            self.streak_counter = 0
            for k in self.powerups: self.powerups[k] += 1
        self.show_end_popup(msg, True)

    def game_loss(self, reason):
        self.cancel_timer()
        self.save_leaderboard() 
        self.streak = 0
        self.streak_counter = 0
        self.score = 0 
        self.show_end_popup(reason, False)

    def show_end_popup(self, title, won):
        self.canvas.create_rectangle(0,0,self.screen_width,self.screen_height, fill="black", stipple="gray75", tags="end_pop")
        cx, cy = self.screen_width//2, self.screen_height//2
        w, h = self.popup_w, self.popup_h * 0.8
        
        self.canvas.create_rectangle(cx-w/2, cy-h/2, cx+w/2, cy+h/2, fill="#F7F1E3", outline="#2c3e50", width=5, tags="end_pop")
        color = "#27ae60" if won else "#c0392b"
        self.canvas.create_text(cx, cy - h/2 + 60*self.scale, text=title, fill=color, font=("Ubuntu", int(40*self.scale), "bold"), tags="end_pop")
        self.canvas.create_text(cx, cy - 20*self.scale, text=f"WORD: {self.current_word}", fill="black", font=("Ubuntu", int(30*self.scale), "bold"), tags="end_pop")
        self.canvas.create_text(cx, cy + 30*self.scale, text=f"Meaning: {self.current_meaning}", fill="#555", font=("Ubuntu", int(16*self.scale), "italic"), width=w*0.8, justify="center", tags="end_pop")
        
        if won:
            self.create_btn(cx - 120*self.scale, cy + h/2 - 80*self.scale, "play_next", lambda: [self.canvas.delete("end_pop"), self.start_game(self.game_mode)], tag="end_pop")
            self.create_btn(cx + 120*self.scale, cy + h/2 - 80*self.scale, "close", lambda: [self.save_leaderboard(), self.draw_main_menu()], tag="end_pop")
        else:
            btn_name = "try_again" if "try_again_norm" in self.assets else "play_next"
            self.create_btn(cx - 120*self.scale, cy + h/2 - 80*self.scale, btn_name, lambda: [self.canvas.delete("end_pop"), self.start_game(self.game_mode)], tag="end_pop")
            
            quit_name = "quit" if "quit_norm" in self.assets else "close"
            self.create_btn(cx + 120*self.scale, cy + h/2 - 80*self.scale, quit_name, lambda: self.draw_main_menu(), tag="end_pop")

    def use_powerup(self, name):
        if self.powerups.get(name, 0) <= 0: return
        if self.roulette_step != "idle": return

        if name == "roulette":
            self.powerups[name] -= 1
            self.roulette_step = "intro"
            self.game_screen.draw_powerups_vertical(self.screen_width * 0.85 + (self.screen_width * 0.15) // 2, int(self.screen_height * 0.35))
            self.game_screen.show_roulette_intro()
            self.root.after(2000, self.activate_roulette_selection)
            return

        used = False
        if name == "freeze":
            if self.game_mode == "Hardest" and not self.freeze_active:
                self.freeze_active = True
                self.root.after(5000, self.unfreeze)
                used = True
        elif name == "duality":
            if not self.duality_active:
                self.duality_active = True
                used = True
        elif name == "reveal":
            unguessed_correct = [c for c in self.current_word if c not in self.guessed_letters]
            if unguessed_correct:
                char = random.choice(unguessed_correct)
                self.guessed_letters.append(char)
                used = True
                self.check_game_over()
        elif name == "filter":
            all_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            candidates = [c for c in all_letters if c not in self.current_word and c not in self.guessed_letters and c not in self.disabled_keys]
            if candidates:
                to_disable = random.sample(candidates, k=min(3, len(candidates)))
                self.disabled_keys.extend(to_disable)
                used = True

        if used:
            self.powerups[name] -= 1
            self.game_screen.draw() 

    def activate_roulette_selection(self):
        self.game_screen.hide_overlays() 
        self.roulette_step = "waiting_for_guess"
        self.game_screen.draw()

    def resolve_roulette_guess(self, won):
        if won:
            for k in self.powerups: self.powerups[k] += 1
            self.game_screen.show_roulette_result(True)
        else:
            for k in self.powerups: self.powerups[k] = max(0, self.powerups[k] - 1)
            self.game_screen.show_roulette_result(False)
        self.root.after(1000, lambda: [self.game_screen.hide_overlays(), self.game_screen.draw()])

    def unfreeze(self): self.freeze_active = False

    def start_timer(self):
        self.cancel_timer()
        self.update_timer()

    def update_timer(self):
        if self.game_mode == "Hardest":
            if not self.freeze_active:
                self.time_left -= 1
                if self.time_left <= 0:
                    self.game_loss("Time's Up!")
                    return
            if self.current_word: self.game_screen.draw() 
            self.timer_id = self.root.after(1000, self.update_timer)

    def cancel_timer(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

if __name__ == "__main__":
    root = tk.Tk()
    HangmanUI(root)
    root.mainloop()
