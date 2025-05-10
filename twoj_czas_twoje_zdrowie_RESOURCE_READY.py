import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import subprocess
import json
import pygame
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ZdrowieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Twój czas, Twoje zdrowie")
        self.root.geometry("180x310")
        self.add_dragging_functionality()
        self.root.resizable(False, False)
        self.bg_color = "#fef4d1"
        self.text_color = "#3a2f1d"
        self.lang_data = {}
        self.current_lang = "pl"
        self.sound_enabled = tk.BooleanVar(value=True)
        self.shutdown_thread = None
        self.shutdown_cancelled = False

        pygame.mixer.init()
        self.sounds = {
            "break": "dzwonek_przerwy.wav",
            "work": "powrot_do_pracy.wav"
        }

        self.timer_running = False
        self.pomodoro_mode = False

        self.load_language(self.current_lang)
        self.show_intro()

    def load_language(self, lang_code):
        try:
            with open(resource_path(f"lang_{lang_code}.json"), "r", encoding="utf-8") as f:
                self.lang_data = json.load(f)
            self.current_lang = lang_code
        except Exception as e:
            print(f"Błąd ładowania języka: {e}")

    def play_sound(self, name):
        if self.sound_enabled.get():
            try:
                pygame.mixer.Sound(resource_path(self.sounds[name])).play()
            except:
                pass

    def show_intro(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.bg_color)

        title = tk.Label(self.root, text=self.lang_data.get("title", ""), font=("Arial", 12, "bold"), bg=self.bg_color, fg=self.text_color)
        title.pack(pady=(20, 10))

        

        sound_frame = tk.Frame(self.root, bg=self.bg_color)
        sound_frame.pack(pady=(20, 5))
        tk.Checkbutton(sound_frame, text=self.lang_data.get("sound_label", ""), variable=self.sound_enabled,
                       bg=self.bg_color, font=("Arial", 11), fg=self.text_color).pack(anchor="w")

        lang_label = tk.Label(self.root, text=self.lang_data.get("language", ""), font=("Arial", 11), bg=self.bg_color, fg=self.text_color)
        lang_label.pack(pady=(13, 0))

        lang_dropdown = ttk.Combobox(self.root, values=["pl", "en", "de", "fr"], state="readonly", width=4)
        lang_dropdown.set(self.current_lang)
        lang_dropdown.pack()
        lang_dropdown.bind("<<ComboboxSelected>>", lambda e: self.change_language(lang_dropdown.get()))

        tk.Button(self.root, text=self.lang_data.get("start_button", ""), command=self.start_main).pack(pady=30)
        author_label = tk.Label(self.root, text="© Piotr Przebiorowski", font=("Arial", 10), bg=self.bg_color, fg=self.text_color)
        author_label.pack(side=tk.BOTTOM, pady=5)


    def change_language(self, lang_code):
        self.load_language(lang_code)
        self.show_intro()

    def start_main(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.geometry("240x420")
        self.root.configure(bg=self.bg_color)

        tk.Label(self.root, text=self.lang_data.get("main_title", ""), font=("Arial", 16, "bold"), bg=self.bg_color, fg=self.text_color).pack(pady=10)
        tk.Label(self.root, text=self.lang_data.get("main_info", ""), font=("Arial", 11), bg=self.bg_color, fg=self.text_color).pack(pady=5)

        tk.Button(self.root, text=self.lang_data.get("mode_1", "Tryb testowy"), command=lambda: self.start_pomodoro_mode(60, 30)).pack(pady=5)
        tk.Button(self.root, text=self.lang_data.get("mode_2", "30 min"), command=lambda: self.start_pomodoro_mode(1800, 120)).pack(pady=5)
        tk.Button(self.root, text=self.lang_data.get("mode_3", "45 min"), command=lambda: self.start_pomodoro_mode(2700, 300)).pack(pady=5)

        self.timer_label = tk.Label(self.root, text="–", font=("Arial", 20), bg=self.bg_color, fg=self.text_color)
        self.timer_label.pack(pady=10)

        tk.Label(self.root, text=self.lang_data.get("shutdown_label", "Czasowy wyłącznik komputera:"), font=("Arial", 11), bg=self.bg_color, fg=self.text_color).pack(pady=(10, 0))
        self.shutdown_entry = tk.Entry(self.root, width=6)
        self.shutdown_entry.pack()
        tk.Button(self.root, text=self.lang_data.get("set_shutdown", "Ustaw czas"), command=self.set_shutdown_timer).pack(pady=(5, 5))

        self.shutdown_info_label = tk.Label(self.root, text="", font=("Arial", 10), bg=self.bg_color, fg="darkred")
        self.shutdown_info_label.pack()

        tk.Button(self.root, text="Reset", command=self.reset_app).pack(pady=(10, 2))

        author_label = tk.Label(self.root, text="© Piotr Przebiorowski", font=("Arial", 10), bg=self.bg_color, fg=self.text_color)
        author_label.pack(side=tk.BOTTOM, pady=5)

    def start_pomodoro_mode(self, work_sec, break_sec):
        self.timer_running = False
        time.sleep(1)
        self.pomodoro_work = work_sec
        self.pomodoro_break = break_sec
        self.current_phase = "work"
        self.run_pomodoro()

    def run_pomodoro(self):
        if self.current_phase == "work":
            self.timer_seconds = self.pomodoro_work
            self.timer_label.config(text=self.lang_data.get("work_mode", "⏳ Praca..."))
            self.timer_running = True
            threading.Thread(target=self.pomodoro_countdown).start()
        else:
            self.timer_running = False
            self.show_break_window()

    def pomodoro_countdown(self):
        while self.timer_seconds > 0 and self.timer_running:
            mins, secs = divmod(self.timer_seconds, 60)
            time_str = f"{mins:02}:{secs:02}"
            self.timer_label.config(text=time_str)
            time.sleep(1)
            self.timer_seconds -= 1

        if self.timer_running:
            if self.current_phase == "work":
                self.current_phase = "break"
                self.play_sound("break")
                self.run_pomodoro()
            else:
                self.current_phase = "work"
                self.play_sound("work")
                self.run_pomodoro()

    def show_break_window(self):
        self.break_window = tk.Toplevel(self.root)
        self.break_window.title(self.lang_data.get("break_title", self.lang_data.get("break_title", "Przerwa")))
        self.break_window.geometry("460x380")
        self.break_window.attributes("-topmost", True)
        self.break_window.overrideredirect(True)
        self.break_window.configure(bg="#7fff7f")

        tk.Label(self.break_window, text=self.lang_data.get("break_message", self.lang_data.get("break_message", "Mrugaj oczami, rozciągnij się...")),
                 wraplength=350, justify="center", font=("Arial", 16, "bold"), bg=self.bg_color, fg=self.text_color).pack(pady=10)

        self.break_time_left = self.pomodoro_break
        self.break_label = tk.Label(self.break_window, text="", font=("Arial", 16), bg=self.bg_color, fg=self.text_color)
        self.break_label.pack(pady=5)
        self.update_break_timer()
        self.animate_break_window()

        def enable_skip():
            self.skip_btn_in_break = tk.Button(self.break_window, text=self.lang_data.get("skip_btn", self.lang_data.get("skip_btn", "Pomiń przerwę / czuję się dobrze")),
                                               command=lambda: [self.break_window.destroy(), self.skip_break()])
            self.skip_btn_in_break.pack(pady=10)

        self.break_window.after(15000, enable_skip)
        self.break_window.after(self.pomodoro_break * 1000, lambda: [self.break_window.destroy(), self.resume_after_break()])

    def update_break_timer(self):
        if self.break_time_left > 0 and self.break_window:
            mins, secs = divmod(self.break_time_left, 60)
            self.break_label.config(text=f"{self.lang_data.get('remaining_break', 'Pozostały czas przerwy')}: {mins:02}:{secs:02}")
            self.break_time_left -= 1
            self.break_window.after(1000, self.update_break_timer)

    def resume_after_break(self):
        self.current_phase = "work"
        self.run_pomodoro()

    def skip_break(self):
        self.timer_running = False
        self.current_phase = "work"
        self.run_pomodoro()

    def set_shutdown_timer(self):
        alarm_input = self.shutdown_entry.get()
        try:
            h, m = map(int, alarm_input.split(":"))
            now = time.localtime()
            now_sec = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec
            target_sec = h * 3600 + m * 60
            delta = target_sec - now_sec
            if delta < 0:
                delta += 86400  # następny dzień
            self.shutdown_cancelled = False
            self.shutdown_thread = threading.Thread(target=lambda: self.shutdown_after(delta))
            self.shutdown_thread.start()
            hours = delta // 3600
            minutes = (delta % 3600) // 60
            shutdown_time = time.localtime(time.time() + delta)
            shutdown_str = time.strftime("%H:%M", shutdown_time)
            self.shutdown_info_label.config(text=f"{self.lang_data.get('shutdown_time_info', '🔔 Komputer zostanie wyłączony o')} {shutdown_str}")
            messagebox.showinfo(self.lang_data.get("set_title", "Ustawiono"), f"{self.lang_data.get('shutdown_set', 'Komputer wyłączy się za')} {hours}h {minutes}min")
        except:
            messagebox.showerror(self.lang_data.get("error_title", "Błąd"), self.lang_data.get("error_format", "Wpisz godzinę w formacie HH:MM"))

    def shutdown_after(self, seconds):
        time.sleep(seconds)
        if self.shutdown_cancelled:
            return
        if os.name == "nt":
            os.system("shutdown /s /t 1")
        else:
            os.system("shutdown now")

    def reset_app(self):
        self.timer_running = False
        self.shutdown_info_label.config(text="")
        self.shutdown_entry.delete(0, tk.END)
        self.timer_label.config(text="–")
        self.shutdown_cancelled = True
        try:
            if os.name == "nt":
                os.system("shutdown /a")
            else:
                subprocess.call(["shutdown", "-c"])
        except:
            pass
        messagebox.showinfo(self.lang_data.get("reset_title", "Reset"), self.lang_data.get("reset_message", "Wszystkie funkcje zostały zresetowane."))



    def animate_break_window(self):
        def move():
            try:
                w = 460
                h = 380
                screen_width = self.break_window.winfo_screenwidth()
                screen_height = self.break_window.winfo_screenheight()

                x = 0
                y = 0
                dx = 1
                dy = 1

                while True:
                    if not self.break_window.winfo_exists():
                        break

                    x += dx
                    y += dy

                    if x + w >= screen_width or x <= 0:
                        dx *= -1
                    if y + h >= screen_height or y <= 0:
                        dy *= -1

                    self.break_window.geometry(f"{w}x{h}+{x}+{y}")
                    time.sleep(0.03)
            except:
                pass

        threading.Thread(target=move, daemon=True).start()



    def add_dragging_functionality(self):
        def start_move(event):
            self.x = event.x
            self.y = event.y

        def stop_move(event):
            self.x = None
            self.y = None

        def do_move(event):
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        self.root.bind("<ButtonPress-1>", start_move)
        self.root.bind("<ButtonRelease-1>", stop_move)
        self.root.bind("<B1-Motion>", do_move)


if __name__ == "__main__":
    root = tk.Tk()
    app = ZdrowieApp(root)
    root.mainloop()
