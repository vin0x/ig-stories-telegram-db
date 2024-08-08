import telebot
import instaloader
import os
import glob
import sqlite3
import csv
import tempfile
from datetime import datetime
from database import init_db, save_story

api_key = "YOUR-API-KEY"
bot = telebot.TeleBot(api_key)
ig = instaloader.Instaloader()

ig.load_session_from_file('INSTAGRAMUSER', filename='session-INSTAGRAMUSER')


# Functions to query from SQLLite table
def get_stories_by_telegram_user(telegram_user_id):
    conn = sqlite3.connect('stories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories WHERE telegram_user_id = ?', (telegram_user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stories_by_instagram_user(instagram_user):
    conn = sqlite3.connect('stories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories WHERE instagram_user = ?', (instagram_user,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_stories():
    conn = sqlite3.connect('stories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories')
    rows = cursor.fetchall()
    conn.close()
    return rows

def view_table():
    conn = sqlite3.connect('stories.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories')
    rows = cursor.fetchall()
    conn.close()
    return rows

@bot.message_handler(commands=["downloadstories"])
def donwloadstories(message):
    sent = bot.send_message(message.chat.id, "Type the Instagram user without @")
    bot.register_next_step_handler(sent, uservar)

def uservar(message):
    user = message.text
    try:
        profile = ig.check_profile_id(user)
        bot.reply_to(message, "Downloading the stories from user: @" + user)
        ig.download_stories(userids=[profile.userid], filename_target=user + str(message.from_user.id))
        bot.reply_to(message, "_[CHECKING PROFILE...]_", parse_mode='Markdown')
        collection = user + str(message.from_user.id) + '/'
        
        if not os.path.exists(collection):
            bot.send_message(message.chat.id, "No stories found ❌")
            return
        
        # Remove unnecessary .json.xz files
        for item in glob.glob(os.path.join(collection, "*.json.xz")):
            os.remove(item)
        
        # Process and send media files
        for filename in os.listdir(collection):
            file_path = os.path.join(collection, filename)
            if os.path.isfile(file_path):
                # Extract time_posted from the file name (format: 'YYYY-MM-DD_HH-MM-SS_UTC.<extension>')
                name = os.path.splitext(filename)
                parts = name.split('_')
                if len(parts) >= 3:
                    timestamp_str = f"{parts[0]} {parts[1]}"
                    try:
                        # Parse the timestamp string into a datetime object
                        time_posted = datetime.strptime(timestamp_str, '%Y-%m-%d %H-%M-%S').strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        time_posted = 'Unknown Time'

                
                # Placeholder for country extraction (implement actual logic if needed)
                country = 'Unknown'
                
                if filename.endswith('.jpg'):
                    bot.send_photo(chat_id=message.chat.id, photo=open(file_path, 'rb'))
                elif filename.endswith('.mp4'):
                    bot.send_video(chat_id=message.chat.id, video=open(file_path, 'rb'))
                
                save_story(message.from_user.id, user, file_path, time_posted, country)  # Save the story with additional info
                
        bot.send_animation(message.chat.id, animation='https://media.tenor.com/F3la7LnCiGAAAAAC/mighty-lancer-games-wink.gif')

        bot.send_message(message.chat.id, "How about trying a new profile? type anything to bring the command again")
        
        
    except instaloader.exceptions.ProfileNotExistsException:
        bot.send_message(message.chat.id, 'Profile does not exist ❌')
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        bot.send_message(message.chat.id, 'Private profile 🔓 or without any available story\nTry another profile')


@bot.message_handler(commands=["getmystories"])
def get_my_stories(message):
    stories = get_stories_by_telegram_user(message.from_user.id)
    if stories:
        bot.send_message(message.chat.id, "Here are your downloaded stories:")
        for story in stories:
            if story[0].endswith('.jpg'):
                bot.send_photo(chat_id=message.chat.id, photo=open(story[0], 'rb'))
            else:
                bot.send_video(chat_id=message.chat.id, video=open(story[0], 'rb'))
    else:
        bot.send_message(message.chat.id, "You have no downloaded stories.")

@bot.message_handler(commands=["getstories"])
def get_stories(message):
    sent = bot.send_message(message.chat.id, "Type the Instagram user to get stories")
    bot.register_next_step_handler(sent, fetch_stories)

def fetch_stories(message):
    user = message.text
    stories = get_stories_by_instagram_user(user)
    if stories:
        bot.send_message(message.chat.id, "Here are the stories for user @" + user + ":")
        for story in stories:
            if story[0].endswith('.jpg'):
                bot.send_photo(chat_id=message.chat.id, photo=open(story[0], 'rb'))
            else:
                bot.send_video(chat_id=message.chat.id, video=open(story[0], 'rb'))
    else:
        bot.send_message(message.chat.id, "No stories found for user @" + user)

@bot.message_handler(commands=["viewtable"])
def handle_view_table(message):
    rows = view_table()
    if rows:
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w', newline='') as temp_file:
            writer = csv.writer(temp_file)
            
            # Write the header
            writer.writerow(['ID', 'Telegram User ID', 'Instagram User', 'File Path', 'Time Posted', 'Country'])
            
            # Write the rows
            for row in rows:
                writer.writerow(row)
            
            temp_file_path = temp_file.name
        
        # Send the CSV file 
        with open(temp_file_path, 'rb') as csv_file:
            bot.send_document(message.chat.id, csv_file, caption="Here is the stories table in .csv format.")
        
        # Remove the temporary file
        os.remove(temp_file_path)
    else:
        bot.send_message(message.chat.id, "The stories table is empty.")

def verificar(message):
    return True

@bot.message_handler(func=verificar)
def responder(message):
    texto = (
        "/downloadstories - To download all available stories, click on the function\n"
        "/getmystories - To get your downloaded stories\n"
        "/getstories - To get stories for a specific Instagram user\n"
        "/viewtable - To view the entire stories table\n"
        "*ONLY PUBLIC PROFILE, IT'S A BOT NOT A MAGE 🧙‍♂️!*\n\n_version: 1.3_"
    )
    bot.reply_to(message, "*Hey!* 🫶 \nSelect one function: \n\n" + texto, parse_mode='Markdown')

init_db()

bot.polling()
