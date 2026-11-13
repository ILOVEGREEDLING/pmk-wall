from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me'  # Секретный ключ для сессий админа
ADMIN_PASSWORD = 'admin'                      # Пароль для входа в админку (можешь поменять)

def get_db():
    conn = sqlite3.connect('pmk_wall.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создаем таблицу базы данных при первом запуске, если её нет
with get_db() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            tag TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    ''')

@app.route('/')
def index():
    conn = get_db()
    # Выводим только одобренные посты на главную страницу
    posts = conn.execute("SELECT * FROM posts WHERE status = 'approved' ORDER BY id DESC").fetchall()
    return render_template('index.html', posts=posts)

@app.route('/add', methods=['POST'])
def add_post():
    text = request.form.get('text', '').strip()
    tag = request.form.get('tag', '#жиза')
    if text and len(text) <= 1000:
        now = datetime.now().strftime("%d.%m %H:%M")
        with get_db() as conn:
            conn.execute("INSERT INTO posts (text, tag, created_at) VALUES (?, ?, ?)", (text, tag, now))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin'))
    return '''
        <form method="post" style="padding: 40px; font-family: sans-serif; background: #111; color: #fff;">
            <h2>Вход в админку ПМК</h2>
            <input type="password" name="password" placeholder="Пароль" style="padding: 8px; margin-right: 8px;">
            <button type="submit" style="padding: 8px 16px;">Войти</button>
        </form>
    '''

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    conn = get_db()
    # Показываем посты, которые ждут модерации
    pending_posts = conn.execute("SELECT * FROM posts WHERE status = 'pending' ORDER BY id DESC").fetchall()
    return render_template('admin.html', posts=pending_posts)

@app.route('/approve/<int:post_id>')
def approve(post_id):
    if session.get('is_admin'):
        with get_db() as conn:
            conn.execute("UPDATE posts SET status = 'approved' WHERE id = ?", (post_id,))
    return redirect(url_for('admin'))

@app.route('/delete/<int:post_id>')
def delete(post_id):
    if session.get('is_admin'):
        with get_db() as conn:
            conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)