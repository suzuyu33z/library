import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from datetime import date

# .env 読み込み
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

def go_to(page, book=None):
    st.session_state.page = page
    if book:
        st.session_state.selected_book = book

# 書籍一覧
def home():
    st.title("📚 書籍一覧")
    query = st.text_input("🔍 書籍名で検索")

    try:
        books = supabase.table("books").select("*").execute().data
    except Exception as e:
        st.error(f"❌ Supabaseから書籍を取得できませんでした: {e}")
        books = []

    filtered_books = [
        book for book in books if query.lower() in book["book_name"].lower()
    ] if query else books

    if not filtered_books:
        st.write("📭 該当する書籍はありません")

    for i, book in enumerate(filtered_books):
        st.write(f"### [{book['book_name']}](#)")
        st.write(f"ステータス: {book['status']}")
        if st.button(f"詳細へ", key=f"detail_{i}"):
            go_to("detail", book=book)
            st.rerun()

# 書籍詳細
def detail():
    book = st.session_state.selected_book
    st.title(book["book_name"])
    st.write(f"ステータス: {book['status']}")

    if st.button("借りる", key="borrow_button"):
        go_to("borrow_input", book)
        st.rerun()

    if st.button("返却する", key="return_button"):
        go_to("return_confirm", book)
        st.rerun()

    if st.button("レビューを書く", key="review_button"):
        go_to("review_input", book)
        st.rerun()

    if st.button("戻る", key="back_button"):
        go_to("home")
        st.rerun()

    st.subheader("レビュー")
    try:
        reviews = supabase.table("review").select("*").eq("book_id", book["book_id"]).execute().data
        if reviews:
            for r in reviews:
                st.write(f"💬 {r['message']} by {r['reviewer']}")
        else:
            st.write("レビューはまだありません。")
    except Exception as e:
        st.error(f"❌ レビューの取得に失敗しました: {e}")

# 借りる（貸出日・返却日入力に変更）
def borrow_input():
    book = st.session_state.selected_book
    st.title(f"{book['book_name']} を借りる")

    name = st.text_input("自分の名前を入力", key="borrow_name")
    borrow_start = st.date_input("貸出日", value=date.today(), min_value=date.today())
    borrow_end = st.date_input("返却予定日", value=date.today(), min_value=borrow_start)

    if st.button("借りる", key="borrow_confirm_button"):
        if borrow_end < borrow_start:
            st.warning("⚠️ 返却予定日は貸出日と同日またはそれ以降にしてください。")
            return
        try:
            borrow_data = {
                "book_id": book["book_id"],
                "username": name,
                "borrow_start": str(borrow_start),
                "borrow_end": str(borrow_end)
            }
            supabase.table("borrow").insert(borrow_data).execute()
            supabase.table("books").update({"status": "貸出中"}).eq("book_id", book["book_id"]).execute()
            st.success("✅ 書籍を借りました！")
            go_to("detail")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 書籍の貸出に失敗しました: {e}")

    if st.button("戻る", key="borrow_back_button"):
        go_to("detail")
        st.rerun()

# 返却
def return_confirm():
    book = st.session_state.selected_book
    st.title(f"{book['book_name']} の返却")
    st.write("書籍を返却しますか？")

    if st.button("返却する", key="return_confirm_button"):
        try:
            supabase.table("books").update({"status": "利用可能"}).eq("book_id", book["book_id"]).execute()
            st.success("✅ 書籍を返却しました！")
            go_to("detail")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 書籍の返却に失敗しました: {e}")

    if st.button("戻る", key="return_back_button"):
        go_to("detail")
        st.rerun()

# レビュー
def review_input():
    book = st.session_state.selected_book
    st.title(f"{book['book_name']} のレビュー")

    name = st.text_input("自分の名前を入力", key="review_name")
    message = st.text_area("レビューを入力", key="review_message")

    if st.button("送信", key="review_submit_button"):
        try:
            review_data = {
                "book_id": book["book_id"],
                "reviewer": name,
                "message": message
            }
            supabase.table("review").insert(review_data).execute()
            st.success("✅ レビューを送信しました！")
            go_to("detail")
            st.rerun()
        except Exception as e:
            st.error(f"❌ レビューの送信に失敗しました: {e}")

    if st.button("戻る", key="review_back_button"):
        go_to("detail")
        st.rerun()

# 画面描画
page = st.session_state.page

if page == "home":
    home()
elif page == "detail":
    detail()
elif page == "borrow_input":
    borrow_input()
elif page == "return_confirm":
    return_confirm()
elif page == "review_input":
    review_input()