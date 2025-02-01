import streamlit as st
import random
import pandas as pd
import json
import os
from datetime import datetime

# Dosya yolu
PROGRESS_FILE = 'user_progress.json'

st.set_page_config(
    page_title="Learn Words",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
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
    return dict(zip(df['english_sentence'], 
                   zip(df['english_word'], 
                       df['turkish_word'], 
                       df['turkish_sentence'],
                       df['word_info'])))

def load_css():
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    load_css()

    # Sidebar içeriği
    with st.sidebar:
        st.markdown("""
            <div class="sidebar-content">
                <div class="user-info">
                    <span>Welcome <span class="username">{}</span></span>
                </div>
            </div>
        """.format(st.session_state.get('user_id', '')), unsafe_allow_html=True)
        
        # Logout button in sidebar footer
        with st.container():
            st.markdown('<div class="sidebar-logout">', unsafe_allow_html=True)
            if st.button("Logout", key="sidebar_logout"):
                st.session_state.clear()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Kullanıcı girişi kontrolü
    if 'user_id' not in st.session_state:
        with st.form("kullanici_giris"):
            user_id = st.text_input("Enter your username:")
            submitted = st.form_submit_button("Login")
            
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
                st.session_state.show_last_card = False
                st.session_state.last_card_index = None
                st.rerun()
        return

    def check_answer():
        answer = st.session_state.current_answer
        correct_answer = st.session_state.word_list[st.session_state.current_index][1][0]  # [0] for english_word
        
        if answer.lower().strip() == correct_answer.lower():
            st.session_state.last_card_index = st.session_state.current_index
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

    def show_card(index, show_answer=False):
        english_sentence, (correct_answer, turkish_word, turkish_sentence, word_info) = st.session_state.word_list[index]
        
        if show_answer:
            # Doğru cevabı renkli göster
            highlighted_sentence = english_sentence.replace(
                "___", 
                f'<span class="highlight">{correct_answer}</span>'
            )
        else:
            # Alt çizgi sayısını ayarla
            blank = "_" * len(correct_answer)
            highlighted_sentence = english_sentence.replace("___", blank)
        
        # Soru kartı
        question_card = f"""
            <div class="question-card">
                <div class="word-display">{highlighted_sentence}</div>
                <div class="target-word"><span class="highlight">{turkish_word}</span> <span class="word-info">{word_info}</span></div>
                <div class="turkish-sentence">{turkish_sentence}</div>
            </div>
        """
        st.markdown(question_card, unsafe_allow_html=True)

    if st.session_state.get('wrong_answer', False):
        st.session_state.wrong_answer = False
        st.session_state.current_answer = ""

    if st.session_state.needs_rerun:
        st.session_state.needs_rerun = False
        st.rerun()

    if st.session_state.current_index < len(st.session_state.word_list):
        # Ana içerik alanı
        main_container = st.container()
        with main_container:
            # İlerleme çubuğu
            progress = (st.session_state.current_index / len(st.session_state.word_list)) * 100
            progress_bar_html = f"""
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: {progress}%;"></div>
                </div>
            """
            st.markdown(progress_bar_html, unsafe_allow_html=True)
            
            if st.session_state.show_last_card and st.session_state.last_card_index is not None:
                show_card(st.session_state.last_card_index, show_answer=True)
            else:
                show_card(st.session_state.current_index)
            
            answer = st.text_input(
                "Your answer",
                key="current_answer",
                label_visibility="collapsed",
                on_change=check_answer
            )

            st.markdown('<div class="info-message">Press Enter after typing your answer</div>', unsafe_allow_html=True)

            
            
            if st.session_state.show_error:
                if st.session_state.wrong_attempts == 1:  # İlk yanlış tahmin
                    st.markdown(f'<div class="error-message">Wrong answer, try again</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="tip-message">{st.session_state.word_list[st.session_state.current_index][1][0][0]}</div>', unsafe_allow_html=True)
                elif st.session_state.wrong_attempts == 2:  # İkinci yanlış tahmin
                    st.markdown(f'<div class="error-message">Wrong answer</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="answer-message">answer: {st.session_state.word_list[st.session_state.current_index][1][0]}</div>', unsafe_allow_html=True)
                    # 1 saniye sonra otomatik geçiş için
                    import time
                    time.sleep(1)
                    st.session_state.last_card_index = st.session_state.current_index
                    st.session_state.current_index += 1
                    st.session_state.wrong_attempts = 0
                    st.session_state.show_error = False
                    st.rerun()

            # Navigation buttons container
            st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
            left_col, right_col = st.columns(2)
            with left_col:
                if st.button("Last Card", disabled=st.session_state.last_card_index is None, key="last_card"):
                    st.session_state.show_last_card = True
            with right_col:
                if st.button("New Card", key="new_card"):
                    st.session_state.show_last_card = False
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Tüm kelimeler tamamlandığında
        st.markdown("""
            <div class="finish-screen">
                <div class="celebration">🎉</div>
                <h1>Congratulations!</h1>
                <p>You have successfully completed all words.</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Over"):
            st.session_state.current_index = 0
            st.session_state.wrong_attempts = 0
            st.session_state.last_card_index = None
            random.shuffle(st.session_state.word_list)
            st.rerun()

if __name__ == "__main__":
    main()