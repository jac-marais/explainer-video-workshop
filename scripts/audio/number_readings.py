"""Pure Python French, Portuguese, Spanish, Hindi, Mandarin and Sino-Korean number readings.

Nonnegative integers below a million, dot decimals (fractional digits read
individually), and percent suffixes. Results retain spoken word boundaries.
Portuguese and Spanish also return their feminine and shortened forms, such as
duas and una, because the script agrees the number with its noun.
"""
import re

FR = 'zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize'.split()
HI = '''शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस
बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस
तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस
चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास
पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ
साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर
सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उनासी
अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी
नब्बे इक्यानवे बानवे तिरानवे चौरानवे पंचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे'''.split()


def french(n):
    if n < 17:
        return FR[n]
    if n < 20:
        return 'dix ' + FR[n - 10]
    if n < 70:
        tens = ['', '', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante'][n // 10]
        return tens + (' et un' if n % 10 == 1 else ' ' + french(n % 10) if n % 10 else '')
    if n < 80:
        return 'soixante ' + ('et ' if n == 71 else '') + french(n - 60)
    if n < 100:
        return 'quatre vingts' if n == 80 else 'quatre vingt ' + french(n - 80)
    unit = 100 if n < 1000 else 1000
    q, r = divmod(n, unit)
    head = ('cent' if q == 1 else french(q) + ' cent' + ('s' if not r else '')) if unit == 100 else ('mille' if q == 1 else re.sub(r'(vingt|cent)s$', r'\1', french(q)) + ' mille')
    return head + (' ' + french(r) if r else '')


def hindi(n):
    if n < 100:
        return HI[n]
    unit, name = (100, 'सौ') if n < 1000 else (1000, 'हज़ार') if n < 100000 else (100000, 'लाख')
    q, r = divmod(n, unit)
    return hindi(q) + ' ' + name + (' ' + hindi(r) if r else '')


def chinese(n):
    if n < 10:
        return '零一二三四五六七八九'[n]
    unit, name = next((u, s) for u, s in [(10000, '万'), (1000, '千'), (100, '百'), (10, '十')] if n >= u)
    q, r = divmod(n, unit)
    head = ('' if unit == 10 and q == 1 else chinese(q)) + name
    # A trailing two-digit group needs its leading 一 after a larger unit.
    tail = ('一' if 10 <= r < 20 else '') + chinese(r) if r else ''
    return head + ('零' if r and r < unit // 10 else '') + tail


def korean(n):
    if n < 10:
        return '영일이삼사오육칠팔구'[n]
    unit, name = next((u, s) for u, s in [(10000, '만'), (1000, '천'), (100, '백'), (10, '십')] if n >= u)
    q, r = divmod(n, unit)
    return ('' if q == 1 else korean(q)) + name + (korean(r) if r else '')


PT = ('zero um dois três quatro cinco seis sete oito nove dez onze doze treze catorze quinze '
      'dezesseis dezessete dezoito dezenove').split()
PT_TENS = ',,vinte,trinta,quarenta,cinquenta,sessenta,setenta,oitenta,noventa'.split(',')
PT_HUNDREDS = ',cento,duzentos,trezentos,quatrocentos,quinhentos,seiscentos,setecentos,oitocentos,novecentos'.split(',')


def portuguese(n):
    if n < 20:
        return PT[n]
    if n < 100:
        return PT_TENS[n // 10] + (' e ' + PT[n % 10] if n % 10 else '')
    if n < 1000:
        return 'cem' if n == 100 else PT_HUNDREDS[n // 100] + (' e ' + portuguese(n % 100) if n % 100 else '')
    q, r = divmod(n, 1000)
    head = 'mil' if q == 1 else portuguese(q) + ' mil'
    # "e" joins a remainder below a hundred or a round hundred; otherwise a space does.
    return head + ((' e ' if r < 100 or r % 100 == 0 else ' ') + portuguese(r) if r else '')


ES = ('cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince '
      'dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro '
      'veinticinco veintiséis veintisiete veintiocho veintinueve').split()
ES_TENS = ',,,treinta,cuarenta,cincuenta,sesenta,setenta,ochenta,noventa'.split(',')
ES_HUNDREDS = ',ciento,doscientos,trescientos,cuatrocientos,quinientos,seiscientos,setecientos,ochocientos,novecientos'.split(',')


def spanish(n):
    if n < 30:
        return ES[n]
    if n < 100:
        return ES_TENS[n // 10] + (' y ' + ES[n % 10] if n % 10 else '')
    if n < 1000:
        return 'cien' if n == 100 else ES_HUNDREDS[n // 100] + (' ' + spanish(n % 100) if n % 100 else '')
    q, r = divmod(n, 1000)
    # Before mil, uno shortens: veintiún mil, treinta y un mil.
    head = 'mil' if q == 1 else re.sub(r'(?:^| )uno$', lambda m: m[0][:-1], re.sub(r'veintiuno$', 'veintiún', spanish(q))) + ' mil'
    return head + (' ' + spanish(r) if r else '')


def agreements(text, language):
    """The masculine reading plus its feminine and shortened forms."""
    if language == 'pt':
        feminine = re.sub(r'\b(um|dois)\b', lambda m: {'um': 'uma', 'dois': 'duas'}[m[1]], text)
        forms = {text, re.sub(r'entos\b', 'entas', feminine)}
        # Brazilian speech also says quatorze.
        return forms | {form.replace('catorze', 'quatorze') for form in forms}
    if language == 'es':
        swap = lambda words: re.sub(r'\b(veinti)?uno\b', lambda m: (m[1] or '') + words[bool(m[1])], text)
        feminine = re.sub(r'ientos\b', 'ientas', swap(('una', 'una')))
        return {text, swap(('un', 'ún')), feminine}
    return {text}


LANGUAGES = {'fr': french, 'pt': portuguese, 'es': spanish, 'hi': hindi, 'zh': chinese, 'ko': korean}


def spoken_numbers(text, language):
    """Return spoken forms, or an empty set for unsupported/non-numeric input."""
    match = re.fullmatch(r'\s*(\d+)(?:\.(\d+))?(%)?\s*[.,。!?！？।]?\s*', text)
    if language not in LANGUAGES or not match or int(match[1]) >= 10**6:
        return set()
    say = LANGUAGES[language]
    result = say(int(match[1]))
    if match[2]:
        point = {'fr': ' virgule ', 'pt': ' vírgula ', 'es': ' coma ', 'hi': ' पॉइंट ', 'zh': '点', 'ko': ' 점 '}[language]
        separator = '' if language in ('zh', 'ko') else ' '
        result += point + separator.join(say(int(d)) for d in match[2])
    if match[3]:
        result = '百分之' + result if language == 'zh' else result + {'fr': ' pour cent', 'pt': ' por cento', 'es': ' por ciento', 'hi': ' प्रतिशत', 'ko': ' 퍼센트'}[language]
    found = agreements(result, language)
    if language == 'hi':
        found.add(result.replace('हज़ार', 'हजार'))
    return found
