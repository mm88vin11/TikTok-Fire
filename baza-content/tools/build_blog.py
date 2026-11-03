#!/usr/bin/env python3
"""Блог студии БАЗА: собирает articles/**/*.md в страницы сайта.
Запуск: python3 tools/build_blog.py <папка_статей> <папка_сайта>"""
import sys, os, re, glob, html, json, datetime, hashlib, shutil

SRC, SITE = sys.argv[1], sys.argv[2]
ORIGIN = "https://bazadigital.ru"
TODAY = datetime.date.today().isoformat()
AUTHOR_URL = ORIGIN + "/about/vladislav/"
PERSON_ID = ORIGIN + "/#founder"
ORG = {"@id": ORIGIN + "/#org"}
HERE = os.path.dirname(os.path.abspath(__file__))

# категория: название, хаб услуги, текст кнопки, оттенок, 3D-объекты
CATS = {
 "baza":     ("О студии БАЗА", "/about/", "Обсудить проект", "#EDEDF2", ["gem2", "brick3", "ring2"]),
 "compare":  ("Сравнения", "/contact/", "Обсудить проект", "#F3F7E6", ["brick3", "gem2", "ball"]),
 "sites":    ("Сайты и лендинги", "/services/sites/", "Обсудить сайт", "#EEF0FF", ["site", "show-sites"]),
 "bots":     ("Боты и мини-приложения", "/services/bots/", "Обсудить бота", "#F3F0FF", ["bot", "show-bots"]),
 "crm":      ("CRM и автоматизация", "/services/crm/", "Обсудить CRM", "#F1F1F4", ["crm", "show-crm", "gear"]),
 "ai":       ("ИИ-ассистенты", "/services/ai/", "Обсудить ИИ-ассистента", "#EEF3FF", ["ai", "show-ai"]),
 "promo":    ("Реклама и продвижение", "/services/promo/", "Обсудить рекламу", "#F4F8E8", ["growth", "show-promo"]),
 "brand":    ("Брендинг и дизайн", "/services/brand/", "Обсудить бренд", "#FFF2EC", ["brand", "show-brand"]),
 "apps":     ("Приложения", "/services/apps/", "Обсудить приложение", "#EEF0FF", ["app", "show-apps"]),
 "niches":   ("Решения по отраслям", "/services/systems/", "Подобрать решение", "#F3F7E6", ["brick3", "gear", "capsule", "show-crm", "show-bots"]),
 "partners": ("Партнёрам", "/partners/", "Стать партнёром", "#F3F0FF", ["capsule", "ring2", "gem2"]),
 "guides":   ("Гайды для бизнеса", "/audit/", "Записаться на разбор", "#F1F1F4", ["gear", "capsule2", "brick4"]),
 "en":       ("Blog", "/en/contact/", "Discuss a project", "#EEF0FF", ["ball", "gem2", "ai"]),
}
CAT_ICON = {"baza": "lg-badge2", "compare": "brick3", "sites": "site", "bots": "bot", "crm": "crm", "ai": "ai", "promo": "growth",
            "brand": "brand", "apps": "app", "niches": "gear", "partners": "capsule", "guides": "gear", "en": "ball"}
MONTHS = "января февраля марта апреля мая июня июля августа сентября октября ноября декабря".split()

def esc(s): return html.escape(s, quote=True)
def ru_date(d):
    y, m, dd = map(int, d.split('-')); return f"{dd} {MONTHS[m-1]} {y}"
def pick(lst, key): return lst[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(lst)]
def img(name): return f"/assets/img/{name}.webp"

def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', s)
    def link(m):
        t, u = m.group(1), html.unescape(m.group(2))
        ext = u.startswith("http") and "bazadigital.ru" not in u
        return '<a href="%s"%s>%s</a>' % (esc(u), ' rel="noopener" target="_blank"' if ext else '', t)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, s)

def slugify(t): return re.sub(r'[^\wа-яё-]+', '-', t.lower()).strip('-')[:60]

def table(rows):
    head = rows[0]
    us = [i for i, c in enumerate(head) if re.search(r'БАЗА|BAZA', c)]
    def cell(tag, c, i):
        cls = ' class="us"' if i in us else ''
        return f'<{tag}{cls}>{inline(c)}</{tag}>'
    h = ''.join(cell('th', c, i) for i, c in enumerate(head))
    b = ''.join('<tr>' + ''.join(cell('td', c, i) for i, c in enumerate(r)) + '</tr>' for r in rows[1:])
    return f'<div class="tw"><table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

