import os
import playsound
import speech_recognition as sr
import time
import json
import re
import webbrowser
import requests
import datetime
from transformers import pipeline
from gtts import gTTS
from youtube_search import YoutubeSearch

# Dữ liệu từ khóa để phân loại ý định
intent_data = {
    "greeting": ["xin chào", "chào bạn", "hello", "hi"],
    "weather": ["thời tiết", "nhiệt độ", "trời hôm nay"],
    "search": ["tìm kiếm", "tra cứu", "tìm"],
    "music": ["nghe nhạc", "mở nhạc", "bật nhạc", "chơi nhạc", "phát nhạc"],
    "tell_me": ["kể chuyện", "đọc wikipedia", "nói về"],
    "open_application": ["mở ứng dụng", "chạy phần mềm"],
    "open_website": ["mở trang web", "truy cập", ".com", "www"],
    "time": ["mấy giờ", "bây giờ là mấy giờ", "hôm nay là ", "thời gian"],
    "goodbye": ["tạm biệt", "hẹn gặp lại", "bye","dừng", "thôi"]
}

# Mô hình NLP để phân loại ý định phức tạp hơn
nlp_pipeline = pipeline('zero-shot-classification', model='facebook/bart-large-mnli')

# Hàm phân loại ý định bằng từ khóa
def classify_intent_by_keywords(text):
    for intent, keywords in intent_data.items():
        for keyword in keywords:
            if keyword in text:
                return intent
    return "unknown"

# Hàm phân loại ý định tổng hợp (từ khóa + mô hình NLP)
def classify_intent(text):
    intent = classify_intent_by_keywords(text)
    if intent != "unknown":
        return intent
    candidate_labels = list(intent_data.keys())
    result = nlp_pipeline(text, candidate_labels)
    return result['labels'][0]

# Hàm đọc lời nói của bot
def speak(text):
    print("Bot: {}".format(text))
    tts = gTTS(text=text, lang='vi', slow=False)
    tts.save("sound.mp3")
    playsound.playsound("sound.mp3", False)
    os.remove("sound.mp3")

# Hàm nhận giọng nói từ người dùng
def get_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Me: ", end='')  # Yêu cầu người dùng nói
        audio = r.listen(source, phrase_time_limit=5)
        try:
            text = r.recognize_google(audio, language="vi-VN")
            print(text)
            return text
        except:
            print("...")  # Khi không nhận diện được giọng nói
            return 0

# Hàm lấy văn bản từ giọng nói của người dùng
def get_text():
    for i in range(3):
        text = get_voice()  # Gọi hàm get_voice để thu thập giọng nói
        if text:
            return text.lower()
        elif i < 2:
            speak("Bot không nghe rõ, bạn có thể nói lại không?")
    time.sleep(5)
    speak("Tạm biệt!")
    return 0

# Hàm xử lý các ý định của người dùng
def handle_intent(intent, name, text):
    if intent == 'greeting':
        speak(f"Chào {name}, tôi là trợ lý ảo của bạn. Bạn cần tôi giúp gì?")
    elif intent == 'open_website':
        open_website(text)
    elif intent == 'weather':
        weather()
    elif intent == 'search':
        google_search()
    elif intent == 'music':
        play_youtube()
    elif intent == 'tell_me':
        tell_me()
    elif intent == 'open_application':
        open_application(text)
    elif intent == 'time':
        get_time()
    elif intent == 'goodbye':
        speak("Hẹn gặp lại bạn! Chúc bạn một ngày tốt lành.")
        exit()

# Hàm lấy giờ
def get_time():
    now = datetime.datetime.now()
    speak(f"Bây giờ là {now.hour} giờ {now.minute} phút.")
    time.sleep(5)

