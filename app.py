from flask import Flask, render_template, request, send_from_directory
import re
import requests

app = Flask(__name__)

# Contentful config
SPACE_ID = "w1ok1fl3qefd"
ACCESS_TOKEN = "itrDNF-PCpzF1IJaLem_V5B9olesdt_HZKgRIFERxas"

# Calculate estimated reading time based on average speed (200 wpm)
def calculate_reading_time(word_count):
    words_per_minute = 200
    return round(word_count / words_per_minute)

# Calculate keyword density as percentage to one decimal place
def calculate_keyword_density(text, keyword):
    word_count = len(text.split())
    keyword_count = text.lower().split().count(keyword.lower())
    return round((keyword_count / word_count) * 100, 1) if word_count > 0 else 0

# Improved middle ground sentence case conversion
def to_sentence_case(text):
    sentences = re.split('([.!?])', text)
    result = []

    for i in range(0, len(sentences) - 1, 2):
        sentence = sentences[i].strip()
        punctuation = sentences[i + 1]
        if sentence:
            sentence = sentence[0].upper() + sentence[1:]
            result.append(sentence + punctuation)
    if len(sentences) % 2 != 0:
        result.append(sentences[-1])

    return ' '.join(result)

# Count paragraphs based on one or more line breaks, ignoring empty lines
def count_paragraphs(text):
    paragraphs = [p for p in re.split(r'\n+', text.strip()) if p.strip()]
    return paragraphs

# Home page route
@app.route("/")
def home():
    return render_template("index.html")

# Word counter route
@app.route("/word-counter", methods=["GET", "POST"])
def word_counter():
    text = ""
    word_count = 0
    char_count = 0
    reading_time = 0

    if request.method == "POST":
        text = request.form["text"]
        word_count = len(text.split())
        char_count = len(text)
        reading_time = calculate_reading_time(word_count)

    return render_template("word_counter.html", text=text, word_count=word_count, char_count=char_count, reading_time=reading_time)

# Keyword density calculator route
@app.route("/keyword-density", methods=["GET", "POST"])
def keyword_density():
    text = ""
    keyword = ""
    keyword_density_result = None

    if request.method == "POST":
        text = request.form["text"]
        keyword = request.form["keyword"]

        if text and keyword:
            clean_text = re.sub(r"[^\w\s]", "", text.lower())
            clean_keyword = keyword.lower()

            word_count = clean_text.split().count(clean_keyword)
            total_words = len(clean_text.split())

            if total_words > 0:
                keyword_density_result = round((word_count / total_words) * 100, 1)

    return render_template("keyword_density.html", text=text, keyword=keyword, keyword_density=keyword_density_result)

# Sentence case converter route
@app.route("/sentence-case", methods=["GET", "POST"])
def sentence_case():
    text = ""
    sentence_case_result = ""

    if request.method == "POST":
        text = request.form["text"]
        if text:
            sentence_case_result = to_sentence_case(text)

    return render_template("sentence_case.html", text=text, sentence_case=sentence_case_result)

# Paragraph counter route
@app.route("/paragraph-counter", methods=["GET", "POST"])
def paragraph_counter():
    text = ""
    paragraph_count = 0

    if request.method == "POST":
        text = request.form["text"]
        paragraphs = count_paragraphs(text)
        paragraph_count = len(paragraphs)

    return render_template("paragraph_counter.html", text=text, paragraph_count=paragraph_count)

# Sitemap route
@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory(app.static_folder, "sitemap.xml")

# Robots.txt route
@app.route("/robots.txt")
def robots_txt():
    return send_from_directory(app.static_folder, "robots.txt")

# Blog route to fetch Contentful entries
@app.route("/blog")
def blog():
    url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/entries"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {"content_type": "pageBlogPost"}  # Check your Contentful content model ID
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        entries = response.json().get("items", [])
    else:
        entries = []

    return render_template("blog.html", entries=entries)

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
