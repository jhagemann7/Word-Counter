from flask import Flask, render_template, request, send_from_directory
import re
import requests
import logging

app = Flask(__name__)

app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True

def render_rich_text(node):
    if not node:
        return ""

    content_html = ""

    for content in node.get("content", []):
        node_type = content.get("nodeType")

        if node_type == "paragraph":
            inner_html = render_rich_text(content)
            content_html += f"<p>{inner_html}</p>"

        elif node_type == "heading-1":
            inner_html = render_rich_text(content)
            content_html += f"<h1>{inner_html}</h1>"

        elif node_type == "heading-2":
            inner_html = render_rich_text(content)
            content_html += f"<h2>{inner_html}</h2>"

        elif node_type == "unordered-list":
            inner_html = render_rich_text(content)
            content_html += f"<ul>{inner_html}</ul>"

        elif node_type == "ordered-list":
            inner_html = render_rich_text(content)
            content_html += f"<ol>{inner_html}</ol>"

        elif node_type == "list-item":
            inner_html = render_rich_text(content)
            content_html += f"<li>{inner_html}</li>"

        elif node_type == "hyperlink":
            url = content["data"].get("uri", "#")
            inner_html = render_rich_text(content)
            content_html += f'<a href="{url}" target="_blank" rel="noopener noreferrer">{inner_html}</a>'

        elif node_type == "text":
            text_value = content.get("value", "")
            for mark in content.get("marks", []):
                if mark["type"] == "bold":
                    text_value = f"<strong>{text_value}</strong>"
                elif mark["type"] == "italic":
                    text_value = f"<em>{text_value}</em>"
            content_html += text_value

    return content_html

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
    urlset = '<?xml version="1.0" encoding="UTF-8"?>\n'
    urlset += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    base_url = "https://text-tool-kit.com"

    # Add static pages
    static_urls = [
        "/",
        "/word-counter",
        "/keyword-density",
        "/sentence-case",
        "/paragraph-counter",
        "/blog"
    ]

    for path in static_urls:
        urlset += f"<url><loc>{base_url}{path}</loc></url>\n"

    # Add blog posts dynamically
    try:
        url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/entries"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        params = {
            "content_type": "pageBlogPost",
            "order": "-sys.createdAt",
            "limit": 1000  # you can adjust this
        }
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        posts = data.get("items", [])

        for post in posts:
            slug = post.get("fields", {}).get("slug")
            if slug:
                urlset += f"<url><loc>{base_url}/blog/post/{slug}</loc></url>\n"

    except Exception as e:
        print("Error fetching posts for sitemap:", e)

    urlset += "</urlset>"

    return app.response_class(urlset, mimetype="application/xml")

# Robots.txt route
@app.route("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")

#Blog Route
@app.route("/blog", strict_slashes=False)
def blog():
    url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/entries"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    # Fetch landing page
    landing_params = {
        "content_type": "pageLanding",
        "limit": 1,
        "include": 2
    }
    landing_response = requests.get(url, headers=headers, params=landing_params)
    landing_data = landing_response.json() if landing_response.status_code == 200 else {}
    landing_page = landing_data.get("items", [None])[0]
    hero_image_url = None

    if landing_page:
        hero_image_ref = landing_page.get("fields", {}).get("heroImage")
        if hero_image_ref:
            image_id = hero_image_ref["sys"]["id"]
            asset = next((a for a in landing_data.get("includes", {}).get("Asset", []) if a["sys"]["id"] == image_id), None)
            if asset:
                hero_image_url = asset["fields"]["file"]["url"]

    # Fetch blog posts
    posts_params = {
        "content_type": "pageBlogPost",
        "order": "-sys.createdAt",
        "include": 2
    }
    posts_response = requests.get(url, headers=headers, params=posts_params)
    posts_data = posts_response.json() if posts_response.status_code == 200 else {}
    posts_items = posts_data.get("items", [])
    posts_includes = posts_data.get("includes", {})

    entries = []
    for item in posts_items:
        fields = item.get("fields", {})
        title = fields.get("title", "No title")
        slug = fields.get("slug", "")
        published_date = fields.get("publishedDate") or item["sys"]["createdAt"]
        subtitle = fields.get("subtitle", "")

        image_url = None
        if "featuredImage" in fields:
            image_id = fields["featuredImage"]["sys"]["id"]
            asset = next((a for a in posts_includes.get("Asset", []) if a["sys"]["id"] == image_id), None)
            if asset:
                image_url = asset["fields"]["file"]["url"]

        entries.append({
            "title": title,
            "date": published_date,
            "subtitle": subtitle,
            "image_url": image_url,
            "url": f"/blog/post/{slug}"
        })

    return render_template("blog.html",
                           landing=landing_page.get("fields") if landing_page else {},
                           hero_image_url=hero_image_url,
                           posts=entries)


@app.route("/blog/post/<slug>")
def blog_post(slug):
    try:
        url = f"https://cdn.contentful.com/spaces/{SPACE_ID}/entries"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        params = {
            "content_type": "pageBlogPost",
            "fields.slug": slug,
            "limit": 1,
            "include": 2
        }
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            return "Error fetching post data", 500

        data = response.json()
        post = data.get("items", [None])[0]

        if not post:
            return "Post not found", 404

        image_url = None
        if "featuredImage" in post.get("fields", {}):
            image_id = post["fields"]["featuredImage"]["sys"]["id"]
            asset = next((a for a in data.get("includes", {}).get("Asset", []) if a["sys"]["id"] == image_id), None)
            if asset:
                image_url = asset["fields"]["file"]["url"]

        body_content = post["fields"].get("content")
        print(body_content)

        rich_text_content = render_rich_text(body_content) if body_content else ""

        return render_template("blog_post.html",
                               post=post["fields"],
                               image_url=image_url,
                               rich_text_content=rich_text_content)

    except Exception as e:
        logging.exception("Error in blog_post route")
        return "Internal Server Error", 500


# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