def md(text, h2num=True, promo=None):
    text = re.sub(r'^(\*\*[^\n]+\*\*)\n(?=\S)', r'\1\n\n', text, flags=re.M)
    out, lines, i, n2 = [], text.split("\n"), 0, 0
    total_h2 = len(re.findall(r'^## ', text, re.M))
    while i < len(lines):
        l = lines[i].rstrip()
        if not l.strip(): i += 1; continue
        m = re.match(r'^(#{2,4})\s+(.*)', l)
        if m:
            lvl = len(m.group(1)); t = m.group(2)
            if lvl == 2:
                n2 += 1
                if promo and n2 == max(2, total_h2 // 2 + 1) and total_h2 >= 2:
                    out.append(promo); promo = None
                num = f'<span class="n">{n2:02d}</span>' if h2num else ''
                out.append(f'<h2 id="{esc(slugify(t))}">{num}{inline(t)}</h2>')
            else:
                out.append(f'<h{lvl}>{inline(t)}</h{lvl}>')
            i += 1; continue
        if l.strip() == '---': out.append('<hr>'); i += 1; continue
        if l.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r':?-+:?', c) for c in r)]
            out.append(table(rows)); continue
        if re.match(r'^\s*[-*]\s+', l) or re.match(r'^\s*\d+[.)]\s+', l):
            ordered = bool(re.match(r'^\s*\d+[.)]\s+', l)); items = []
            while i < len(lines) and (re.match(r'^\s*[-*]\s+', lines[i]) or re.match(r'^\s*\d+[.)]\s+', lines[i])):
                items.append(re.sub(r'^\s*([-*]|\d+[.)])\s+', '', lines[i])); i += 1
            tag = 'ol' if ordered else 'ul'
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if l.startswith('>'):
            q = []
            while i < len(lines) and lines[i].startswith('>'):
                q.append(lines[i].lstrip('> ').rstrip()); i += 1
            out.append(f'<blockquote><p>{inline(" ".join(q))}</p></blockquote>'); continue
        p = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{2,4}\s|\||>|---$|\s*[-*]\s|\s*\d+[.)]\s)', lines[i]):
            p.append(lines[i].strip()); i += 1
        out.append(f'<p>{inline(" ".join(p))}</p>')
    if promo: out.append(promo)
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
    fm = re.search(r'\n## (Частые вопросы|FAQ)\n(.*?)(?=\n## |\Z)', body, re.S)
    if fm:
        for q, a in re.findall(r'\*\*(.+?)\*\*\s*\n?(.+?)(?=\n\*\*|\Z)', fm.group(2), re.S):
            faq.append((q.strip(), re.sub(r'\s+', ' ', a).strip()))
        body = (body[:fm.start()] + body[fm.end():]).strip()
    paras = body.split('\n\n', 1)
    lead = paras[0].strip() if not paras[0].startswith(('#', '|', '-', '>')) else ''
    rest = paras[1] if lead and len(paras) > 1 else (body if not lead else '')
    words = len(re.sub(r'[#*|>\[\]()]', ' ', raw.split('---', 2)[2]).split())
    h2 = re.findall(r'^## (.+)$', rest, re.M)
    meta.update(lead=lead, rest=rest, faq=faq, words=words, h2=h2, src=path)
    meta.setdefault('lang', 'ru'); meta.setdefault('date', TODAY)
    meta['minutes'] = max(2, round(words / 170))
    return meta

def person():
    return {"@type": "Person", "@id": PERSON_ID, "name": "Владислав Мирошниченко",
            "alternateName": ["Владислав Андреевич Мирошниченко", "Vladislav Miroshnichenko"],
            "jobTitle": "Основатель студии БАЗА", "url": AUTHOR_URL, "worksFor": ORG, "image": ORIGIN + "/assets/img/lg-badge.webp",
            "knowsAbout": ["разработка сайтов", "Telegram-боты", "CRM", "Битрикс24", "amoCRM", "ИИ-ассистенты", "системы продаж", "брендинг", "digital-маркетинг"],
            "sameAs": ["https://t.me/bazadigital", "https://vk.com/baza_digital"]}

