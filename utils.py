import re, random, collections
from templates import RU_TEMPLATES, RU_FOLLOWUPS, EN_TEMPLATES, EN_FOLLOWUPS

RU_STOP = set(\"\"\"и в во на но ни не или да же что это как так а к ко о от до из бы же уж ли ведь при по над под для без про между также также-таки ещё уже более менее был была было были если то то-то тот эта это эти эту будет будут есть был бы чтобы потому поэтому когда где куда откуда такой такая такое такие которых которых и/или / \\ | — - _ . , ! ? : ; ( ) [ ] {{ }} ' \"\"\".split())
EN_STOP = set(\"\"\"the a an to of for in on at and or but so if then else when where how what which who whom whose is are was were be been being have has had do does did not no yes ok okay this that these those from by with as it it's its i'm you're we're they're can can't won't don't didn't hasn't haven't should shouldn't could couldn't would wouldn't
/ \\ | — - _ . , ! ? : ; ( ) [ ] {{ }} ' \"\"\".split())

def tokenize(text):
    text = text.lower()
    tokens = re.findall(r\"[\\w\\-#@]+\", text, flags=re.U)
    return tokens

def keywords_from_messages(messages, lang='ru', topn=5):
    stop = RU_STOP if lang=='ru' else EN_STOP
    freq = collections.Counter()
    for m in messages:
        toks = [t for t in tokenize(m) if t not in stop and len(t) > 2]
        freq.update(toks)
    kws = [w for w,_ in freq.most_common(topn)]
    return kws or ["тема"]

def build_reply(kws, lang='ru'):
    kw = random.choice(kws)
    if lang=='ru':
        tpl = random.choice(RU_TEMPLATES)
        q = random.choice(RU_FOLLOWUPS)
    else:
        tpl = random.choice(EN_TEMPLATES)
        q = random.choice(EN_FOLLOWUPS)
    return tpl.format(kw=kw, q=q)
