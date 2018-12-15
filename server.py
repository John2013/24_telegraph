import json
import uuid
from datetime import date
from json import JSONDecodeError
from os import makedirs
from os.path import exists
from re import sub, compile

import bleach
from bleach_whitelist import markdown_tags, markdown_attrs
from flask import Flask, render_template, request, redirect, make_response, \
    abort
from markdown import markdown

app = Flask(__name__)


def format_date(date_value):
    return date_value.strftime('%d.%m.%Y')


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
        header, signature, body, ordinal_date, article_id = json.load(file)
    return {
        'header': header,
        'signature': signature,
        'body': body,
        'date': date.fromordinal(ordinal_date),
        'id': article_id
    }


def article_as_list(article_dict):
    return [
        article_dict['header'],
        article_dict['signature'],
        article_dict['body'],
        article_dict['date'].toordinal(),
        article_dict['id']
    ]


def clear_article_header(header):
    re = compile(r"[\\/*+.,`~\r\n\t\f\v<>!@#$%^&=?'\"|]+")
    return sub(re, '_', header)


@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        cur_date = date.today()
        article_id = str(uuid.uuid4())
        article = [
            clear_article_header(request.form['header']),
            request.form['signature'],
            request.form['body'],
            cur_date.toordinal(),
            article_id
        ]
        slug = save_article(article)

        article_ids = json.loads(request.cookies.get('articles') or "[]")

        article_ids.append(article_id)
        responce = make_response(redirect('/{}'.format(slug)))
        responce.set_cookie('articles', json.dumps(article_ids))
        return responce

    return render_template('form-create.html')


def save_article(article, slug=None):
    if not exists('./articles'):
        makedirs('./articles')
    if not slug:
        header_key = 0
        file_path, slug = get_article_file_path_and_slug(
            article[header_key]
        )
    else:
        file_path = './articles/{}.json'.format(slug)

    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False)

    return slug


@app.route('/<string:slug>')
def article_page(slug):
    article = get_article(slug)

    if article is False:
        not_found_code = 404
        return abort(not_found_code)

    article['body'] = bleach.clean(
        markdown(article['body']),
        markdown_tags,
        markdown_attrs
    )

    try:
        user_article_ids = json.loads(request.cookies.get('articles'))
    except TypeError:
        user_article_ids = []
    except JSONDecodeError:
        user_article_ids = []

    if article['id'] in user_article_ids:
        return render_template('article-edit.html', article=article, slug=slug)

    return render_template('article.html', article=article)


@app.route('/edit/<string:slug>', methods=['GET', 'POST'])
def edit_page(slug):
    article = get_article(slug)

    try:
        user_article_ids = json.loads(request.cookies.get('articles'))
    except TypeError:
        user_article_ids = []
    except JSONDecodeError:
        user_article_ids = []

    if article['id'] not in user_article_ids:
        access_denied_code = 403
        return abort(access_denied_code)

    if request.method == 'POST':
        article['body'] = request.form['body']
        list_article = article_as_list(article)
        save_article(list_article, slug)
        return redirect("/{}".format(slug))

    return render_template('form-change.html', article=article)


app.jinja_env.filters['date'] = format_date

if __name__ == "__main__":
    app.run()