FONTS = '<link rel="preload" href="/assets/fonts/onest-cyrillic-600-normal.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="/assets/fonts/onest-cyrillic-400-normal.woff2" as="font" type="font/woff2" crossorigin>'

def head(title, desc, url, lang, ld, ogimg, ogtype="article", extra=""):
    loc = "ru_RU" if lang == "ru" else "en_US"
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Владислав Мирошниченко">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{ogtype}"><meta property="og:site_name" content="БАЗА"><meta property="og:locale" content="{loc}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{ogimg}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(title)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{ogimg}">
{extra}<link rel="alternate" type="application/rss+xml" title="Блог студии БАЗА" href="{ORIGIN}/blog/rss.xml">
<link rel="icon" href="/favicon.png" type="image/png"><link rel="apple-touch-icon" href="/assets/icon-180.png">
{FONTS}
<meta name="theme-color" content="#ffffff">
<link rel="stylesheet" href="/assets/blog.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<script src="/assets/blog.js" defer></script>
</head>'''

def header(lang, active="blog"):
    if lang == "en":
        links = [("/en/", "Studio"), ("/en/works/", "Works"), ("/en/services/", "Services"), ("/en/blog/", "Blog"), ("/en/about/", "About")]
        cta = ("/en/contact/", "Discuss a project"); home = "/en/"
    else:
        links = [("/", "Студия"), ("/works/", "Работы"), ("/services/", "Услуги"), ("/audit/", "Разбор"), ("/blog/", "Блог"), ("/partners/", "Партнёрам"), ("/about/", "О студии")]
        cta = ("/contact/", "Обсудить проект"); home = "/"
    nav = ''.join(f'<a href="{u}"{" class=on" if "blog" in u else ""}>{t}</a>' for u, t in links)
    return (f'<div class="prog" aria-hidden="true"><i></i></div><header class="top"><a class="logo" href="{home}" aria-label="БАЗА — на главную">'
            f'<img src="/assets/img/lg-mark.webp" alt="" width="34" height="24"><span>БАЗА</span></a>'
            f'<nav class="pill" aria-label="Разделы">{nav}</nav><a class="btn dark" href="{cta[0]}">{cta[1]}<span class="spark">✳</span></a></header>')

def footer(lang):
    if lang == "en":
        return ('<footer class="foot"><div class="fin"><p class="big">Ready when you are.</p><p><a class="btn lime" href="/en/contact/">Discuss a project</a></p>'
                '<p class="mut">BAZA · digital studio · founder Vladislav Miroshnichenko · <a href="https://t.me/bazadigital" rel="noopener">Telegram</a> · <a href="/en/blog/">Blog</a></p></div></footer>')
    return ('<footer class="foot"><div class="fin">'
            '<div class="fcols"><div><img class="fmark" src="/assets/img/lg-badge.webp" alt="Это БАЗА" width="96" height="96" loading="lazy">'
            '<p class="mut">Цифровая студия: сайты, приложения, боты, CRM, ИИ, брендинг и реклама одной командой. Основатель — <a href="/about/vladislav/">Владислав Мирошниченко</a>.</p></div>'
            '<div><p class="h">Студия</p><a href="/works/">Работы</a><a href="/services/">Услуги</a><a href="/about/">О студии</a><a href="/blog/">Блог</a></div>'
            '<div><p class="h">Начать</p><a href="/audit/">Экспресс-разбор</a><a href="/build/">Подбор решения</a><a href="/contact/">Обсудить проект</a><a href="/partners/">Партнёрам</a></div>'
            '<div><p class="h">Мы в соцсетях</p><a href="https://t.me/bazadigital" rel="noopener">Телеграм</a><a href="https://vk.com/baza_digital" rel="noopener">ВКонтакте</a><a href="/blog/rss.xml">RSS блога</a></div></div>'
            '<p class="req">© 2026 БАЗА · <a href="/legal/privacy/">Конфиденциальность</a> · <a href="/legal/requisites/">Об исполнителе</a> · Мирошниченко Владислав Андреевич · самозанятый · ИНН 740499180655</p>'
            '</div></footer>')

def promo_card(a):
    if a['lang'] == 'en': return None
    if a['cat'] == 'partners':
        return ('<aside class="ins lilac"><img src="/assets/img/capsule.webp" alt="" loading="lazy" width="160" height="165"><div><p class="k">Партнёрская программа</p>'
                '<p class="t">10% с каждой оплаты клиента. Без потолка, с кабинетом и выплатами по кнопке.</p><a class="btn dark" href="/partners/">Получить ссылку и промокод</a></div></aside>')
    if pick([0, 1], a['slug']) == 0:
        return ('<aside class="ins"><img src="/assets/img/gem2.webp" alt="" loading="lazy" width="110" height="166"><div><p class="k">Экспресс-разбор</p>'
                '<p class="t">За 3 дня найдём, где уходят заявки и деньги. Не найдём от 25 000 ₽ за полгода — вернём оплату.</p><a class="btn dark" href="/audit/">Записаться на разбор</a></div></aside>')
    return ('<aside class="ins lime"><img src="/assets/img/brick3.webp" alt="" loading="lazy" width="160" height="151"><div><p class="k">Подбор решения</p>'
            '<p class="t">Три вопроса — и сразу видно, с чего начать именно вам: сайт, бот, CRM или реклама.</p><a class="btn dark" href="/build/">Подобрать за минуту</a></div></aside>')

def card(a, big=False):
    c = CATS[a['cat']]
    return (f'<a class="card{" big" if big else ""}" href="{a["path"]}"><span class="cv" style="--t:{c[3]}"><img src="{img(a["hero"])}" alt="" loading="lazy"></span>'
            f'<span class="cb"><span class="ck">{esc(c[0])}</span><span class="ct">{esc(a["h1"])}</span><span class="cd">{esc(a["desc"])}</span>'
            f'<span class="cm">{a["minutes"]} мин{" чтения" if a["lang"]=="ru" else " read"}</span></span></a>')

def build(arts):
    by_cat = {}
    for a in arts:
        base = "/en/blog/" if a['lang'] == "en" else "/blog/"
        a['path'] = base + a['slug'] + "/"; a['url'] = ORIGIN + a['path']
        a['hero'] = a.get('img') or pick(CATS[a['cat']][4], a['slug'])
        a['og'] = f"{ORIGIN}/assets/blog/og/{a['lang']}-{a['slug']}.jpg"
        by_cat.setdefault(a['cat'], []).append(a)
    os.makedirs(os.path.join(SITE, 'assets', 'blog'), exist_ok=True)
    json.dump([{k: a[k] for k in ('slug', 'lang', 'h1', 'cat', 'hero', 'minutes')} | {"catname": CATS[a['cat']][0], "tint": CATS[a['cat']][3]} for a in arts],
              open(os.path.join(HERE, 'og-list.json'), 'w', encoding='utf-8'), ensure_ascii=False)

    for a in arts:
        lang = a['lang']; cname, hub, ctxt, tint, _ = CATS[a['cat']]
        sib = [x for x in by_cat[a['cat']] if x is not a]
        idx = by_cat[a['cat']].index(a)
        rel = (sib[idx:] + sib[:idx])[:3]
        if lang == 'ru' and a['cat'] not in ('baza', 'compare'):
            extra = [x for x in by_cat.get('compare', []) + by_cat.get('baza', []) if x is not a]
            rel.append(pick(extra, a['slug']) if extra else None); rel = [r for r in rel if r]
        crumbs_ld = [{"@type": "ListItem", "position": 1, "name": "БАЗА", "item": ORIGIN + ("/" if lang == "ru" else "/en/")},
                     {"@type": "ListItem", "position": 2, "name": "Блог" if lang == "ru" else "Blog", "item": ORIGIN + ("/blog/" if lang == "ru" else "/en/blog/")},
                     {"@type": "ListItem", "position": 3, "name": a['h1'], "item": a['url']}]
        graph = [{"@type": "BlogPosting", "@id": a['url'] + "#article", "headline": a['h1'][:110], "name": a['title'],
                  "description": a['desc'], "inLanguage": "ru-RU" if lang == "ru" else "en-US",
                  "datePublished": a['date'], "dateModified": a.get('updated', TODAY),
                  "author": {"@id": PERSON_ID}, "publisher": ORG, "mainEntityOfPage": a['url'],
                  "image": [a['og'], ORIGIN + img(a['hero'])], "articleSection": cname, "wordCount": a['words'],
                  "timeRequired": f"PT{a['minutes']}M", "keywords": a.get('keys', ''), "about": ORG, "mentions": ORG,
                  "isPartOf": {"@type": "Blog", "@id": ORIGIN + ("/blog/" if lang == "ru" else "/en/blog/") + "#blog"}},
                 person(), {"@type": "BreadcrumbList", "itemListElement": crumbs_ld}]
        if a['faq']:
            graph.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": an}} for q, an in a['faq']]})
        ld = {"@context": "https://schema.org", "@graph": graph}
        ru = lang == 'ru'
        toc = ''.join(f'<li><a href="#{esc(slugify(h))}">{inline(h)}</a></li>' for h in a['h2'])
        if a['faq']: toc += f'<li><a href="#faq">{"Частые вопросы" if ru else "FAQ"}</a></li>'
        faq_html = ''
        if a['faq']:
            faq_html = (f'<section class="faq" id="faq"><h2>{"Частые вопросы" if ru else "FAQ"}</h2>' +
                        ''.join(f'<details><summary>{inline(q)}</summary><p>{inline(an)}</p></details>' for q, an in a['faq']) + '</section>')
        lead = f'<div class="lead"><span class="lk">{"Коротко" if ru else "In short"}</span><p>{inline(a["lead"])}</p></div>' if a['lead'] else ''
        body = md(a['rest'], promo=promo_card(a))
        author = (f'<div class="author"><img src="/assets/img/lg-badge.webp" alt="" width="64" height="64" loading="lazy"><div>'
                  f'<p class="an"><a href="/about/vladislav/">{"Владислав Мирошниченко" if ru else "Vladislav Miroshnichenko"}</a></p>'
                  f'<p class="ad">{"Основатель цифровой студии БАЗА. Собираю сайт, бота, CRM, ИИ и рекламу в одну систему продаж, чтобы заявки не терялись между подрядчиками." if ru else "Founder of BAZA digital studio. Builds websites, bots, CRM, AI and ads as one sales system."}</p></div></div>')
        hero = (f'<section class="hero" style="--t:{tint}"><div class="hl">'
                f'<nav class="crumbs"><a href="{"/" if ru else "/en/"}">БАЗА</a><span>/</span><a href="{"/blog/" if ru else "/en/blog/"}">{"Блог" if ru else "Blog"}</a></nav>'
                f'<a class="chip" href="{"/blog/#" + a["cat"] if ru else "/en/blog/"}"><img src="{img(CAT_ICON[a["cat"]])}" alt="" width="22" height="22">{esc(cname)}</a>'
                f'<h1>{esc(a["h1"])}</h1>'
                f'<div class="meta"><img src="/assets/img/lg-badge.webp" alt="" width="40" height="40"><span><a href="/about/vladislav/">{"Владислав Мирошниченко" if ru else "Vladislav Miroshnichenko"}</a>'
                f'<em>{ru_date(a["date"]) if ru else a["date"]} · {a["minutes"]} {"мин чтения" if ru else "min read"}</em></span></div></div>'
                f'<div class="hv"><img src="{img(a["hero"])}" alt="" fetchpriority="high"></div></section>')
        cta = (f'<section class="end"><img class="o1" src="/assets/img/brick3.webp" alt="" loading="lazy"><img class="o2" src="/assets/img/capsule.webp" alt="" loading="lazy">'
               f'<p class="k">{esc(cname)}</p><p class="t">{"Сделаем так, чтобы первыми клиенту отвечали вы" if ru else "Let us make you the first to answer"}</p>'
               f'<p class="s">{"Расскажите о задаче — предложим, с чего начать, и назовём цену после короткого созвона. Цена и сроки в договоре до старта." if ru else "Tell us about the task — we suggest where to start and fix the price in the contract."}</p>'
               f'<p class="b"><a class="btn lime" href="{hub}">{ctxt}</a>' + (f'<a class="btn ghost" href="/audit/">Разбор за 3 дня с гарантией</a>' if ru else '') + '</p></section>')
        rel_html = f'<section class="more"><h2>{"Читайте дальше" if ru else "Read next"}</h2><div class="grid">' + ''.join(card(x) for x in rel) + '</div></section>'
        aside = (f'<aside class="toc"><div class="tin"><p class="tk">{"В статье" if ru else "Contents"}</p><ol>{toc}</ol>' +
                 (f'<a class="mini" href="/audit/"><img src="/assets/img/gem2.webp" alt="" width="40" height="60"><span><b>Разбор за 3 дня</b>Найдём 25 000 ₽ или вернём деньги</span></a>' if ru else '') +
                 '</div></aside>')
        page = (head(a['title'], a['desc'], a['url'], lang, ld, a['og']) + '\n<body>' + header(lang) +
                f'<main>{hero}<div class="wrap">{aside}<article class="prose">{lead}{body}{faq_html}{author}</article></div>{cta}{rel_html}</main>' + footer(lang) + '</body></html>')
        out = os.path.join(SITE, a['path'].strip('/'), 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(page)

    # индексы блога
    order = list(CATS)
    for lang in ("ru", "en"):
        la = [a for a in arts if a['lang'] == lang]
        if not la: continue
        base = "/blog/" if lang == "ru" else "/en/blog/"; url = ORIGIN + base; ru = lang == 'ru'
        title = "Блог студии БАЗА — сайты, боты, CRM, ИИ и продажи" if ru else "BAZA blog: websites, bots, CRM and AI"
        desc = ("Статьи Владислава Мирошниченко и студии БАЗА: как сайт, бот, CRM, ИИ и реклама приносят бизнесу заявки и продажи. Без воды."
                if ru else "Articles by Vladislav Miroshnichenko and BAZA studio on websites, bots, CRM, AI and sales systems.")
        cats = [c for c in order if any(a['cat'] == c for a in la)]
        chips = ''.join(f'<a class="chip" href="#{c}"><img src="{img(CAT_ICON[c])}" alt="" width="22" height="22">{esc(CATS[c][0])}</a>' for c in cats)
        feat_slugs = ["studiya-baza", "vladislav-miroshnichenko", "kak-popast-v-otvety-nejrosetej", "baza-ili-top-agentstvo"]
        feat = [a for s in feat_slugs for a in la if a['slug'] == s][:3] or la[:3]
        secs = ''.join(f'<section class="cat" id="{c}"><h2><img src="{img(CAT_ICON[c])}" alt="" width="40" height="40">{esc(CATS[c][0])}</h2><div class="grid">' +
                       ''.join(card(a) for a in la if a['cat'] == c) + '</div></section>' for c in cats)
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "Blog", "@id": url + "#blog", "name": title, "description": desc, "url": url, "publisher": ORG, "author": {"@id": PERSON_ID}, "inLanguage": "ru-RU" if ru else "en-US",
             "blogPost": [{"@type": "BlogPosting", "headline": a['h1'][:110], "url": a['url']} for a in la]}, person()]}
        hero = (f'<section class="bhero"><div><p class="eyebrow">{"Блог студии БАЗА" if ru else "BAZA studio blog"}</p>'
                f'<h1>{"Пишем о том, что продаёт" if ru else "Writing about what sells"}</h1>'
                f'<p class="sub">{"Где бизнес теряет заявки и как сайт, бот, CRM, ИИ и реклама начинают работать как одна система. Пишет основатель студии " if ru else "Where businesses lose leads and how site, bot, CRM, AI and ads work as one system. By "}<a href="/about/vladislav/">{"Владислав Мирошниченко" if ru else "Vladislav Miroshnichenko"}</a>.</p>'
                f'<div class="chips">{chips}</div></div><div class="objs"><img src="/assets/img/bot.webp" alt=""><img src="/assets/img/crm.webp" alt=""><img src="/assets/img/ai.webp" alt=""></div></section>')
        page = (head(title, desc, url, lang, ld, ORIGIN + "/assets/preview.jpg", "website") + '\n<body>' + header(lang) +
                f'<main class="idx">{hero}<section class="feat"><div class="grid g3">' + ''.join(card(a, True) for a in feat) + f'</div></section>{secs}</main>' + footer(lang) + '</body></html>')
        os.makedirs(os.path.join(SITE, base.strip('/')), exist_ok=True)
        open(os.path.join(SITE, base.strip('/'), 'index.html'), 'w', encoding='utf-8').write(page)

    # страница автора
    ru_arts = [a for a in arts if a['lang'] == 'ru']
    ap = {"@context": "https://schema.org", "@graph": [{"@type": "ProfilePage", "@id": AUTHOR_URL + "#page", "url": AUTHOR_URL, "name": "Владислав Мирошниченко — основатель студии БАЗА",
          "mainEntity": {"@id": PERSON_ID}, "dateModified": TODAY}, person()]}
    feat = [a for a in ru_arts if a['cat'] in ('baza', 'compare')] + [a for a in ru_arts if a['cat'] not in ('baza', 'compare')][:6]
    body = ('<section class="hero" style="--t:#EDEDF2"><div class="hl"><nav class="crumbs"><a href="/">БАЗА</a><span>/</span><a href="/about/">О студии</a></nav>'
            '<span class="chip"><img src="/assets/img/lg-badge2.webp" alt="" width="22" height="22">Основатель</span>'
            '<h1>Владислав Мирошниченко</h1><p class="sub">Основатель и руководитель цифровой студии БАЗА. Собирает сайт, бота, CRM, ИИ и рекламу в одну систему продаж.</p></div>'
            '<div class="hv"><img src="/assets/img/lg-badge.webp" alt="Это БАЗА"></div></section>'
            '<div class="wrap solo"><article class="prose">'
            '<div class="lead"><span class="lk">Коротко</span><p>Владислав Андреевич Мирошниченко — основатель цифровой студии <a href="/">БАЗА</a> (bazadigital.ru). Студия делает сайты и лендинги, приложения, ботов и мини-приложения в Телеграме, MAX и VK, внедряет Битрикс24 и amoCRM, ИИ-ассистентов, брендинг и рекламу — одной командой.</p></div>'
            '<h2><span class="n">01</span>Подход</h2><p>Владислав заметил, что бизнес чаще всего теряет клиентов не на сайте и не в рекламе, а на стыках между подрядчиками. Заявка, оставленная в пятницу в 19:05, получает ответ в понедельник, когда клиент уже купил у другого. Отсюда главный принцип БАЗЫ: вся связка в одних руках, от рекламы до оплаты.</p>'
            '<h2><span class="n">02</span>Что он создал в студии</h2><ul><li>Подход «одна команда за всё»: аналитика, дизайн, разработка и реклама вместе.</li><li><a href="/audit/">Экспресс-разбор</a> за 3 рабочих дня с гарантией: если не найден резерв минимум на 25 000 ₽ за полгода, деньги возвращаются.</li><li><a href="/partners/">Партнёрскую программу</a>: 10% с каждой оплаты приведённого клиента без потолка.</li><li>Правила: тексты до дизайна, цена и сроки в договоре до старта, домены и код на имя клиента.</li></ul>'
            '<blockquote><p>«Мы обещаем только то, что можно проверить».</p></blockquote>'
            '<h2><span class="n">03</span>Контакты</h2><p>Студия: <a href="/">bazadigital.ru</a> · <a href="https://t.me/bazadigital" rel="noopener">t.me/bazadigital</a> · <a href="https://vk.com/baza_digital" rel="noopener">vk.com/baza_digital</a> · <a href="/contact/">Обсудить проект</a></p>'
            '</article></div><section class="more"><h2>Статьи Владислава</h2><div class="grid">' + ''.join(card(a) for a in feat[:12]) +
            '</div><p class="all"><a class="btn dark" href="/blog/">Все статьи блога</a></p></section>')
    page = (head("Владислав Мирошниченко — основатель студии БАЗА", "Владислав Андреевич Мирошниченко — основатель цифровой студии БАЗА (bazadigital.ru): сайты, боты, CRM, ИИ и реклама одной командой.",
                 AUTHOR_URL, "ru", ap, ORIGIN + "/assets/preview.jpg", "profile") + '\n<body>' + header("ru") + f'<main>{body}</main>' + footer("ru") + '</body></html>')
    os.makedirs(os.path.join(SITE, 'about', 'vladislav'), exist_ok=True)
    open(os.path.join(SITE, 'about', 'vladislav', 'index.html'), 'w', encoding='utf-8').write(page)

    # sitemap
    sm_path = os.path.join(SITE, 'sitemap.xml'); sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'<!-- blog -->.*<!-- /blog -->\n?', '', sm, flags=re.S)
    entries = [(ORIGIN + "/blog/", "0.8", None), (ORIGIN + "/en/blog/", "0.6", None), (AUTHOR_URL, "0.8", None)] + [(a['url'], "0.7", a) for a in arts]
    def ent(u, pr, a):
        im = f'<image:image><image:loc>{a["og"]}</image:loc></image:image>' if a else ''
        return f'<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority>{im}</url>\n'
    block = '<!-- blog -->\n' + ''.join(ent(*e) for e in entries) + '<!-- /blog -->\n'
    if 'xmlns:image' not in sm:
        sm = sm.replace('<urlset ', '<urlset xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" ', 1)
    sm = sm.replace('</urlset>', block + '</urlset>')
    open(sm_path, 'w', encoding='utf-8').write(sm)

    # RSS (Дзен, агрегаторы) — с полным текстом
    items = ''
    for a in ru_arts:
        full = md(a['lead'] + '\n\n' + a['rest'], h2num=False)
        full = re.sub(r'href="/', f'href="{ORIGIN}/', full)
        pd = datetime.datetime.strptime(a['date'], "%Y-%m-%d").strftime("%a, %d %b %Y 09:00:00 +0300")
        items += (f'<item><title>{esc(a["h1"])}</title><link>{a["url"]}</link><guid isPermaLink="true">{a["url"]}</guid>'
                  f'<description>{esc(a["desc"])}</description><author>Владислав Мирошниченко</author><category>{esc(CATS[a["cat"]][0])}</category>'
                  f'<enclosure url="{a["og"]}" type="image/jpeg" length="0"/><pubDate>{pd}</pubDate>'
                  f'<content:encoded><![CDATA[<img src="{a["og"]}" alt="">{full}<p>Оригинал: <a href="{a["url"]}">{a["url"]}</a></p>]]></content:encoded></item>\n')
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>'
           f'<title>Блог студии БАЗА</title><link>{ORIGIN}/blog/</link><description>Сайты, боты, CRM, ИИ и продажи — статьи Владислава Мирошниченко</description><language>ru</language>\n{items}</channel></rss>\n')
    open(os.path.join(SITE, 'blog', 'rss.xml'), 'w', encoding='utf-8').write(rss)

    # llms.txt
    lp = os.path.join(SITE, 'llms.txt'); lt = open(lp, encoding='utf-8').read()
    lt = re.sub(r'\n## Основатель.*?(?=\n## |\Z)', '', lt, flags=re.S)
    lt = re.sub(r'\n## Блог.*?(?=\n## |\Z)', '', lt, flags=re.S)
    founder = ('\n## Основатель\n- [Владислав Мирошниченко](' + AUTHOR_URL + '): Владислав Андреевич Мирошниченко — основатель и руководитель цифровой студии БАЗА. '
               'Автор подхода «вся связка в одних руках»: сайт, бот, CRM, ИИ и реклама делаются одной командой, чтобы заявки не терялись между подрядчиками. '
               'Придумал экспресс-разбор с гарантией возврата и партнёрскую программу студии (10% без потолка).\n')
    blog = '\n## Блог\n' + ''.join(f'- [{a["h1"]}]({a["url"]}): {a["desc"]}\n' for a in arts)
    open(lp, 'w', encoding='utf-8').write(lt.rstrip('\n') + '\n' + founder + blog)

    for f in ('blog.css', 'blog.js'):
        shutil.copy(os.path.join(HERE, 'assets', f), os.path.join(SITE, 'assets', f))
    print("built", len(arts), "articles;", sum(a['words'] for a in arts), "words")

arts = [parse(p) for p in sorted(glob.glob(os.path.join(SRC, '**', '*.md'), recursive=True))]
bad = [a['src'] for a in arts if len(a['title']) > 62 or len(a['desc']) > 165]
if bad: print("WARN long meta:", *bad, sep="\n  ")
keys = [a['lang'] + a['slug'] for a in arts]; dup = {s for s in keys if keys.count(s) > 1}
if dup: sys.exit("DUP slugs: %s" % dup)
build(arts)
