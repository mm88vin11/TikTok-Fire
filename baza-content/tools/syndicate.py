#!/usr/bin/env python3
"""Пакет для внешних площадок: полные версии (vc.ru, Дзен, Spark, Teletype, Medium...) и короткие посты (TenChat, VK, OK, Телеграм).
Запуск: python3 tools/syndicate.py articles для-площадок"""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = sys.argv[1], sys.argv[2]
ORIGIN = "https://bazadigital.ru"
CATN = {"baza": "О студии", "compare": "Сравнения", "sites": "Сайты", "bots": "Боты", "crm": "CRM", "ai": "ИИ", "promo": "Продвижение",
        "brand": "Брендинг", "apps": "Приложения", "niches": "Отрасли", "partners": "Партнёрам", "guides": "Гайды", "en": "English"}

def meta(raw):
    m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S); d = {}
    for l in m.group(1).split('\n'):
        if ':' in l: k, v = l.split(':', 1); d[k.strip()] = v.strip()
    d['body'] = m.group(2).strip(); d.setdefault('lang', 'ru'); return d

def absl(t): return re.sub(r'\]\(/', '](' + ORIGIN + '/', t)

os.makedirs(os.path.join(OUT, 'полные-статьи'), exist_ok=True)
posts, tg = [], []
for f in sorted(glob.glob(os.path.join(SRC, '*', '*.md'))):
    a = meta(open(f, encoding='utf-8').read()); n = os.path.basename(f)[:-3]
    base = "/en/blog/" if a['lang'] == 'en' else "/blog/"; url = ORIGIN + base + a['slug'] + "/"
    og = f"{ORIGIN}/assets/blog/og/{a['lang']}-{a['slug']}.jpg"
    ru = a['lang'] == 'ru'
    foot = (f"\n\n---\n\n*Автор — Владислав Мирошниченко, основатель цифровой студии БАЗА (bazadigital.ru): сайты, боты, CRM, ИИ и реклама одной командой.*\n\n"
            f"Оригинал статьи: {url}\n\nОбсудить задачу: {ORIGIN}/contact/ · Телеграм студии: https://t.me/bazadigital\n") if ru else \
           (f"\n\n---\n\n*By Vladislav Miroshnichenko, founder of BAZA digital studio (bazadigital.ru).*\n\nOriginal: {url}\n")
    full = f"# {a['h1']}\n\nОбложка: {og}\n\n" + absl(a['body']) + foot
    open(os.path.join(OUT, 'полные-статьи', f"{n}-{a['slug']}.md"), 'w', encoding='utf-8').write(full)
    lead = a['body'].split('\n\n', 1)[0].strip()
    if len(lead) > 420: lead = lead[:lead.rfind('. ', 0, 420) + 1]
    h2 = [h for h in re.findall(r'^## (.+)$', a['body'], re.M) if not h.startswith(('Частые', 'FAQ'))][:4]
    tags = ' '.join('#' + re.sub(r'[^\wа-яё]', '', k.strip().split(' ')[0] + ''.join(w.capitalize() for w in k.strip().split(' ')[1:]), flags=re.I)
                    for k in a.get('keys', '').strip('[]').split(',')[:3] if k.strip())
    if ru:
        p = (f"{a['h1']}\n\n{lead}\n\nВ статье:\n" + ''.join(f"— {h}\n" for h in h2) + f"\nЧитать полностью: {url}\n\n#БАЗА #bazadigital {tags}")
        posts.append(f"## {n} · {CATN.get(a['cat'], '')} · {a['h1']}\n\nКартинка: {og}\n\n```\n{p}\n```\n")
        tg.append(f"**{a['h1']}**\n\n{lead}\n\n→ {url}")
    else:
        posts.append(f"## {n} · English · {a['h1']}\n\nImage: {og}\n\n```\n{a['h1']}\n\n{lead}\n\nRead: {url}\n```\n")
open(os.path.join(OUT, 'короткие-посты-TenChat-VK-OK-LinkedIn.md'), 'w', encoding='utf-8').write(
    "# Короткие посты к каждой статье\n\nКопируйте текст из блока, прикрепляйте картинку по ссылке. Подходит для TenChat, ВКонтакте, Одноклассников, LinkedIn, Пикабу.\n\n" + '\n'.join(posts))
open(os.path.join(OUT, 'посты-для-телеграма.md'), 'w', encoding='utf-8').write(
    "# Посты для Телеграм-канала\n\nПо одному в день. Текст + ссылка, превью с обложкой подтянется само.\n\n" + '\n\n---\n\n'.join(tg))
print('syndication:', len(posts))
