from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

WEBHOOK_URL = "http://localhost:5678/webhook-test/82f5d629-cd85-4090-81b8-bd7b8682f385"

def send_to_webhook(data):
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code == 200:
            print("Gửi dữ liệu đến webhook thành công!")
        else:
            print(f"Lỗi khi gửi dữ liệu: {response.status_code}")
    except Exception as e:
        print(f"Lỗi khi kết nối webhook: {e}")

# Tạo bảng nếu chưa có
def create_tables():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM product")
    if cursor.fetchone()[0] == 0:
        products = [
            ('Laptop', 15000000),
            ('Điện thoại', 8000000),
            ('Tai nghe', 1200000),
            ('Chuột máy tính', 500000)
        ]
        cursor.executemany("INSERT INTO product (name, price) VALUES (?, ?)", products)

    conn.commit()
    conn.close()

@app.route('/')
def home():
    return redirect(url_for('login')) if 'user_id' not in session else redirect(url_for('dashboard'))

# Đăng ký
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
            conn.commit()
            conn.close()

            # send_to_webhook({"event": "signup", "name": name, "email": email})

            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email đã tồn tại!', 'danger')

    return render_template('signup.html')

# Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]

            # send_to_webhook({"event": "login", "user_id": user[0], "name": user[1], "email": email})

            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Thông tin đăng nhập không chính xác', 'danger')

    return render_template('login.html')

# Dashboard - Hiển thị sản phẩm
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product")
    products = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', name=session['user_name'], products=products)

# Thêm vào giỏ hàng
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product_id = request.form.get('product_id')

    # Kiểm tra product_id hợp lệ
    if not product_id or not product_id.isdigit():
        flash('Sản phẩm không hợp lệ!', 'danger')
        return redirect(url_for('dashboard'))

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append(int(product_id))
    session.modified = True

    flash('Sản phẩm đã được thêm vào giỏ hàng!', 'success')
    return redirect(url_for('cart'))

# Xem giỏ hàng
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', products=[])

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Truy vấn các sản phẩm có trong giỏ hàng
    query = "SELECT * FROM product WHERE id IN ({})".format(",".join("?" * len(session['cart'])))
    cursor.execute(query, tuple(session['cart']))
    products = cursor.fetchall()

    conn.close()

    return render_template('cart.html', products=products)

#thanh toan
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'cart' not in session or not session['cart']:
        flash('Không có sản phẩm nào trong giỏ hàng!', 'warning')
        return redirect(url_for('cart'))

    user_id = session['user_id']
    user_name = session['user_name']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Lấy email của user từ database
    cursor.execute("SELECT email FROM user WHERE id = ?", (user_id,))
    user_email = cursor.fetchone()[0]  # Lấy email

    # Lấy thông tin các sản phẩm trong giỏ hàng
    query = "SELECT id, name, price FROM product WHERE id IN ({})".format(",".join("?" * len(session['cart'])))
    cursor.execute(query, tuple(session['cart']))
    products = cursor.fetchall()

    # Tính tổng tiền
    total_amount = sum(product[2] for product in products)

    # Chuẩn bị dữ liệu gửi đến webhook
    checkout_data = {
        "event": "checkout",
        "user_id": user_id,
        "name": user_name,
        "email": user_email,  # Thêm email vào dữ liệu gửi webhook
        "total_amount": total_amount,
        "products": [{"id": p[0], "name": p[1], "price": p[2]} for p in products]
    }

    send_to_webhook(checkout_data)

    conn.close()

    # Xóa giỏ hàng sau khi thanh toán
    session.pop('cart', None)

    flash('Thanh toán thành công!', 'success')
    return redirect(url_for('dashboard'))



# Đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash('Đăng xuất thành công!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    product_id = request.form['product_id']

    # Xóa sản phẩm khỏi giỏ hàng
    if 'cart' in session and product_id in session['cart']:
        session['cart'].remove(product_id)
        session.modified = True

    flash('Đã xóa sản phẩm khỏi giỏ hàng!', 'success')
    return redirect(url_for('cart'))
