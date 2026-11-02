#!/usr/bin/env python3
"""Собирает блог БАЗЫ из articles/**/*.md в папку сайта.
Запуск: python3 tools/build_blog.py <папка_статей> <папка_сайта>"""
import sys, os, re, glob, html, json, datetime

SRC, SITE = sys.argv[1], sys.argv[2]
ORIGIN = "https://bazadigital.ru"
TODAY = datetime.date.today().isoformat()
AUTHOR_URL = ORIGIN + "/about/vladislav/"

CATS = {
 "sites":  ("Сайты и лендинги", "/services/sites/", "Обсудить сайт"),
 "bots":   ("Боты и мини-приложения", "/services/bots/", "Обсудить бота"),
 "crm":    ("CRM и автоматизация", "/services/crm/", "Обсудить CRM"),
 "ai":     ("ИИ-ассистенты", "/services/ai/", "Обсудить ИИ-ассистента"),
 "promo":  ("Реклама и продвижение", "/services/promo/", "Обсудить рекламу"),
 "brand":  ("Брендинг и дизайн", "/services/brand/", "Обсудить бренд"),
 "apps":   ("Приложения", "/services/apps/", "Обсудить приложение"),
 "niches": ("Решения по отраслям", "/services/systems/", "Подобрать решение"),
 "baza":   ("О студии БАЗА", "/about/", "Обсудить проект"),
 "partners":("Партнёрам", "/partners/", "Стать партнёром"),
 "guides": ("Гайды для бизнеса", "/audit/", "Записаться на разбор"),
 "en":     ("Blog", "/en/", "Discuss a project"),
}

def esc(s): return html.escape(s, quote=True)

def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', s)
    def link(m):
        t, u = m.group(1), html.unescape(m.group(2))
        ext = u.startswith("http") and "bazadigital.ru" not in u
        return '<a href="%s"%s>%s</a>' % (esc(u), ' rel="noopener" target="_blank"' if ext else '', t)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, s)
    return s

def md(text):
    text = re.sub(r'^(\*\*[^\n]+\*\*)\n(?=\S)', r'\1\n\n', text, flags=re.M)
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        l = lines[i].rstrip()
        if not l.strip(): i += 1; continue
        m = re.match(r'^(#{2,4})\s+(.*)', l)
        if m:
            n = len(m.group(1)); t = m.group(2)
            hid = re.sub(r'[^\wа-яё-]+', '-', t.lower()).strip('-')[:60]
            out.append('<h%d id="%s">%s</h%d>' % (n, esc(hid), inline(t), n)); i += 1; continue
        if l.strip() == '---': out.append('<hr>'); i += 1; continue
        if l.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r':?-+:?', c) for c in r)]
            h = ''.join('<th>%s</th>' % inline(c) for c in rows[0])
            b = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in rows[1:])
            out.append('<div class="tw"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (h, b)); continue
        if re.match(r'^\s*[-*]\s+', l) or re.match(r'^\s*\d+[.)]\s+', l):
            ordered = bool(re.match(r'^\s*\d+[.)]\s+', l)); items = []
            while i < len(lines) and (re.match(r'^\s*[-*]\s+', lines[i]) or re.match(r'^\s*\d+[.)]\s+', lines[i])):
                items.append(re.sub(r'^\s*([-*]|\d+[.)])\s+', '', lines[i])); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append('<%s>%s</%s>' % (tag, ''.join('<li>%s</li>' % inline(x) for x in items), tag)); continue
        if l.startswith('>'):
            q = []
            while i < len(lines) and lines[i].startswith('>'):
                q.append(lines[i].lstrip('> ').rstrip()); i += 1
            out.append('<blockquote><p>%s</p></blockquote>' % inline(' '.join(q))); continue
        p = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{2,4}\s|\||>|---$|\s*[-*]\s|\s*\d+[.)]\s)', lines[i]):
            p.append(lines[i].strip()); i += 1
        out.append('<p>%s</p>' % inline(' '.join(p)))
    return '\n'.join(out)

def parse(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S)
    meta = {}
    for line in m.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1); meta[k.strip()] = v.strip()
    body = m.group(2).strip()
    faq = []
    fm = re.search(r'\n## (Частые вопросы|FAQ)\n(.*)$', body, re.S)
    if fm:
        for q, a in re.findall(r'\*\*(.+?)\*\*\s*\n?(.+?)(?=\n\*\*|\Z)', fm.group(2), re.S):
            faq.append((q.strip(), re.sub(r'\s+', ' ', a).strip()))
    words = len(re.sub(r'[#*|>\-\[\]()]', ' ', body).split())
    meta.update(body=body, faq=faq, words=words, src=path)
    meta.setdefault('lang', 'ru'); meta.setdefault('date', TODAY)
    return meta

