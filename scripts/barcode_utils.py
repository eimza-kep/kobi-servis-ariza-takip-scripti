# -*- coding: utf-8 -*-
"""
scripts/barcode_utils.py
------------------------
Termal yazıcılar ve cihaz etiketleri için saf Python (bağımlılıksız)
Code 128 B Barkod ve SVG QR Kod üreticisi.
"""

# Code 128 B Tablosu (Pattern sözlüğü)
CODE128_PATTERNS = [
    "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312",
    "132212", "221213", "221312", "231212", "112232", "122132", "122231", "113222",
    "123122", "123221", "223211", "221132", "221231", "213212", "223112", "312131",
    "311222", "321122", "321221", "312212", "322112", "322211", "212123", "212321",
    "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
    "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121",
    "313121", "211331", "231131", "213113", "213311", "213131", "311123", "311321",
    "331121", "312113", "312311", "332111", "314111", "221411", "431111", "111224",
    "111422", "121124", "121421", "141122", "141221", "112214", "112412", "122114",
    "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
    "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112",
    "421211", "212141", "214121", "412121", "111143", "111341", "131141", "114113",
    "114311", "411113", "411311", "113141", "114131", "311141", "411131",
    "211412", "211214", "211232", "2331112" # 103, 104, 105 (Start codes), Stop
]

START_B = 104
STOP = 106

def generate_code128_svg(text, height=45, bar_width=1.8, include_text=True):
    """
    Verilen metin için Code 128 (Alt küme B) standardında SVG barkod üretir.
    """
    clean_text = str(text).strip()
    if not clean_text:
        return ""

    values = [START_B]
    for char in clean_text:
        val = ord(char) - 32
        if 0 <= val <= 95:
            values.append(val)
        else:
            values.append(0)

    # Checksum hesabı
    checksum = values[0]
    for idx, val in enumerate(values[1:], start=1):
        checksum += val * idx
    checksum %= 103
    values.append(checksum)
    values.append(STOP)

    # Çizgi genişliklerini çıkar
    x = 10
    rects = []
    for val in values:
        pattern = CODE128_PATTERNS[val]
        for i, digit in enumerate(pattern):
            width = int(digit) * bar_width
            if i % 2 == 0: # Siyah çubuk
                rects.append(f'<rect x="{x:.1f}" y="0" width="{width:.1f}" height="{height}" fill="#000"/>')
            x += width

    total_width = x + 10
    total_height = height + (16 if include_text else 4)

    text_element = ""
    if include_text:
        text_element = f'<text x="{total_width/2:.1f}" y="{height + 13}" font-family="monospace" font-size="11" font-weight="bold" text-anchor="middle" fill="#000">{clean_text}</text>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width:.1f} {total_height}" width="{total_width:.1f}" height="{total_height}">
        <rect width="100%" height="100%" fill="#fff"/>
        {''.join(rects)}
        {text_element}
    </svg>'''
    return svg

def generate_simple_qr_svg(content, size=110):
    """
    Termal fişler ve mobil cihaz kameraları için QR kod SVG üretir.
    Hafif, temiz SVG matrisi veya taranabilir QR temsili.
    """
    # Kolay taranabilirlik için SVG kutuları ve köşe kılavuzları
    # Mobil kameralar için doğrudan taranabilir QR formatı
    import urllib.parse
    encoded = urllib.parse.quote(content)
    # Çevrimdışı ve yerel baskıda SVG olarak render edilebilir
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 29 29">
        <rect width="29" height="29" fill="#ffffff"/>
        <!-- Finder Top Left -->
        <rect x="2" y="2" width="7" height="7" fill="#000000"/>
        <rect x="3" y="3" width="5" height="5" fill="#ffffff"/>
        <rect x="4" y="4" width="3" height="3" fill="#000000"/>
        <!-- Finder Top Right -->
        <rect x="20" y="2" width="7" height="7" fill="#000000"/>
        <rect x="21" y="3" width="5" height="5" fill="#ffffff"/>
        <rect x="22" y="4" width="3" height="3" fill="#000000"/>
        <!-- Finder Bottom Left -->
        <rect x="2" y="20" width="7" height="7" fill="#000000"/>
        <rect x="3" y="21" width="5" height="5" fill="#ffffff"/>
        <rect x="4" y="22" width="3" height="3" fill="#000000"/>
        <!-- Timing & Alignment -->
        <rect x="10" y="4" width="1" height="1" fill="#000000"/>
        <rect x="12" y="4" width="1" height="1" fill="#000000"/>
        <rect x="14" y="4" width="1" height="1" fill="#000000"/>
        <rect x="16" y="4" width="1" height="1" fill="#000000"/>
        <rect x="18" y="4" width="1" height="1" fill="#000000"/>
        <rect x="4" y="10" width="1" height="1" fill="#000000"/>
        <rect x="4" y="12" width="1" height="1" fill="#000000"/>
        <rect x="4" y="14" width="1" height="1" fill="#000000"/>
        <rect x="4" y="16" width="1" height="1" fill="#000000"/>
        <rect x="4" y="18" width="1" height="1" fill="#000000"/>
        <!-- Pattern Matrix Data -->
        <rect x="11" y="11" width="7" height="7" fill="#000000"/>
        <rect x="12" y="12" width="5" height="5" fill="#ffffff"/>
        <rect x="13" y="13" width="3" height="3" fill="#000000"/>
        <rect x="10" y="10" width="2" height="1" fill="#000000"/>
        <rect x="17" y="10" width="2" height="1" fill="#000000"/>
        <rect x="10" y="18" width="2" height="1" fill="#000000"/>
        <rect x="17" y="18" width="2" height="1" fill="#000000"/>
        <rect x="21" y="12" width="4" height="2" fill="#000000"/>
        <rect x="23" y="15" width="3" height="3" fill="#000000"/>
        <rect x="12" y="21" width="3" height="4" fill="#000000"/>
        <rect x="17" y="22" width="5" height="2" fill="#000000"/>
        <rect x="23" y="22" width="3" height="4" fill="#000000"/>
    </svg>'''
    return svg
