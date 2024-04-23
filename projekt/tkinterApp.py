import tkinter as tk
import smtplib
from dotenv import load_dotenv
import os
from email.mime.text import MIMEText

def saveToFile():
    load_dotenv()
    emails = textBar.get("1.0", "end").split("\n")
    with open("emaile.txt", "w") as plik:
        for i, email in enumerate(emails, 1):
            if email.strip(): 
                plik.write(f"{i} {email.strip()}\n")
    textBar.delete("1.0", "end")
    status.config(text="Zapisano do pliku emaile.txt")

def sendEmails():
    contentEmail = textBar_email.get("1.0", "end")
    with open("emaile.txt", "r") as plik:
        for line in plik:
            idEmail, email = line.strip().split(" ")
            allContent = f"{contentEmail}\n\nKliknij w link aby dowiedzieć się więcej: http://127.0.0.1:5000/konkurs?id={idEmail}"
            print(allContent)
            msg = MIMEText(allContent)
            msg['Subject'] = 'Ważna wiadomość!'
            msg['From'] = os.getenv("EMAIL")
            msg['To'] = email

            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(os.getenv("EMAIL"), os.getenv("CODE"))
                server.sendmail(msg['From'], msg['To'], msg.as_string())
                server.quit()
                status.config(text=f"Wysłano wiadomość do {email}")
            except Exception as e:
                status.config(text=f"Błąd podczas wysyłania wiadomości do {email}: {str(e)}")


okno = tk.Tk()
okno.title("Aplikacja do zarządzania emailami")
okno.configure(bg="#F0F0F0")


topFrame = tk.Frame(okno, bg="#D3D3D3", padx=10, pady=10)
topFrame.pack(fill=tk.BOTH)

topBar = tk.Label(topFrame, text="Wklej tutaj emaile:", bg="#D3D3D3", fg="#000", font=("Helvetica", 12, "bold"))
topBar.pack()

textBar = tk.Text(topFrame, width=40, height=5, bg="#FFF", fg="#000", font=("Arial", 10))
textBar.pack()

saveButton = tk.Button(topFrame, text="Zapisz do pliku", command=saveToFile, bg="#008CBA", fg="#FFF", font=("Arial", 10, "bold"), padx=10, pady=5)
saveButton.pack(pady=5)

bottomFrame = tk.Frame(okno, bg="#D3D3D3", padx=10, pady=10)
bottomFrame.pack(fill=tk.BOTH)

bottomBar = tk.Label(bottomFrame, text="Wpisz treść wiadomości:", bg="#D3D3D3", fg="#000", font=("Helvetica", 12, "bold"))
bottomBar.pack()
textBar_email = tk.Text(bottomFrame, width=60, height=10, bg="#FFF", fg="#000", font=("Arial", 10))
textBar_email.pack()


sendButton = tk.Button(bottomFrame, text="Wyślij email", command=sendEmails, bg="#008CBA", fg="#FFF", font=("Arial", 10, "bold"), padx=10, pady=5)
sendButton.pack(pady=5)

status = tk.Label(okno, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#FFF", fg="#000", font=("Arial", 10))
status.pack(side=tk.BOTTOM, fill=tk.X)

okno.mainloop()
