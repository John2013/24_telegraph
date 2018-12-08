import json
from datetime import date
from os.path import exists

import bleach
from bleach_whitelist import markdown_tags, markdown_attrs
from flask import Flask, render_template, request, redirect
from markdown import markdown

app = Flask(__name__)


def format_date(value):
    return value.strftime('%d.%m.%Y')


def get_article_file_path_and_slug(header):
    article_number = 1
    current_date = date.today()
    slug = '{}-{}-{}-{}'.format(
        header,
        current_date.month,
        current_date.day,
        article_number
    )
    file_path = 'articles/{}.json'.format(slug)
    while exists(file_path):
        article_number += 1
        slug = '{}-{}-{}-{}'.format(
            header,
            current_date.month,
            current_date.day,
            article_number
        )
        file_path = 'articles/{}.json'.format(slug)
    return file_path, slug


def get_article(slug):
    file_path = 'articles/{}.json'.format(slug)
    if not exists(file_path):
        return False

    with open(file_path, 'r', encoding="utf-8") as file:
        header, signature, body, ordinal_date = json.load(file)
    return {
        'header': header,
        'signature': signature,
        'body': body,
        'date': date.fromordinal(ordinal_date)
    }


@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        cur_date = date.today()
        article = [
            request.form['header'],
            request.form['signature'],
            request.form['body'],
            cur_date.toordinal()
        ]
        file_path, slug = get_article_file_path_and_slug(
            request.form['header']
        )
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(article, file, ensure_ascii=False)
        return redirect('/{}'.format(slug))

    return render_template('form.html')


@app.route('/<string:slug>')
def article_page(slug):
    article = get_article(slug)
    if article is False:
        return render_template('404.html'), 404

    article['body'] = bleach.clean(
        markdown(article['body']),
        markdown_tags,
        markdown_attrs
    )

    return render_template('article.html', article=article)


app.jinja_env.filters['date'] = format_date

if __name__ == "__main__":
    app.run()
