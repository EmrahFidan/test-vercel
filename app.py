import streamlit as st
import random
import json
import os
from datetime import datetime

# İlerleme dosyasının yolu
PROGRESS_FILE = 'user_progress.json'

# Kelime çiftleri
word_pairs = {
    "apple": "elma",
    "book": "kitap",
    "house": "ev",
    "tree": "ağaç",
    "sun": "güneş",
    "water": "su",
    "bread": "ekmek",
    "flower": "çiçek",
    "bird": "kuş",
    "moon": "ay"
}

# İlerleme yönetimi fonksiyonları
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_progress(progress_data):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

# Uygulama başlangıcı
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'word_list' not in st.session_state:
    st.session_state.word_list = list(word_pairs.items())
    random.shuffle(st.session_state.word_list)

# Kullanıcı girişi
if st.session_state.user_id is None:
    with st.form("kullanici_giris"):
        user_id = st.text_input("Kullanıcı adınızı girin:")
        submitted = st.form_submit_button("Giriş Yap")
        if submitted and user_id:
            progress_data = load_progress()
            st.session_state.user_id = user_id
            
            # Kullanıcının mevcut ilerlemesini kontrol et
            if user_id in progress_data:
                st.session_state.current_word_index = progress_data[user_id]['current_index']
            else:
                st.session_state.current_word_index = 0
                progress_data[user_id] = {
                    'current_index': 0,
                    'last_update': str(datetime.now())
                }
                save_progress(progress_data)
            st.rerun()

elif st.session_state.user_id:
    st.title('İngilizce-Türkçe Kelime Öğrenme Oyunu')
    st.write(f"Kullanıcı: {st.session_state.user_id}")

    def update_progress():
        progress_data = load_progress()
        progress_data[st.session_state.user_id] = {
            'current_index': st.session_state.current_word_index,
            'last_update': str(datetime.now())
        }
        save_progress(progress_data)

    def next_word():
        st.session_state.current_word_index += 1
        update_progress()

    def reset_game():
        st.session_state.current_word_index = 0
        update_progress()
        random.shuffle(st.session_state.word_list)

    # Oyun mantığı
    if st.session_state.current_word_index < len(st.session_state.word_list):
        current_word, correct_answer = st.session_state.word_list[st.session_state.current_word_index]
        
        st.write(f"### Kelime {st.session_state.current_word_index + 1}/10:")
        st.write(f"## {current_word}")
        
        user_answer = st.text_input("Bu kelimenin Türkçe karşılığını yazın:", 
                                  key=f"answer_{st.session_state.current_word_index}")
        
        if user_answer:
            if user_answer.lower().strip() == correct_answer.lower():
                st.success("Doğru cevap! 👏")
                if st.button("Sonraki Kelime"):
                    next_word()
                    st.rerun()
            else:
                st.error("Yanlış cevap. Tekrar deneyin!")
                
    else:
        st.balloons()
        st.success("🎉 Tebrikler! Tüm kelimeleri başarıyla tamamladınız! 🎉")
        
        if st.button("Oyunu Yeniden Başlat"):
            reset_game()
            st.rerun()

    # İlerleme çubuğu
    progress = st.session_state.current_word_index / len(st.session_state.word_list)
    st.progress(progress)

    # Çıkış yap butonu
    if st.button("Çıkış Yap"):
        st.session_state.user_id = None
        st.rerun()