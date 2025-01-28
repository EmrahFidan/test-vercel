import streamlit as st
import random
import pandas as pd
import json
import os
from datetime import datetime

# Dosya yolu
PROGRESS_FILE = 'user_progress.json'

st.set_page_config(
    page_title="Kelime Öğren",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# İlerleme yönetimi fonksiyonları
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_progress(progress_data):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

@st.cache_data
def load_words():
    df = pd.read_csv('words.csv')
    return dict(zip(df['turkish_sentence'], zip(df['english_word'], df['turkish_word'])))

def load_css():
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    load_css()
    
    # Kullanıcı girişi kontrolü
    if 'user_id' not in st.session_state:
        with st.form("kullanici_giris"):
            user_id = st.text_input("Kullanıcı adınızı girin:")
            submitted = st.form_submit_button("Giriş Yap")
            
            if submitted and user_id:
                st.session_state.user_id = user_id
                progress_data = load_progress()
                
                # Session state'leri başlat
                st.session_state.word_pairs = load_words()
                st.session_state.word_list = list(st.session_state.word_pairs.items())
                random.shuffle(st.session_state.word_list)
                
                # Kullanıcının kaldığı yerden devam et
                if user_id in progress_data:
                    st.session_state.current_index = progress_data[user_id]['current_index']
                else:
                    st.session_state.current_index = 0
                
                st.session_state.show_error = False
                st.session_state.needs_rerun = False
                st.session_state.wrong_answer = False
                st.session_state.wrong_attempts = 0
                st.rerun()
        return

    def check_answer():
        answer = st.session_state.current_answer
        correct_answer = st.session_state.word_list[st.session_state.current_index][1][0]  # [0] for english_word
        
        if answer.lower().strip() == correct_answer.lower():
            st.session_state.current_index += 1
            st.session_state.show_error = False
            st.session_state.current_answer = ""
            st.session_state.wrong_attempts = 0
            
            # İlerlemeyi kaydet
            progress_data = load_progress()
            progress_data[st.session_state.user_id] = {
                'current_index': st.session_state.current_index,
                'last_update': str(datetime.now())
            }
            save_progress(progress_data)
            
            st.session_state.needs_rerun = True
        else:
            st.session_state.show_error = True
            st.session_state.wrong_answer = True
            st.session_state.wrong_attempts += 1
            st.session_state.current_answer = ""

    if st.session_state.get('wrong_answer', False):
        st.session_state.wrong_answer = False
        st.session_state.current_answer = ""

    if st.session_state.needs_rerun:
        st.session_state.needs_rerun = False
        st.rerun()

    if st.session_state.current_index < len(st.session_state.word_list):
        current_sentence, (correct_answer, target_word) = st.session_state.word_list[st.session_state.current_index]
        
        # İlerleme çubuğu
        progress = (st.session_state.current_index / len(st.session_state.word_list)) * 100
        progress_bar_html = f"""
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {progress}%;"></div>
            </div>
        """
        st.markdown(progress_bar_html, unsafe_allow_html=True)
        
        # Soru kartı
        question_card = f"""
            <div class="question-card">
                <div class="word-display">{current_sentence.replace(target_word, f'<span style="color: #19b48d;">{target_word}</span>')}</div>
            </div>
        """
        st.markdown(question_card, unsafe_allow_html=True)
        
        answer = st.text_input(
            "Cevabınız",
            key="current_answer",
            label_visibility="collapsed",
            on_change=check_answer
        )
        
        if st.session_state.show_error:
            wrong_attempts = st.session_state.wrong_attempts
            hint = correct_answer[:min(wrong_attempts, len(correct_answer))]
            st.markdown(f'<div class="error-message">Yanlış cevap!</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="tip-message">{hint}</div>', unsafe_allow_html=True)

        st.markdown('<div class="info-message">Cevabınızı yazdıktan sonra Enter tuşuna basın</div>', unsafe_allow_html=True)
    else:
        # Tüm kelimeler tamamlandığında
        st.markdown("""
            <div class="finish-screen">
                <div class="celebration">🎉</div>
                <h1>Tebrikler!</h1>
                <p>Tüm kelimeleri başarıyla tamamladınız.</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Tekrar Başla"):
            st.session_state.current_index = 0
            st.session_state.wrong_attempts = 0
            random.shuffle(st.session_state.word_list)
            st.rerun()

    # Çıkış butonu
    if st.button("Çıkış Yap"):
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()