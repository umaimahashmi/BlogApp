
from flask import Flask, render_template, request, redirect, url_for
from config import get_db_connection
import json
app = Flask(__name__)

@app.route('/')
def display_articles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles")
    articles = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('display_articles.html', articles=articles)


#**************************************************************************************************
#**************************************************************************************************
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add', methods=['GET', 'POST'])
def add_article():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        content = request.form['content']
        
        files = request.files.getlist('images')
        image_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                image_paths.append(f'uploads/{filename}')
        
        image_paths_json = json.dumps(image_paths)  # Store as JSON array

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO articles (title, description, content, images) VALUES (%s, %s, %s, %s)",
                       (title, description, content, image_paths_json))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('display_articles'))
    return render_template('add_article.html')

@app.route('/article/<int:id>')
def view_article(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles WHERE id = %s", (id,))
    article = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if article and article['images']:
        article['images'] = json.loads(article['images'])  # Decode JSON array
    
    return render_template('view_article.html', article=article)


import os

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM articles WHERE id = %s", (id,))
    article = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        content = request.form['content']
        
        files = request.files.getlist('images')
        image_paths = json.loads(article['images']) if article['images'] else []
        
        # Save new images
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                image_paths.append(filename)  # Store filename only, not full path
        
        # Handle image deletions
        delete_images = request.form.getlist('delete_images')
        for image in delete_images:
            if image in image_paths:
                image_paths.remove(image)
                full_path = os.path.join(UPLOAD_FOLDER, image)
                if os.path.exists(full_path):
                    os.remove(full_path)
        
        image_paths_json = json.dumps(image_paths)
        
        cursor = conn.cursor()
        cursor.execute("UPDATE articles SET title = %s, description = %s, content = %s, images = %s WHERE id = %s",
                       (title, description, content, image_paths_json, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('display_articles'))
    
    conn.close()
    if article['images']:
        article['images'] = json.loads(article['images'])
    return render_template('edit_article.html', article=article)




@app.route('/delete/<int:id>', methods=['GET'])
def delete_article(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('display_articles'))

if __name__ == '__main__':
    app.run(debug=True)