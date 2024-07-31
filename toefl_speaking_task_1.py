import os
import tkinter as tk
from tkinter import messagebox, scrolledtext, Listbox, SINGLE
import sounddevice as sd
from scipy.io.wavfile import write, read
import numpy as np

class QuestionApp:
    def __init__(self, master, questions):
        self.master = master
        self.master.geometry("800x600")  # Set the initial window size
        self.questions = questions
        self.answered_questions = self.load_answered_questions()
        self.reviewed_questions = self.load_reviewed_questions()
        self.current_question = 0
        self.read_time = 2  # Time to read the question
        self.answer_time = 5  # Time to answer the question
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
        
        self.loader_canvas = tk.Canvas(self.qa_frame, width=50, height=50)
        self.loader_canvas.pack(pady=10)
        self.loader_arc = self.loader_canvas.create_arc(( 5, 5, 45, 45), start=0, extent=0, fill="blue")

        self.skip_button = tk.Button(self.qa_frame, text="Skip", command=self.skip_question)
        self.skip_button.pack(pady=10)
        
        self.back_button_qa = tk.Button(self.qa_frame, text="Back to Main Menu", command=self.back_to_main_menu)
        self.back_button_qa.pack(pady=10)
        self.skip_button.pack()  # Show initially
        
        # Review answers screen
        self.review_frame = tk.Frame(master)
        
        self.review_listbox = Listbox(self.review_frame, selectmode=SINGLE, font=("Arial", 14), width=50, height=10)
        self.review_listbox.pack(pady=20)
        self.review_listbox.bind("<<ListboxSelect>>", self.display_answer)
        
        self.review_text_area = scrolledtext.ScrolledText(self.review_frame, wrap=tk.WORD, font=("Arial", 14), height=5, width=50)
        self.review_text_area.pack(pady=10)
        self.review_text_area.config(state=tk.DISABLED)
        
        self.play_button = tk.Button(self.review_frame, text="Play Answer", command=self.play_answer)
        self.play_button.pack(pady=10)
        
        self.done_reviewing_button = tk.Button(self.review_frame, text="Done Reviewing", command=self.mark_as_reviewed)
        self.done_reviewing_button.pack(pady=10)
        
        self.back_button_review = tk.Button(self.review_frame, text="Back to Main Menu", command=self.back_to_main_menu)
        self.back_button_review.pack(pady=10)

    def load_answered_questions(self):
        if os.path.exists('answered_questions.txt'):
            with open('answered_questions.txt', 'r') as file:
                answered = file.read().splitlines()
            return list(map(int, answered))
        return []
    
    def load_reviewed_questions(self):
        if os.path.exists('reviewed_questions.txt'):
            with open('reviewed_questions.txt', 'r') as file:
                reviewed = file.read().splitlines()
            return list(map(int, reviewed))
        return []

    def save_answered_question(self, question_index):
        self.answered_questions.append(question_index)
        with open('answered_questions.txt', 'a') as file:
            file.write(f"{question_index}\n")

    def save_reviewed_question(self, question_index):
        if question_index not in self.reviewed_questions:
            self.reviewed_questions.append(question_index)
            with open('reviewed_questions.txt', 'a') as file:
                file.write(f"{question_index}\n")

    def answer_new_questions(self):
        self.intro_frame.pack_forget()
        self.qa_frame.pack(pady=20)
        self.ask_question()

    def review_answered_questions(self):
        self.intro_frame.pack_forget()
        self.review_frame.pack(pady=20)
        self.update_review_listbox()

    def back_to_main_menu(self):
        self.qa_frame.pack_forget()
        self.review_frame.pack_forget()
        self.intro_frame.pack(pady=20)

    def ask_question(self):
        unanswered_questions = [i for i in range(len(self.questions)) if i not in self.answered_questions]
        if unanswered_questions:
            if self.current_question >= len(unanswered_questions):
                self.current_question = 0  # Reset to the start if end of list
            question_index = unanswered_questions[self.current_question]
            question = self.questions[question_index]
            self.text_area.config(state=tk.NORMAL)  # Enable editing to update text
            self.text_area.delete(1.0, tk.END)  # Clear previous text
            self.text_area.insert(tk.END, question)
            self.text_area.config(state=tk.DISABLED)  # Disable editing again
            
            self.update_timer(self.read_time, self.record_answer, self.read_time)
        else:
            self.text_area.config(state=tk.NORMAL)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "All questions completed!")
            self.text_area.config(state=tk.DISABLED)
            self.timer_label.config(text="")
            self.skip_button.pack_forget()  # Hide skip button

    def update_timer(self, remaining_time, callback, total_time):
        self.timer_running = True
        if remaining_time > 0:
            self.timer_label.config(text=f"Time left: {remaining_time} seconds")
            extent = ((total_time - remaining_time) / total_time) * 360
            self.loader_canvas.itemconfig(self.loader_arc, extent=extent)
            remaining_time -= 1
            self.timer_id = self.master.after(1000, self.update_timer, remaining_time, callback, total_time)
        else:
            self.loader_canvas.itemconfig(self.loader_arc, extent=360)
            self.timer_running = False
            callback()
            
    def record_answer(self):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, "Recording...")
        self.text_area.config(state=tk.DISABLED)
        
        self.update_timer(self.answer_time, self.save_recording, self.answer_time)
        
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

    def display_answer(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            question_index = self.answered_questions[index]
            question = self.questions[question_index]
            
            self.review_text_area.config(state=tk.NORMAL)
            self.review_text_area.delete(1.0, tk.END)
            self.review_text_area.insert(tk.END, question)
            self.review_text_area.config(state=tk.DISABLED)
            
            # Store the selected question index for marking as reviewed
            self.current_reviewing_question = question_index

    def play_answer(self):
        selection = self.review_listbox.curselection()
        if selection:
            index = selection[0]
            question_index = self.answered_questions[index]
            answer_path = f"answers/answer_{question_index + 1}.wav"
            if os.path.exists(answer_path):
                fs, data = read(answer_path)
                sd.play(data, fs)
                sd.wait()  # Wait until the sound has finished playing
            else:
                messagebox.showerror("Error", "Audio file not found")

    def mark_as_reviewed(self):
        if hasattr(self, 'current_reviewing_question'):
            question_index = self.current_reviewing_question
            self.save_reviewed_question(question_index)
            self.update_review_listbox()
            self.review_text_area.config(state=tk.NORMAL)
            self.review_text_area.delete(1.0, tk.END)
            self.review_text_area.config(state=tk.DISABLED)

    def update_review_listbox(self):
        self.review_listbox.delete(0, tk.END)
        for index in self.answered_questions:
            review_status = " (already reviewed)" if index in self.reviewed_questions else ""
            self.review_listbox.insert(tk.END, f"Question {index + 1}{review_status}")

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
