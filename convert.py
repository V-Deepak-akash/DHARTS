import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import base64
from pathlib import Path

def image_to_base64_gui():
    filepath = filedialog.askopenfilename(title="Select Image",
                                          filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
    if filepath:
        try:
            with open(filepath, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
                text_area.delete("1.0", tk.END)
                text_area.insert(tk.END, encoded)
                messagebox.showinfo("Success", "Image converted to Base64.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not encode image.\n{e}")

def base64_to_image_gui():
    base64_data = text_area.get("1.0", tk.END).strip()
    if not base64_data:
        messagebox.showwarning("Warning", "Base64 data is empty.")
        return

    filepath = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")])
    if filepath:
        try:
            with open(filepath, "wb") as image_file:
                image_file.write(base64.b64decode(base64_data))
            messagebox.showinfo("Success", f"Image saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not decode Base64.\n{e}")

def load_base64_from_file():
    filepath = filedialog.askopenfilename(title="Select Base64 Text File",
                                          filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if filepath:
        try:
            with open(filepath, "r") as file:
                content = file.read()
                text_area.delete("1.0", tk.END)
                text_area.insert(tk.END, content)
                messagebox.showinfo("Loaded", "Base64 content loaded into the text box.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file.\n{e}")

def save_base64_to_file():
    content = text_area.get("1.0", tk.END).strip()
    if not content:
        messagebox.showwarning("Warning", "Base64 data is empty.")
        return
    filepath = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if filepath:
        try:
            with open(filepath, "w") as file:
                file.write(content)
            messagebox.showinfo("Success", f"Base64 saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file.\n{e}")

# GUI Setup
window = tk.Tk()
window.title("Image <--> Base64 Converter")
window.geometry("700x600")

frame = tk.Frame(window)
frame.pack(pady=10)

btn_img_to_b64 = tk.Button(frame, text="📤 Image → Base64", command=image_to_base64_gui)
btn_img_to_b64.grid(row=0, column=0, padx=5)

btn_b64_to_img = tk.Button(frame, text="📥 Base64 → Image", command=base64_to_image_gui)
btn_b64_to_img.grid(row=0, column=1, padx=5)

btn_load_file = tk.Button(frame, text="📂 Load Base64 File", command=load_base64_from_file)
btn_load_file.grid(row=0, column=2, padx=5)

btn_save_b64 = tk.Button(frame, text="💾 Save Base64", command=save_base64_to_file)
btn_save_b64.grid(row=0, column=3, padx=5)

text_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, width=80, height=25)
text_area.pack(padx=10, pady=10)

window.mainloop()
