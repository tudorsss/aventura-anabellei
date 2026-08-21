#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Face `www/` — varianta de aplicatie a jocului — din fisierele din radacina.

Trei lucruri se schimba fata de varianta web, si fiecare are un motiv:
  1. fontul devine local. Un recenzent Apple poate porni aplicatia in modul
     avion; cu fontul luat de la Google, ar vedea alt font si texte deplasate.
  2. service worker-ul se scoate. In aplicatie nu e nimic de pus in cache — tot
     jocul e deja pe telefon — si un cache vechi ar putea servi o versiune
     veche dupa un update din App Store.
  3. sfatul "adauga pe ecranul principal" se scoate. Aplicatia E deja pe ecranul
     principal; sfatul ar fi absurd si Apple il citeste ca instructiune de a
     folosi altceva decat aplicatia.
Plus cateva reglaje de WebView: fara zoom, fara selectie de text, fara
scroll-ul elastic, si zona sigura respectata (crestatura telefonului).
"""
import io, os, re, shutil, sys

AICI = os.path.dirname(os.path.abspath(__file__))
RADACINA = os.path.dirname(AICI)
WWW = os.path.join(AICI, 'www')

def citeste(p): return io.open(p, encoding='utf-8').read()

def main():
    if os.path.isdir(WWW): shutil.rmtree(WWW)
    os.makedirs(WWW)

    html = citeste(os.path.join(RADACINA, 'index.html'))
    pornit = len(html)

    # 1. fontul local
    vechi_link = re.search(r'<link rel="preconnect" href="https://fonts\.googleapis\.com">.*?'
                           r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>',
                           html, re.S)
    if not vechi_link: sys.exit('nu gasesc legatura catre Google Fonts')
    fonturi = citeste(os.path.join(AICI, 'fonts', 'fonts-local.css'))
    html = html.replace(vechi_link.group(0), '<style>\n' + fonturi + '</style>')

    # 2. service worker-ul
    sw = re.search(r"  /\* service worker.*?\n  \}\n", html, re.S)
    if not sw: sys.exit('nu gasesc inregistrarea service worker-ului')
    html = html.replace(sw.group(0), "  /* in aplicatie nu e nevoie de service worker: tot jocul e deja pe telefon */\n")

    # 3. sfatul de instalare pe ecranul principal
    sfat = re.search(r"  /\* sfatul de instalare.*?\n  \}\n", html, re.S)
    if not sfat: sys.exit('nu gasesc blocul cu sfatul de instalare')
    html = html.replace(sfat.group(0), "  /* in aplicatie nu are sens un sfat de instalare */\n")
    bara = re.search(r'<div id="instaleaza">.*?</div>\n', html, re.S)
    if not bara: sys.exit('nu gasesc bara de instalare')
    html = html.replace(bara.group(0), '')

    # 3c. legatura catre manifest-ul de PWA. Manifestul e pentru instalarea din
    #     browser; in aplicatie nu are ce sa faca, si cum nu copiem fisierul in
    #     www/, WebView-ul cere un fisier care nu exista si da 404 la pornire.
    manifest = re.search(r'\s*<link rel="manifest"[^>]*>', html)
    if not manifest: sys.exit('nu gasesc legatura catre manifest')
    html = html.replace(manifest.group(0), '')

    # 3b. stilurile barei de instalare si linia care vorbeste de server
    css_sfat = re.search(r'/\* ---------- sfat de instalare[^*]*\*/.*?\n(?=/\* -|</style>)', html, re.S)
    if css_sfat: html = html.replace(css_sfat.group(0), '')
    html = re.sub(r'#instaleaza[^{]*\{[^}]*\}\n?', '', html)
    vechi_fps = "(navigator.serviceWorker && navigator.serviceWorker.controller ? 'salvat local' : 'de la server')"
    if vechi_fps in html:
        html = html.replace(vechi_fps, "'aplicație'")

    # 4. reglaje de WebView
    vp = '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">'
    html = re.sub(r'<meta name="viewport"[^>]*>', vp, html, count=1)
    html = html.replace('</head>',
      '<style>\n'
      '/* reglaje pentru aplicatie: fara selectie, fara zoom cu doua degete,\n'
      '   fara scroll elastic, si loc pentru crestatura telefonului */\n'
      'html,body{-webkit-user-select:none;user-select:none;-webkit-touch-callout:none;\n'
      '  overscroll-behavior:none;touch-action:manipulation;\n'
      '  padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)}\n'
      '</style>\n</head>')

    io.open(os.path.join(WWW, 'index.html'), 'w', encoding='utf-8').write(html)

    # fisierele care raman
    shutil.copytree(os.path.join(AICI, 'fonts'), os.path.join(WWW, 'fonts'),
                    ignore=shutil.ignore_patterns('*.css'))
    shutil.copytree(os.path.join(RADACINA, 'icons'), os.path.join(WWW, 'icons'))
    shutil.copy(os.path.join(RADACINA, 'apple-touch-icon.png'), WWW)

    # verificari: ce NU are voie sa ramana in varianta de aplicatie
    rele = []
    if 'fonts.googleapis.com' in html or 'fonts.gstatic.com' in html:
        rele.append('a ramas o legatura catre Google Fonts')
    if 'serviceWorker' in html: rele.append('a ramas o referire la service worker')
    if 'id="instaleaza"' in html: rele.append('a ramas bara de instalare')
    if 'anabelle-instalare' in html: rele.append('a ramas sfatul de instalare')
    if 'rel="manifest"' in html: rele.append('a ramas legatura catre manifest-ul de PWA')
    if re.search(r'https?://(?!www\.w3\.org)', html): rele.append('a ramas o adresa externa')
    for carlig in ('__t', 'globalThis.__'):
        if carlig in html: rele.append('a ramas un carlig de test: ' + carlig)
    if rele:
        print('NU E BUN:'); [print('  -', r) for r in rele]; sys.exit(1)

    n = os.path.getsize(os.path.join(WWW, 'index.html'))
    print('www/ gata. index.html %d -> %d caractere (fontul e acum inauntru)' % (pornit, n))
    print('fisiere:', sorted(os.listdir(WWW)))

if __name__ == '__main__':
    main()