# Hàm thời tiết
def weather():
    speak("Bạn muốn xem thời tiết ở đâu ạ!")
    time.sleep(3)
    city = get_text()
    if not city:
        speak("Không có thành phố nào được cung cấp!")
        return
    api_key = "fe8d8c65cf345889139d8e545f57819a"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data["cod"] != "404":
        city_res = data["main"]
        current_temp = city_res["temp"]
        current_pressure = city_res["pressure"]
        current_humidity = city_res["humidity"]
        sun_time  = data["sys"]
        sun_rise = datetime.datetime.fromtimestamp(sun_time["sunrise"])
        sun_set = datetime.datetime.fromtimestamp(sun_time["sunset"])
        weather_desc = data["weather"][0]["description"]
        now = datetime.datetime.now()
        content = f"""
        Hôm nay là ngày {now.day} tháng {now.month} năm {now.year}
        Mặt trời mọc vào {sun_rise.hour} giờ {sun_rise.minute} phút
        Mặt trời lặn vào {sun_set.hour} giờ {sun_set.minute} phút
        Nhiệt độ trung bình là {current_temp} độ C
        Áp suất không khí là {current_pressure} hPa
        Độ ẩm là {current_humidity}%.
        Trời hôm nay {weather_desc}.
        """
        speak(content)
        time.sleep(25)  
    else:
        speak("Không tìm thấy thành phố!")

# Hàm tìm kiếm Google
def google_search():
    speak("Bạn muốn tìm kiếm gì trên Google?")
    search_for = get_text()
    if search_for:
        webbrowser.open(f"https://www.google.com/search?q={search_for}")
        speak(f"Tôi đã tìm kiếm {search_for} trên Google.")
    else:
        speak("Không có gì để tìm kiếm!")

# Hàm mở trang web
def open_website(text):
    regex = re.search(r'mở (.+)', text)
    if regex:
        domain = regex.group(1)
        url = 'https://www.' + domain
        webbrowser.open(url)
        speak(f"Tôi đã mở trang web {domain} cho bạn.")
        time.sleep(5)
    else:
        speak("Không thể mở trang web này.")

# Hàm chơi nhạc trên YouTube
def play_youtube():
    speak("Xin mời bạn chọn bài hát")
    song_name = get_text()
    if song_name:
        results = YoutubeSearch(song_name, max_results=1).to_dict()
        if results:
            url = f'https://www.youtube.com{results[0]["url_suffix"]}'
            webbrowser.open(url)
            speak(f"Tôi đã mở bài hát {song_name} cho bạn.")
        else:
            speak("Không tìm thấy bài hát.")
    else:
        speak("Không có tên bài hát nào được cung cấp.")

# Hàm mở ứng dụng
def open_application(text):
    if "google" in text:
        os.startfile(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
        speak("Đang mở Google Chrome.")
    elif "word" in text:
        os.startfile(r"C:\Program Files\Microsoft Office\Office15\WINWORD.EXE")
        speak("Đang mở Microsoft Word.")
    elif "zalo" in text:
        os.startfile(r"C:\Users\NGUYEN ANH TUAN\AppData\Local\Programs\Zalo\Zalo.exe")
        speak("Đang mở zalo")
    else:
        speak("Không tìm thấy ứng dụng này.")

# Hàm kể chuyện hoặc đọc Wikipedia
def tell_me():
    speak("Bạn muốn nghe về gì ạ?")
    topic = get_text()
    if topic:
        try:
            import wikipedia
            wikipedia.set_lang("vi")
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except:
            speak("Xin lỗi, tôi không tìm thấy thông tin về chủ đề này.")
    else:
        speak("Không có chủ đề nào được cung cấp.")

# Hàm chính gọi trợ lý ảo
def call_sen():
    speak("Xin chào, bạn tên là gì nhỉ?")
    time.sleep(3)
    name = get_text()
    if name:
        speak(f"Chào bạn {name}.")
        while True:
            speak("Bạn cần tôi làm gì?")
            time.sleep(3)
            text = get_text()
            if not text:
                break
            intent = classify_intent(text)  
            handle_intent(intent, name, text)

call_sen()
