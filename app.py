import streamlit as st
import random
import pandas as pd
import json
import os
from datetime import datetime
import shutil

# Constants
BASE_DIR = "data"
USERS_DIR = os.path.join(BASE_DIR, "users")
MASTER_WORDS_FILE = 'words.csv'
MIN_GAP_BETWEEN_WORDS = 5
TARGET_COUNT = 2

st.set_page_config(
    page_title="Learn Words",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

def ensure_user_directory(user_id):
    """Kullanıcı dizinini ve gerekli dosyaları oluşturur"""
    user_dir = os.path.join(USERS_DIR, user_id)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
        
    progress_file = os.path.join(user_dir, "words_progress.json")
    if not os.path.exists(progress_file):
        # Tüm kelimeleri count=0 ile başlat
        df = pd.read_csv(MASTER_WORDS_FILE)
        progress = {
            "words": {word: {"count": 0, "last_seen_index": None} 
                     for word in df['english_word']},
            "current_index": 0,
            "last_update": str(datetime.now())
        }
        save_progress(user_id, progress)

def load_progress(user_id):
    """Kullanıcının ilerlemesini yükler"""
    progress_file = os.path.join(USERS_DIR, user_id, "words_progress.json")
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_progress(user_id, progress_data):
    """Kullanıcının ilerlemesini kaydeder"""
    progress_file = os.path.join(USERS_DIR, user_id, "words_progress.json")
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def get_available_words(user_id, current_index):
    """Gösterilebilecek kelimeleri filtreler"""
    progress = load_progress(user_id)
    words_progress = progress["words"]
    
    # Önce hedef sayıya ulaşmamış kelimeleri kontrol et
    incomplete_words = []
    words_with_gap = []
    df = pd.read_csv(MASTER_WORDS_FILE)
    
    for idx, row in df.iterrows():
        word = row['english_word']
        word_progress = words_progress[word]
        
        if word_progress["count"] < TARGET_COUNT:
            incomplete_words.append(row.to_dict())
            last_seen = word_progress["last_seen_index"]
            
            # Minimum aralık şartını kontrol et
            if last_seen is None or (current_index - last_seen) >= MIN_GAP_BETWEEN_WORDS:
                words_with_gap.append(row.to_dict())
    
    # Eğer hiç tamamlanmamış kelime yoksa oyun bitmiştir
    if not incomplete_words:
        return None
        
    # Önce aralık şartını sağlayan kelimeleri dene
    if words_with_gap:
        return random.choice(words_with_gap)
    
    # Aralık şartını sağlayan kelime yoksa, herhangi bir tamamlanmamış kelimeyi seç
    return random.choice(incomplete_words)

def update_word_progress(user_id, word, is_correct):
    """Kelime ilerlemesini günceller"""
    progress = load_progress(user_id)
    
    if is_correct:
        progress["words"][word]["count"] += 1
    else:  # 2 yanlış cevap durumunda
        progress["words"][word]["count"] = max(0, progress["words"][word]["count"] - 1)
    
    progress["words"][word]["last_seen_index"] = progress["current_index"]
    progress["current_index"] += 1
    save_progress(user_id, progress)

def get_statistics(user_id):
    """Kullanıcı istatistiklerini hesaplar"""
    progress = load_progress(user_id)
    words_progress = progress["words"]
    
    total_words = len(words_progress)
    level_0_words = sum(1 for w in words_progress.values() if w["count"] == 0)
    level_1_words = sum(1 for w in words_progress.values() if w["count"] == 1)
    completed_words = sum(1 for w in words_progress.values() if w["count"] == TARGET_COUNT)
    
    return {
        "total": total_words,
        "level_0": level_0_words,
        "level_1": level_1_words,
        "completed": completed_words
    }

def get_progress_percentage(user_id):
    """Her kelime için count değerlerini toplayıp toplam hedef değere böler"""
    progress = load_progress(user_id)
    words_progress = progress["words"]
    
    # Mevcut toplam count
    total_count = sum(w["count"] for w in words_progress.values())
    
    # Hedef toplam (kelime sayısı * TARGET_COUNT)
    total_target = len(words_progress) * TARGET_COUNT
    
    return (total_count / total_target) * 100

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
        
        if 'user_id' in st.session_state:
            stats = get_statistics(st.session_state.user_id)
            st.markdown("""
                - Total Words: {} words
                - Not Started: {} words
                - Level 1: {} words
                - Completed: {} words
            """.format(
                stats["total"],
                stats["level_0"],
                stats["level_1"],
                stats["completed"]
            ))
        
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
                ensure_user_directory(user_id)
                progress = load_progress(user_id)
                
                st.session_state.current_word = None
                st.session_state.show_error = False
                st.session_state.needs_rerun = False
                st.session_state.wrong_attempts = 0
                st.session_state.show_last_card = False
                st.session_state.last_word = None
                st.rerun()
        return

    def check_answer():
        answer = st.session_state.current_answer.strip().lower()
        correct_answer = st.session_state.current_word['english_word'].lower()
        
        if answer == correct_answer:
            st.session_state.last_word = st.session_state.current_word
            # Kelime tamamlandı mı kontrol et
            progress = load_progress(st.session_state.user_id)
            current_count = progress["words"][correct_answer]["count"]
            
            update_word_progress(st.session_state.user_id, correct_answer, True)
            st.session_state.show_error = False
            st.session_state.current_answer = ""
            st.session_state.wrong_attempts = 0
            
            # Eğer kelime yeni tamamlandıysa (count 2'ye ulaştıysa) 1 saniye bekle
            if current_count == 1:  # Bu doğru cevapla 2'ye ulaşacak
                import time
                time.sleep(1)
            else:  # Normal kart değişiminde 0.5 saniye bekle
                import time
                time.sleep(0.3)
            
            st.session_state.needs_rerun = True
        else:
            st.session_state.show_error = True
            st.session_state.wrong_attempts += 1
            st.session_state.current_answer = ""
            if st.session_state.wrong_attempts >= 2:
                update_word_progress(st.session_state.user_id, correct_answer, False)
                st.session_state.last_word = st.session_state.current_word
                st.session_state.wrong_attempts = 0
                st.session_state.show_error = False
                st.session_state.needs_rerun = True

    def show_card(word_data, show_answer=False):
        if show_answer:
            highlighted_sentence = word_data['english_sentence'].replace(
                "___", 
                f'<span class="highlight">{word_data["english_word"]}</span>'
            )
        else:
            blank = "_" * len(word_data['english_word'])
            highlighted_sentence = word_data['english_sentence'].replace("___", blank)
        
        # Level indicator'ı ekle
        word = word_data['english_word'].lower()
        progress = load_progress(st.session_state.user_id)
        word_count = progress["words"][word]["count"]
        
        dots_html = '<div class="level-indicator">'
        for i in range(2):
            dot_class = "active" if i < (word_count + 1) else ""
            dots_html += f'<div class="level-dot {dot_class}"></div>'
        dots_html += '</div>'
        
        question_card = f"""
            <div class="question-card">
                {dots_html}
                <div class="word-display">{highlighted_sentence}</div>
                <div class="target-word">
                    <span class="highlight">{word_data['turkish_word']}</span> 
                    <span class="word-info">{word_data['word_info']}</span>
                </div>
                <div class="turkish-sentence">{word_data['turkish_sentence']}</div>
            </div>
        """
        st.markdown(question_card, unsafe_allow_html=True)

    if st.session_state.needs_rerun:
        st.session_state.needs_rerun = False
        st.session_state.current_word = None
        st.rerun()

    # Ana içerik alanı
    main_container = st.container()
    with main_container:
        progress = load_progress(st.session_state.user_id)
        current_index = progress["current_index"]
        
        # Progress bar için tamamlanma yüzdesini hesapla
        progress_percentage = get_progress_percentage(st.session_state.user_id)
        
        # İlerleme çubuğu
        progress_bar_html = f"""
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {progress_percentage}%;"></div>
            </div>
        """
        st.markdown(progress_bar_html, unsafe_allow_html=True)
        
        # Eğer mevcut kelime yoksa yeni kelime al
        if st.session_state.current_word is None:
            word = get_available_words(st.session_state.user_id, current_index)
            if word is None:  # Tüm kelimeler tamamlandı
                st.markdown("""
                    <div class="finish-screen">
                        <div class="celebration">🎉</div>
                        <h1>Congratulations!</h1>
                        <p>You have successfully completed all words.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("Start Over"):
                    # Tüm kelimelerin count değerlerini sıfırla
                    progress = load_progress(st.session_state.user_id)
                    for word in progress["words"]:
                        progress["words"][word]["count"] = 0
                        progress["words"][word]["last_seen_index"] = None
                    progress["current_index"] = 0
                    save_progress(st.session_state.user_id, progress)
                    st.session_state.current_word = None
                    st.session_state.wrong_attempts = 0
                    st.session_state.last_word = None
                    st.rerun()
                return
            st.session_state.current_word = word
        
        if st.session_state.show_last_card and st.session_state.last_word:
            show_card(st.session_state.last_word, show_answer=True)
        else:
            show_card(st.session_state.current_word)
            
        answer = st.text_input(
            "Your answer",
            key="current_answer",
            label_visibility="collapsed",
            on_change=check_answer
        )
        
        if st.session_state.show_error:
            if st.session_state.wrong_attempts == 1:
                st.markdown(f'<div class="error-message">Wrong answer, try again</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tip-message">{st.session_state.current_word["english_word"][0]}</div>', unsafe_allow_html=True)
            elif st.session_state.wrong_attempts == 2:
                st.markdown(f'<div class="error-message">Wrong answer</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="answer-message">answer: {st.session_state.current_word["english_word"]}</div>', unsafe_allow_html=True)
                import time
                time.sleep(1)
                st.rerun()

        # Navigation buttons container
        st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
        left_col, right_col = st.columns(2)
        with left_col:
            if st.button("Last Card", key="last_card", disabled=st.session_state.last_word is None):
                st.session_state.show_last_card = True
        with right_col:
            if st.button("New Card", key="new_card"):
                import time
                time.sleep(0.3)  # New Card butonuna basıldığında 0.5 saniye bekle
                st.session_state.show_last_card = False
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()