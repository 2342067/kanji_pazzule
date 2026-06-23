import sqlite3
import os

def get_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "puzzle.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DBファイルが見つかりません: {db_path}")

    # 読み取り専用で開く（誤って書き込んでしまうのも防げる）
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def get_words(field=None, difficulty=None):
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT id, word, field, difficulty FROM words"
    conditions = []
    params = []

    if field:
        conditions.append("field=?")
        params.append(field)
    if difficulty:
        conditions.append("difficulty=?")
        params.append(difficulty)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_questions(field, difficulty):
    """指定した分野・難易度の問題一覧を取得する"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, field, difficulty, word_count FROM questions WHERE field=? AND difficulty=? ORDER BY id",
        (field, difficulty)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_question_words(question_id):
    """指定した問題に含まれる単語と空欄情報を取得する"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT words.word, question_words.blank_position, question_words.blank_number
        FROM question_words
        JOIN words ON question_words.word_id = words.id
        WHERE question_words.question_id=?
    """, (question_id,))
    rows = cur.fetchall()
    conn.close()
    return rows