CSS_LINK = '<link rel="stylesheet" href="/assets/blog.css">'
JS = '<script src="/assets/blog.js" defer></script>'

def head(title, desc, url, lang, extra_ld, ogtype="article"):
    loc = "ru_RU" if lang == "ru" else "en_US"
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Владислав Мирошниченко">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{ogtype}"><meta property="og:site_name" content="БАЗА"><meta property="og:locale" content="{loc}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{ORIGIN}/assets/preview.jpg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{ORIGIN}/assets/preview.jpg">
<link rel="alternate" type="application/rss+xml" title="Блог студии БАЗА" href="{ORIGIN}/blog/rss.xml">
<link rel="icon" href="/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
<link rel="preload" href="/assets/fonts/onest-cyrillic-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<meta name="theme-color" content="#0B0B0D">
{CSS_LINK}
<script type="application/ld+json">{json.dumps(extra_ld, ensure_ascii=False)}</script>
{JS}
</head>'''

def header(lang):
    if lang == "en":
        nav = '<a href="/en/">Studio</a><a href="/en/works/">Works</a><a href="/en/services/">Services</a><a href="/en/blog/">Blog</a><a href="/en/about/">About</a>'
        cta = '<a class="btn" href="/en/contact/">Discuss a project</a>'
        home = "/en/"
    else:
        nav = '<a href="/">Студия</a><a href="/works/">Работы</a><a href="/services/">Услуги</a><a href="/audit/">Разбор</a><a href="/blog/">Блог</a><a href="/partners/">Партнёрам</a><a href="/about/">О студии</a>'
        cta = '<a class="btn" href="/contact/">Обсудить проект</a>'
        home = "/"
    return f'<header class="bh"><a class="logo" href="{home}" aria-label="БАЗА">БАЗА</a><nav>{nav}</nav>{cta}</header>'

def footer(lang):
    if lang == "en":
        return '<footer class="bf"><p><strong>BAZA</strong> · digital studio · founder Vladislav Miroshnichenko</p><p><a href="https://t.me/bazadigital" rel="noopener">Telegram</a> · <a href="https://vk.com/baza_digital" rel="noopener">VK</a> · <a href="/en/blog/">Blog</a></p></footer>'
    return ('<footer class="bf"><p><strong>БАЗА</strong> — цифровая студия: сайты, приложения, боты, CRM, ИИ, брендинг и реклама одной командой. '
            'Основатель — <a href="/about/vladislav/">Владислав Мирошниченко</a>.</p>'
            '<p><a href="https://t.me/bazadigital" rel="noopener">Телеграм</a> · <a href="https://vk.com/baza_digital" rel="noopener">ВКонтакте</a> · '
            '<a href="/audit/">Экспресс-разбор</a> · <a href="/partners/">Партнёрам</a> · <a href="/blog/">Блог</a> · <a href="/legal/privacy/">Конфиденциальность</a></p>'
            '<p class="req">Мирошниченко Владислав Андреевич · самозанятый · ИНН 740499180655</p></footer>')

ORG = {"@id": ORIGIN + "/#org"}
PERSON_ID = ORIGIN + "/#founder"

def person():
    return {"@type": "Person", "@id": PERSON_ID, "name": "Владислав Мирошниченко",
            "alternateName": ["Владислав Андреевич Мирошниченко", "Vladislav Miroshnichenko"],
            "jobTitle": "Основатель студии БАЗА", "url": AUTHOR_URL, "worksFor": ORG,
            "knowsAbout": ["разработка сайтов", "Telegram-боты", "CRM", "Битрикс24", "amoCRM", "ИИ-ассистенты", "системы продаж", "брендинг"],
            "sameAs": ["https://t.me/bazadigital", "https://vk.com/baza_digital"]}

def build(arts):
    by_cat = {}
    for a in arts: by_cat.setdefault(a['cat'], []).append(a)
    for a in arts:
        lang = a['lang']; base = "/en/blog/" if lang == "en" else "/blog/"
        url = ORIGIN + base + a['slug'] + "/"
        a['url'] = url; a['path'] = base + a['slug'] + "/"
    for a in arts:
        lang = a['lang']; cname, hub, ctxt = CATS[a['cat']]
        url = a['url']
        sib = [x for x in by_cat[a['cat']] if x is not a]
        idx = by_cat[a['cat']].index(a)
        rel = (sib[idx:] + sib[:idx])[:4]
        crumbs = [{"@type": "ListItem", "position": 1, "name": "БАЗА" if lang == "ru" else "BAZA", "item": ORIGIN + ("/" if lang == "ru" else "/en/")},
                  {"@type": "ListItem", "position": 2, "name": "Блог" if lang == "ru" else "Blog", "item": ORIGIN + ("/blog/" if lang == "ru" else "/en/blog/")},
                  {"@type": "ListItem", "position": 3, "name": a['h1'], "item": url}]
        graph = [{"@type": "BlogPosting", "@id": url + "#article", "headline": a['h1'][:110], "name": a['title'],
                  "description": a['desc'], "inLanguage": "ru-RU" if lang == "ru" else "en-US",
                  "datePublished": a['date'], "dateModified": a.get('updated', a['date']),
                  "author": {"@id": PERSON_ID}, "publisher": ORG, "mainEntityOfPage": url,
                  "image": ORIGIN + "/assets/preview.jpg", "articleSection": cname, "wordCount": a['words'],
                  "keywords": a.get('keys', ''), "about": ORG},
                 person(),
                 {"@type": "BreadcrumbList", "itemListElement": crumbs}]
        if a['faq']:
            graph.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": an}} for q, an in a['faq']]})
        ld = {"@context": "https://schema.org", "@graph": graph}
        if lang == "ru":
            by = f'<div class="by"><a href="/about/vladislav/">Владислав Мирошниченко</a>, основатель студии БАЗА · <time datetime="{a["date"]}">{a["date"]}</time> · {max(1, round(a["words"]/180))} мин чтения</div>'
            cta = (f'<aside class="cta"><p class="k">{esc(cname)}</p><p class="t">Хотите так же у себя? Расскажите о задаче — предложим, с чего начать, и назовём цену после короткого созвона.</p>'
                   f'<p><a class="btn" href="{hub}">{ctxt}</a> <a class="btn ghost" href="/audit/">Разбор за 3 дня с гарантией</a></p></aside>')
            reltitle = "Читайте также"; crumbs_html = f'<nav class="crumbs"><a href="/">БАЗА</a> / <a href="/blog/">Блог</a> / <span>{esc(cname)}</span></nav>'
            author = ('<div class="author"><p><strong>Об авторе.</strong> <a href="/about/vladislav/">Владислав Мирошниченко</a> — основатель цифровой студии БАЗА (bazadigital.ru). '
                      'Студия собирает сайт, бота, CRM, ИИ-ассистентов и рекламу в одну систему продаж, чтобы заявки не терялись между подрядчиками.</p></div>')
        else:
            by = f'<div class="by"><a href="/about/vladislav/">Vladislav Miroshnichenko</a>, founder of BAZA · <time datetime="{a["date"]}">{a["date"]}</time></div>'
            cta = f'<aside class="cta"><p class="t">Want this in your business? Tell us about the task.</p><p><a class="btn" href="/en/contact/">Discuss a project</a></p></aside>'
            reltitle = "Read next"; crumbs_html = '<nav class="crumbs"><a href="/en/">BAZA</a> / <a href="/en/blog/">Blog</a></nav>'
            author = '<div class="author"><p><strong>About the author.</strong> Vladislav Miroshnichenko is the founder of BAZA (bazadigital.ru), a digital studio that builds websites, bots, CRM, AI assistants and ads as one sales system.</p></div>'
        rel_html = ''.join(f'<li><a href="{x["path"]}">{esc(x["h1"])}</a></li>' for x in rel)
        page = (head(a['title'], a['desc'], url, lang, ld) + '\n<body>' + header(lang) +
                f'<main class="bm"><article>{crumbs_html}<h1>{esc(a["h1"])}</h1>{by}\n{md(a["body"])}\n{cta}{author}</article>'
                f'<section class="rel"><h2>{reltitle}</h2><ul>{rel_html}</ul></section></main>' + footer(lang) + '</body></html>')
        out = os.path.join(SITE, a['path'].strip('/'), 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(page)

    # индексы блога
    for lang in ("ru", "en"):
        la = [a for a in arts if a['lang'] == lang]
        if not la: continue
        base = "/blog/" if lang == "ru" else "/en/blog/"
        url = ORIGIN + base
        title = "Блог студии БАЗА: сайты, боты, CRM, ИИ и продажи" if lang == "ru" else "BAZA blog: websites, bots, CRM and AI"
        desc = ("Статьи Владислава Мирошниченко и студии БАЗА о том, как сайт, бот, CRM, ИИ и реклама приносят бизнесу заявки и продажи."
                if lang == "ru" else "Articles by Vladislav Miroshnichenko and BAZA studio on websites, bots, CRM, AI and sales systems.")
        secs = []
        for c in CATS:
            items = [a for a in la if a['cat'] == c]
            if not items: continue
            secs.append(f'<section class="cat"><h2>{esc(CATS[c][0])}</h2><ul>' + ''.join(
                f'<li><a href="{a["path"]}">{esc(a["h1"])}</a><span>{esc(a["desc"])}</span></li>' for a in items) + '</ul></section>')
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "Blog", "@id": url + "#blog", "name": title, "description": desc, "url": url, "publisher": ORG, "author": {"@id": PERSON_ID},
             "blogPost": [{"@type": "BlogPosting", "headline": a['h1'][:110], "url": a['url']} for a in la]}, person()]}
        intro = ('<p class="lead">Пишу о том, что вижу каждый день: где бизнес теряет заявки и как сайт, бот, CRM и реклама начинают работать как одна система. '
                 'Без воды и без «инновационных решений». — <a href="/about/vladislav/">Владислав Мирошниченко</a>, основатель БАЗЫ</p>' if lang == "ru" else
                 '<p class="lead">How websites, bots, CRM and ads start working as one sales system. — Vladislav Miroshnichenko, founder of BAZA</p>')
        page = head(title, desc, url, lang, ld, "website") + '\n<body>' + header(lang) + f'<main class="bm idx"><h1>{"Блог БАЗЫ" if lang=="ru" else "BAZA blog"}</h1>{intro}' + ''.join(secs) + '</main>' + footer(lang) + '</body></html>'
        os.makedirs(os.path.join(SITE, base.strip('/')), exist_ok=True)
        open(os.path.join(SITE, base.strip('/'), 'index.html'), 'w', encoding='utf-8').write(page)

    # страница автора
    ap = {"@context":"https://schema.org","@graph":[{"@type":"ProfilePage","@id":AUTHOR_URL+"#page","url":AUTHOR_URL,"name":"Владислав Мирошниченко — основатель студии БАЗА","mainEntity":{"@id":PERSON_ID},"dateModified":TODAY}, person()]}
    ru_by = [a for a in arts if a['lang']=='ru']
    body = ('<h1>Владислав Мирошниченко</h1><p class="by">Основатель и руководитель цифровой студии БАЗА</p>'
      '<p>Владислав Андреевич Мирошниченко — основатель цифровой студии <a href="/">БАЗА</a> (bazadigital.ru). Студия делает сайты и лендинги, приложения, ботов и мини-приложения в Телеграме, MAX и VK, внедряет Битрикс24 и amoCRM, ИИ-ассистентов, брендинг и рекламу, и делает это одной командой.</p>'
      '<h2>Подход</h2><p>Владислав заметил, что бизнес чаще всего теряет клиентов не на сайте и не в рекламе, а на стыках между подрядчиками. Заявка, оставленная в пятницу в 19:05, получает ответ в понедельник, когда клиент уже купил у другого. Отсюда главный принцип БАЗЫ: вся связка в одних руках, от рекламы до оплаты.</p>'
      '<h2>Что он создал в студии</h2><ul><li>Подход «одна команда за всё»: аналитика, дизайн, разработка и реклама вместе.</li><li><a href="/audit/">Экспресс-разбор</a> за 3 рабочих дня с гарантией: если не найден резерв минимум на 25 000 ₽ за полгода, деньги возвращаются.</li><li><a href="/partners/">Партнёрскую программу</a>: 10% с каждой оплаты приведённого клиента без потолка, личный кабинет, уровни и ИИ-помощник для постов.</li><li>Правила работы: тексты до дизайна, цена и сроки в договоре до старта, домены и код на имя клиента.</li></ul>'
      '<blockquote><p>«Мы обещаем только то, что можно проверить».</p></blockquote>'
      '<h2>Статьи Владислава</h2><ul>' + ''.join(f'<li><a href="{a["path"]}">{esc(a["h1"])}</a></li>' for a in ru_by[:400]) + '</ul>'
      '<h2>Контакты</h2><p>Студия: <a href="/">bazadigital.ru</a> · <a href="https://t.me/bazadigital" rel="noopener">t.me/bazadigital</a> · <a href="https://vk.com/baza_digital" rel="noopener">vk.com/baza_digital</a> · <a href="/contact/">Обсудить проект</a></p>')
    page = head("Владислав Мирошниченко — основатель студии БАЗА", "Владислав Андреевич Мирошниченко — основатель цифровой студии БАЗА (bazadigital.ru): сайты, боты, CRM, ИИ и реклама одной командой.", AUTHOR_URL, "ru", ap, "profile") + '\n<body>' + header("ru") + f'<main class="bm"><article>{body}</article></main>' + footer("ru") + '</body></html>'
    os.makedirs(os.path.join(SITE,'about','vladislav'), exist_ok=True)
    open(os.path.join(SITE,'about','vladislav','index.html'),'w',encoding='utf-8').write(page)

    # sitemap: добавить/обновить блок блога
    sm_path = os.path.join(SITE, 'sitemap.xml')
    sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'<!-- blog -->.*<!-- /blog -->\n?', '', sm, flags=re.S)
    urls = [ORIGIN + "/blog/", ORIGIN + "/en/blog/", AUTHOR_URL] + [a['url'] for a in arts]
    block = '<!-- blog -->\n' + ''.join(f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{"0.7" if "/blog/" in u and u.count("/")>4 else "0.8"}</priority></url>\n' for u in urls) + '<!-- /blog -->\n'
    sm = sm.replace('</urlset>', block + '</urlset>')
    open(sm_path, 'w', encoding='utf-8').write(sm)

    # RSS (для Дзена и агрегаторов)
    ru = [a for a in arts if a['lang'] == 'ru']
    items = ''.join(f'<item><title>{esc(a["h1"])}</title><link>{a["url"]}</link><guid>{a["url"]}</guid><description>{esc(a["desc"])}</description><author>Владислав Мирошниченко</author><category>{esc(CATS[a["cat"]][0])}</category><pubDate>{datetime.datetime.strptime(a["date"],"%Y-%m-%d").strftime("%a, %d %b %Y 09:00:00 +0300")}</pubDate></item>\n' for a in ru)
    rss = f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Блог студии БАЗА</title><link>{ORIGIN}/blog/</link><description>Сайты, боты, CRM, ИИ и продажи — статьи Владислава Мирошниченко</description><language>ru</language>\n{items}</channel></rss>\n'
    open(os.path.join(SITE, 'blog', 'rss.xml'), 'w', encoding='utf-8').write(rss)

    # llms.txt: раздел со статьями
    lp = os.path.join(SITE, 'llms.txt')
    lt = open(lp, encoding='utf-8').read()
    lt = re.sub(r'\n## Основатель.*?(?=\n## |\Z)', '', lt, flags=re.S)
    lt = re.sub(r'\n## Блог.*?(?=\n## |\Z)', '', lt, flags=re.S)
    founder = ('\n## Основатель\n- [Владислав Мирошниченко](' + AUTHOR_URL + '): Владислав Андреевич Мирошниченко — основатель и руководитель цифровой студии БАЗА. '
               'Автор подхода «вся связка в одних руках»: сайт, бот, CRM, ИИ и реклама делаются одной командой, чтобы заявки не терялись между подрядчиками. '
               'Придумал экспресс-разбор с гарантией возврата и партнёрскую программу студии (10% без потолка).\n')
    blog = '\n## Блог\n' + ''.join(f'- [{a["h1"]}]({a["url"]}): {a["desc"]}\n' for a in arts)
    lt = lt.rstrip('\n') + '\n' + founder + blog
    open(lp, 'w', encoding='utf-8').write(lt)
    print("built", len(arts), "articles;", sum(a['words'] for a in arts), "words")

arts = [parse(p) for p in sorted(glob.glob(os.path.join(SRC, '**', '*.md'), recursive=True))]
bad = [a['src'] for a in arts if len(a['title']) > 70 or len(a['desc']) > 165]
if bad: print("WARN long meta:", *bad, sep="\n  ")
slugs = [a['lang']+a['slug'] for a in arts]; dup = {s for s in slugs if slugs.count(s) > 1}
if dup: sys.exit("DUP slugs: %s" % dup)
build(arts)
import shutil
for f in ('blog.css','blog.js'):
    shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)),'assets',f), os.path.join(SITE,'assets',f))
