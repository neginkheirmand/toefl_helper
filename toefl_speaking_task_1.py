import os
import tkinter as tk
from tkinter import messagebox, scrolledtext
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import time

class QuestionApp:
    def __init__(self, master, questions):
        self.master = master
        self.questions = questions
        self.current_question = 0
        self.read_time = 20  # Time to read the question
        self.answer_time = 5  # Time to answer the question
        self.timer_running = False
        
        # Create the answers folder if it does not exist
        if not os.path.exists('answers'):
            os.makedirs('answers')
        
        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, font=("Arial", 14), height=10, width=50)
        self.text_area.pack(pady=20)
        self.text_area.config(state=tk.DISABLED)  # Initially disable editing
        
        self.timer_label = tk.Label(master, text="", font=("Arial", 14))
        self.timer_label.pack(pady=10)
        
        self.start_button = tk.Button(master, text="Start", command=self.start)
        self.start_button.pack(pady=20)
        
        self.skip_button = tk.Button(master, text="Skip", command=self.skip_question)
        self.skip_button.pack(pady=20)
        self.skip_button.pack_forget()  # Hide initially

    def start(self):
        self.start_button.pack_forget()
        self.skip_button.pack()  # Show skip button
        self.ask_question()
        
    def ask_question(self):
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            self.text_area.config(state=tk.NORMAL)  # Enable editing to update text
            self.text_area.delete(1.0, tk.END)  # Clear previous text
            self.text_area.insert(tk.END, question)
            self.text_area.config(state=tk.DISABLED)  # Disable editing again
            
            self.update_timer(self.read_time, self.record_answer)
        else:
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "All questions completed!")
            self.text_area.config(state=tk.DISABLED)
            self.timer_label.config(text="")
            self.skip_button.pack_forget()  # Hide skip button

    def update_timer(self, remaining_time, callback):
        self.timer_running = True
        if remaining_time > 0:
            self.timer_label.config(text=f"Time left: {remaining_time} seconds")
            remaining_time -= 1
            self.timer_id = self.master.after(1000, self.update_timer, remaining_time, callback)
        else:
            self.timer_running = False
            callback()
            
    def record_answer(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Recording...")
        self.text_area.config(state=tk.DISABLED)
        
        self.update_timer(self.answer_time, self.save_recording)
        
        fs = 44100  # Sample rate
        seconds = self.answer_time  # Duration of recording
        
        # Record audio
        self.myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        
    def save_recording(self):
        sd.wait()  # Wait until recording is finished
        
        # Save as WAV file in the answers folder
        answer_path = f"answers/answer_{self.current_question + 1}.wav"
        write(answer_path, 44100, self.myrecording)
        
        self.current_question += 1
        self.ask_question()

    def skip_question(self):
        if self.timer_running:
            self.master.after_cancel(self.timer_id)  # Cancel the running timer
            self.timer_running = False
        self.current_question += 1
        self.ask_question()

def load_questions(filename):
    with open(filename, 'r') as file:
        questions = file.readlines()
    questions = [q.strip() for q in questions]
    return questions

if __name__ == "__main__":
    questions = load_questions('questions.txt')
    
    root = tk.Tk()
    root.title("Question and Answer App")
    app = QuestionApp(root, questions)
    root.mainloop()
