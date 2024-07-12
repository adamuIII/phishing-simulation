import flet as ft
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import smtplib
import os
from dotenv import load_dotenv, set_key
import qrcode
from io import BytesIO
from openai import OpenAI
import re
from twilio.rest import Client
import sqlite3


# DB
def init_db():
    conn = sqlite3.connect('phishing_simulation.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS emails
              (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL)
              ''')
    c.execute('''
              CREATE TABLE IF NOT EXISTS winners
              (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL)
              ''')
    conn.commit()
    conn.close()

init_db()


load_dotenv()

def contains_dangerous_characters(input_text):
    dangerous_characters_pattern = re.compile(r'[<>]')
    return dangerous_characters_pattern.search(input_text) is not None


def create_text_field(label):
    return ft.TextField(
        label=label,
        multiline=True,
        width=300,
        height=50,
        color='',
        fill_color='',
        border=1,
        border_radius=10,
        border_color='#2c3e50',
        border_width=3
        )


# Emails validation
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# Basic app settings
def main(page: ft.Page):
    page.title = "Phishing Simulation APP"
    page.bgcolor = '#333333'  
    page.window_width = 900       
    page.window_height = 700       
    page.window_resizable = False  


    # Switching views
    # Save e-mails
    def show_save_emails(e):
        print("show_save_emails called")
        main_container.controls.clear()
        
        email_input = ft.TextField(label="e-mail addresses", multiline=True, width=400, height=100, color='', fill_color='', border=1, border_radius=10, border_color='#2c3e50', border_width=5)
        status_text = ft.Text(value="", color="red")
        db_emails = ft.TextField(label="Database Content", multiline=True, width=400, height=200, color='', fill_color='', border=1, border_radius=10, border_color='#2c3e50', border_width=5, read_only=True)
        
        def save_email(event):
            try:
                emails = email_input.value.splitlines()
                valid_emails = [email for email in emails if is_valid_email(email)]

                conn = sqlite3.connect('phishing_simulation.db')
                c = conn.cursor()
                for email in valid_emails:
                    c.execute('INSERT INTO emails (email) VALUES (?)', (email,))
                conn.commit()
                conn.close()
                
                email_input.value = ""
                status_text.value = "e-mails saved successfully."
            except Exception as ex:
                status_text.value = f"save emails error: {str(ex)}"
            finally:
                page.update()

        def clear_database(event):
            try:
                conn = sqlite3.connect('phishing_simulation.db')
                c = conn.cursor()
                c.execute('DELETE FROM emails')
                c.execute('DELETE FROM sqlite_sequence WHERE name="emails"')
                c.execute('DELETE FROM  winners')
                conn.commit()
                conn.close()
                status_text.value = "Database cleared successfully."
            except Exception as ex:
                status_text.value = f"clear database error: {str(ex)}"
            finally:
                page.update()

        def show_database(event):
            try:
                conn = sqlite3.connect('phishing_simulation.db')
                c = conn.cursor()
                c.execute('SELECT id, email FROM emails')
                rows = c.fetchall()
                conn.close()

                generated_text = "\n".join([f"{row[0]} {row[1]}" for row in rows])
                db_emails.value = generated_text
                db_emails.update()
            except Exception as ex:
                status_text.value = f"show database error: {str(ex)}"
            finally:
                page.update()

        save_button = ft.ElevatedButton(text="Save", on_click=save_email, opacity=100, width=150)
        clear_button = ft.ElevatedButton(text="Clear Database", on_click=clear_database, opacity=100, width=150)
        show_button = ft.ElevatedButton(text="Show Database", on_click=show_database, opacity=100, width=150)

        main_container.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[email_input, save_button, clear_button, show_button, db_emails, status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center
            )
        )
        page.update()
    
    # Send phishing messages
    def show_write_message(e):
        print("show_write_message called")
        main_container.controls.clear()
        
        email_content_input = ft.TextField(label="Type the message content", multiline=True, width=400, height=300, color='', fill_color='', border=1, border_radius=10, border_color='#2c3e50', border_width=5)
        status_text = ft.Text("")

        def send_emails(event):
            content_email = email_content_input.value
            try:
                conn = sqlite3.connect('phishing_simulation.db')
                c = conn.cursor()
                c.execute('SELECT id, email FROM emails')
                emails = c.fetchall()
                conn.close()

                for id_email, email in emails:
                    all_content = f"{content_email}\n\nClick on the link to learn more: http://127.0.0.1:5000/phish?id={id_email}"
                    msg = MIMEText(all_content)
                    msg['Subject'] = 'Important message!'
                    msg['From'] = os.getenv("EMAIL")
                    msg['To'] = email

                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(os.getenv("EMAIL"), os.getenv("EMAIL_KEY"))
                    server.sendmail(msg['From'], msg['To'], msg.as_string())
                    server.quit()
                    status_text.value = f"Message send to {email}"
            except Exception as ex:
                status_text.value = f"Send message error: {str(ex)}"
            page.update()
        
        send_button = ft.ElevatedButton(text="Phish", on_click=send_emails)
        main_container.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[email_content_input, send_button, status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center
            )
        )
        page.update()
    
    # Send phishing messages with QR code 
    def show_write_message_qr(e):
        print("show_write_message_qr called")
        main_container.controls.clear()
        
        email_content_input = ft.TextField(label="Type the message content", multiline=True, width=400, height=300, color='', fill_color='', border=1, border_radius=10, border_color='#2c3e50', border_width=5)
        status_text = ft.Text("")

        def send_emails(event):
            content_email = email_content_input.value
            try:
                conn = sqlite3.connect('phishing_simulation.db')
                c = conn.cursor()
                c.execute('SELECT id, email FROM emails')
                emails = c.fetchall()
                conn.close()

                for id_email, email in emails:
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(f"{content_email}\n\nClick on the link to learn more: http://127.0.0.1:5000/phish?id={id_email}")
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    # Convert image to binary data
                    img_buffer = BytesIO()
                    img.save(img_buffer, format="PNG")
                    img_data = img_buffer.getvalue()
                    
                    msg = MIMEMultipart()
                    msg['Subject'] = 'Important message!'
                    msg['From'] = os.getenv("EMAIL")
                    msg['To'] = email
                    
                    # Add email content
                    text = MIMEText(content_email)
                    msg.attach(text)
                    
                    # Attach QR code image
                    qr_img_mime = MIMEImage(img_data)
                    qr_img_mime.add_header('Content-Disposition', 'attachment', filename='qrcode.png')
                    msg.attach(qr_img_mime)

                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(os.getenv("EMAIL"), os.getenv("EMAIL_KEY"))
                    server.sendmail(msg['From'], msg['To'], msg.as_string())
                    server.quit()
                    status_text.value = f"Message send to {email}"
            except Exception as ex:
                status_text.value = f"Send message error: {str(ex)}"
            page.update()

        send_button = ft.ElevatedButton(text="Phish", on_click=send_emails)
        main_container.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[email_content_input, send_button, status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center
            )
        )
        page.update()
    
    # Generate phishing message with OpenAI
    def show_generate_text(e):
        print("show_generate_text called")

        def save_and_display_info(event):
            try:
                basic_info = basic_info_field.value
                socioemotional_info = socioemotional_info_field.value
                if contains_dangerous_characters(basic_info) or contains_dangerous_characters(socioemotional_info):
                    raise ValueError("Error: Dangerous characters.")
                client = OpenAI(api_key=os.getenv("GPT_API_KEY"))

                feeling = socioemotional_info_field.value
                personal_info = basic_info_field.value

                # GPT 3.5 Configuration for phishing with social engineering aspects
                chat_completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are an assistant who writes email messages. You need to evoke that kind of emotion in the message: {feeling}. In the email, try to persuade that person to click on the link below. Everything will be in the next messages so you don't have to add texts like: [LINK] etc. Try to use all the information about this person to persuade him/her to click on the link."},
                        {"role": "user", "content": f"Write an email to the person with such personal information: {personal_info}"}

                    ]
                )

                generated_text_field.value = f"{chat_completion.choices[0].message.content}"
                status_text.value = "Text generated successfully."
                generated_text_field.update()

            except Exception as ex:
                status_text.value = f"Error : {str(ex)}"
            finally:
                page.update()

        main_container.controls.clear()

        basic_info_field = ft.TextField(label="Informations about target", multiline=True, width=300, height=100,color='',fill_color='',border=1,border_radius=10,border_color='#2c3e50',border_width=5)
        socioemotional_info_field = ft.TextField(label="Social Engineering - pressure, anger etc", multiline=True, width=300, height=100,color='',fill_color='',border=1,border_radius=10,border_color='#2c3e50',border_width=5)

        save_button = ft.ElevatedButton(text="Send", on_click=save_and_display_info)

        generated_text_field = ft.TextField(label="Generated text", multiline=True, width=600, height=200,color='',fill_color='',border=1,border_radius=10,border_color='#2c3e50',border_width=5)

        status_text = ft.Text(value="", color="red")

        main_container.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[basic_info_field, socioemotional_info_field, save_button, generated_text_field,status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center
            )
        )
        
        page.update()

    # Smishing with Twilio API
    def smishing(e):
        print("smishing called")

        def is_valid_phone_number(phone_number):
            return phone_number.isdigit() and len(phone_number) == 9
        

        def save_and_display_info(event):
            try:
                if not is_valid_phone_number(phone_number_input.value):
                    raise ValueError("Phone number must contain 9 digits.")
                account_sid = os.getenv("ACCOUNT_SID")
                auth_token = os.getenv("AUTH_TOKEN")
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body=sms_body.value,
                    from_ = os.getenv("TWILIO_NUMBER"),
                    to = phone_number_input.value
              
                )
                print(message.sid)
                status_text.value = "Message was sent successfully."
            except Exception as ex:    
                status_text.value = f"Error message: {str(ex)}"
            finally:
                page.update()
            
        main_container.controls.clear()

        phone_number_input  = ft.TextField(label="+area_code_phone_number", multiline=True, width=300, height=100,color='',fill_color='',border=1,border_radius=10,border_color='#2c3e50',border_width=5)
        sms_body = ft.TextField(label="message", multiline=True, width=300, height=100,color='',fill_color='',border=1,border_radius=10,border_color='#2c3e50',border_width=5)

        status_text = ft.Text(value="", color="red")
        save_button = ft.ElevatedButton(text="Send SMS", on_click=save_and_display_info)
        main_container.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[phone_number_input, sms_body,save_button,status_text],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center
            )
        )
        page.update()
    # Setting API keys etc. in env. file
    def settings(e):
        print("settings called")
        def save_and_display_info(event):
            
            email = email_text_field.value
            email_key = email_key_text_field.value
            gpt_api_key = gpt_key_text_field.value
            account_sid = account_sid_text_field.value
            auth_token = auth_token_text_field.value
            twilio_number = twilio_number_text_field.value

            env_file_path = ".env"
            if not os.path.exists(env_file_path):
                with open(env_file_path, 'w') as f:
                    f.write('')  # Create an empty .env file if it doesn't exist

            # Save values to .env file
            set_key(env_file_path, "EMAIL", email)
            set_key(env_file_path, "EMAIL_KEY", email_key)
            set_key(env_file_path, "GPT_API_KEY", gpt_api_key)
            set_key(env_file_path, "ACCOUNT_SID", account_sid)
            set_key(env_file_path, "AUTH_TOKEN", auth_token)
            set_key(env_file_path, "TWILIO_NUMBER", twilio_number)

            
            print("Saved to .env file .env")

            main_container.controls.append(
                ft.Text("Saved to .env file!", color=ft.colors.GREEN)
            )
            page.update()



        main_container.controls.clear()
        email_text_field = create_text_field("email")
        email_key_text_field = create_text_field("email key")
        gpt_key_text_field = create_text_field("gpt api key")
        account_sid_text_field = create_text_field("account sid")
        auth_token_text_field = create_text_field("auth token")
        twilio_number_text_field = create_text_field("twilio number")

        save_button = ft.ElevatedButton(text="Save settings", on_click=save_and_display_info)
        main_container.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[email_text_field, email_key_text_field, gpt_key_text_field, account_sid_text_field ,auth_token_text_field, twilio_number_text_field , save_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                alignment=ft.alignment.center
            )
        )
        page.update()


    # Menu buttons
    menu = ft.Row(
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.SAVE, color=ft.colors.WHITE),
                        ft.Text("Save emails", color=ft.colors.WHITE, size=14)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                border=ft.border.all(1, color=ft.colors.GREY_800),
                bgcolor='#2C3E50',
                height=100,
                width=130,  # Increase width to accommodate longer text
                alignment=ft.alignment.center,
                padding=10,
                on_click=show_save_emails,
                ink=True,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.EMAIL, color=ft.colors.WHITE),
                        ft.Text("Phishing", color=ft.colors.WHITE, size=14)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                border=ft.border.all(1, color=ft.colors.GREY_800),
                bgcolor='#354b60', 
                height=100,
                width=130,  # Increase width to accommodate longer text
                alignment=ft.alignment.center,
                padding=10,
                on_click=show_write_message,
                ink=True,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.QR_CODE, color=ft.colors.WHITE),
                        ft.Text("Link QR", color=ft.colors.WHITE, size=17)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                border=ft.border.all(1, color=ft.colors.GREY_800),
                bgcolor='#248BD6',
                height=100,
                width=130,  # Increase width to accommodate longer text
                alignment=ft.alignment.center,
                padding=10,
                on_click=show_write_message_qr,
                ink=True,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.SMART_TOY_SHARP, color=ft.colors.WHITE),
                        ft.Text("Generate text", color=ft.colors.WHITE, size=14)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                border=ft.border.all(1, color=ft.colors.GREY_800),
                bgcolor='#83B8FF',
                height=100,
                width=130,  # Increase width to accommodate longer text
                alignment=ft.alignment.center,
                padding=10,
                on_click=show_generate_text,
                ink=True,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.SMS, color=ft.colors.WHITE),
                        ft.Text("Smishing", color=ft.colors.WHITE, size=14)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                border=ft.border.all(1, color=ft.colors.GREY_800),
                bgcolor='#b6d5ff',
                height=100,
                width=130,  # Increase width to accommodate longer text
                alignment=ft.alignment.center,
                padding=10,
                on_click=smishing,
                ink=True,
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.SETTINGS, color=ft.colors.WHITE),
                        ft.Text("Settings", color=ft.colors.WHITE, size=14)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                border=ft.border.all(1, color=ft.colors.GREY_800),
                bgcolor='#d0e4ff',
                height=100,
                width=130,  # Increase width to accommodate longer text
                alignment=ft.alignment.center,
                padding=10,
                on_click=settings,
                ink=True,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )

    menu_container = ft.Container(
        content=menu,
        bgcolor='#34495E',  # Set the menu background to dark gray
        padding=10,
    )

    main_container = ft.Column(
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    page.add(
        ft.Column(
            [
                menu_container,
                main_container,    
            ],
            expand=True,  
        ), 
    
    )

if __name__ == "__main__":
    ft.app(target=main)
