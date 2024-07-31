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
        self.answered_questions = self.load_answered_questions()
        self.current_question = 0
        self.read_time = 20  # Time to read the question
        self.answer_time = 45  # Time to answer the question
        self.timer_running = False

        # Create the answers folder if it does not exist
        if not os.path.exists('answers'):
            os.makedirs('answers')
        
        # Initial screen
        self.intro_frame = tk.Frame(master)
        self.intro_frame.pack(pady=20)
        self.answer_new_button = tk.Button(self.intro_frame, text="Answer New Questions", command=self.answer_new_questions)
        self.answer_new_button.pack(pady=10)
        self.review_answers_button = tk.Button(self.intro_frame, text="Review Answered Questions", command=self.review_answered_questions)
        self.review_answers_button.pack(pady=10)
        
        # Question and answer screen
        self.qa_frame = tk.Frame(master)
        self.text_area = scrolledtext.ScrolledText(self.qa_frame, wrap=tk.WORD, font=("Arial", 14), height=10, width=50)
        self.text_area.pack(pady=20)
        self.text_area.config(state=tk.DISABLED)  # Initially disable editing
        
        self.timer_label = tk.Label(self.qa_frame, text="", font=("Arial", 14))
        self.timer_label.pack(pady=10)
        
        self.skip_button = tk.Button(self.qa_frame, text="Skip", command=self.skip_question)
        self.skip_button.pack(pady=10)
        
        self.back_button_qa = tk.Button(self.qa_frame, text="Back to Main Menu", command=self.back_to_main_menu)
        self.back_button_qa.pack(pady=10)
        self.skip_button.pack()  # Show initially
        
        # Review answers screen
        self.review_frame = tk.Frame(master)
        self.review_text_area = scrolledtext.ScrolledText(self.review_frame, wrap=tk.WORD, font=("Arial", 14), height=10, width=50)
        self.review_text_area.pack(pady=20)
        self.review_text_area.config(state=tk.DISABLED)
        
        self.back_button_review = tk.Button(self.review_frame, text="Back to Main Menu", command=self.back_to_main_menu)
        self.back_button_review.pack(pady=10)
        
    def load_answered_questions(self):
        if os.path.exists('answered_questions.txt'):
            with open('answered_questions.txt', 'r') as file:
                answered = file.read().splitlines()
            return list(map(int, answered))
        return []
    
    def save_answered_question(self, question_index):
        self.answered_questions.append(question_index)
        with open('answered_questions.txt', 'a') as file:
            file.write(f"{question_index}\n")

    def answer_new_questions(self):
        self.intro_frame.pack_forget()
        self.qa_frame.pack(pady=20)
        self.ask_question()
        
    def review_answered_questions(self):
        self.intro_frame.pack_forget()
        self.review_frame.pack(pady=20)
        
        self.review_text_area.config(state=tk.NORMAL)
        self.review_text_area.delete(1.0, tk.END)
        for index in self.answered_questions:
            self.review_text_area.insert(tk.END, f"Question {index + 1}: {self.questions[index]}\n")
        self.review_text_area.config(state=tk.DISABLED)

    def back_to_main_menu(self):
        self.qa_frame.pack_forget()
        self.review_frame.pack_forget()
        self.intro_frame.pack(pady=20)

    def ask_question(self):
        unanswered_questions = [i for i in range(len(self.questions)) if i not in self.answered_questions]
        if self.current_question < len(unanswered_questions):
            question_index = unanswered_questions[self.current_question]
            question = self.questions[question_index]
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
        question_index = [i for i in range(len(self.questions)) if i not in self.answered_questions][self.current_question]
        answer_path = f"answers/answer_{question_index + 1}.wav"
        write(answer_path, 44100, self.myrecording)
        
        self.save_answered_question(question_index)
        
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
