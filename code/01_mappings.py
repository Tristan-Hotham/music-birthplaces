"""Group Wikidata music occupations (P106) and genres (P136) into a few broad families.

Inputs (complete QLever exports, retrieved 2026):
  raw4/music_occupations.tsv   ?occ ?occL   every subclass of musician (Q639669) used as an occupation
  raw4/genre_labels.tsv        ?genre ?gL   English labels of every genre linked from a musician or band
  raw4/musician_genres.tsv, raw4/band_genres.tsv   usage counts, used only to report how much each rule covers
Outputs:
  data/occupation_families.csv   occupation Q-id, label, family, people (persons with that occupation, if counted)
  data/genre_families.csv        genre Q-id, label, family, links (musician and band links)

Rules are ordered regular expressions on the lower-cased English label: the first family whose rule matches wins.
A person can belong to several occupation families (a singer who is also a composer counts in both); each occupation
belongs to exactly one family. Labels with no English label go to 'other'.
"""
import csv, re, sys, os
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RAW4 = os.environ.get("MUS_RAW", "/home/claude/newdata/raw4")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); os.makedirs(DATA, exist_ok=True)

OCC_FAM = [  # key, display name, rule
    ("other", "Other musicians", r"teacher|educator|professor|pedagog|lecturer|musicolog|critic|theorist|librarian|copyist|engraver|"
                                 r"instrument maker|luthier|manager|promoter|impresario|^musician$|^musicians$|recording artist|music interpreter|"
                                 r"church musician|military musician|^soloist$|music artist|performer"),
    ("rap", "Rappers and MCs", r"rapper|\bmc\b|hip.?hop (musician|artist)|beatbox|toaster|freestyle|drill artist|grime"),
    ("dj", "DJs and producers", r"\bdj\b|disc jockey|deejay|producer|beatmaker|remixer|track ?maker|turntabl|vocaloid|selector"),
    ("conductor", "Conductors and bandleaders", r"conductor|choir director|chapel ?master|kapellmeister|bandleader|band leader|chorus master|"
                                                 r"music director|musical director|bandmaster|director of bands|maestro|kirchenmusikdirektor|precentor|choirmaster|choir master|"
                                                 r"cantor of a choir|thomaskantor|orchestra leader|director of music"),
    ("songwriter", "Songwriters", r"songwriter|song ?writer|lyricist|hymn ?writer|hymnographer|liedermacher|librettist|jingle writer|tunesmith"),
    ("composer", "Composers and arrangers", r"compos|arranger|orchestrator|melodist|contrapuntist"),
    ("singer", "Singers", r"singer|vocalist|soprano|tenor|baritone|contralto|mezzo|\balto\b|countertenor|castrato|cantor|hazzan|chanteuse|chansonnier|"
                          r"cantaor|cantaora|playback|troubadour|trouv[eè]re|minnesinger|meistersinger|bard|ashik|ashugh|bertsolari|khananda|yodel|"
                          r"crooner|diva|vedette|qāriʾ|reciter|muezzin|griot|choir|chorister|gospel|mugham|qawwal|jazz singer|scat|chant|minnes[aä]nger|yoik|calypsonian|"
                          r"bass singer|\bbasso\b|treble|throat|kirtan|bhajan|enka|fado|rebetiko|skald|minstrel|jongleur|lamenter"),
    ("instr", "Instrumentalists", r"ist\b|player|piper|drummer|fiddler|trumpeter|keyboard|organ|accompan|r[ée]p[ée]titeur|concertmaster|kobzar|"
                                  r"tambourinaire|bell.?ringer|bagpip|session musician|string|brass|wind instrument|spelman|instrumentalist|"
                                  r"bassist|guitar|piano|violin|cello|flute|horn|oboe|bandura|sitar|tabla|santur|duduk|kora|harp|drum|txistulari|trikitilari|lirnyk|alta cappella"),
]
GEN_FAM = [  # key, display name, rule (first match wins, so specific families come before broad ones)
    ("eapop", "K-pop, J-pop and East Asian pop", r"nhạc trẻ|group sounds|yellow music|\bk-?pop|\bj-?pop|\bj-?rock|\bc-?pop|mandopop|cantopop|kay[oō]kyoku|enka|anime song|city pop|visual kei|"
                                                 r"\btrot\b|\bv-?pop|thai pop|\bt-?pop\b|idol|shibuya|japanese (rock|pop)|korean (rock|pop|ballad)|taiwanese pop|"
                                                 r"hong kong|vocaloid|denpa|luk thung|opm\b|pinoy|dangdut|indonesian pop|mor lam"),
    ("metal", "Metal", r"deathgrind|metal|grindcore|deathcore|djent|doom|sludge|thrash|black ?gaze|nwobhm|death-doom|goregrind"),
    ("hiphop", "Hip hop", r"hip.?hop|\brap\b|rapping|trap\b|trap music|gangsta|drill|grime|horrorcore|crunk|dirty south|g-funk|boom bap|"
                          r"nerdcore|hyphy|phonk|mumble|bounce music|turntablism|chopped|cloud rap|emo rap|pop rap|uk rap|french hip|afro trap|latin trap"),
    ("latin", "Latin", r"andean|timba|habanera|brega|urbano|latin|salsa|reggaeton|tango|bossa|samba|cumbia|bachata|merengue|bolero|ranchera|mariachi|norteño|banda\b|corrido|"
                       r"sertanejo|forró|axé|pagode|choro|m[uú]sica popular brasileira|mpb|brazil|mexic|cuban|son cubano|son jarocho|"
                       r"tropical|vallenato|nueva canción|nueva trova|trova|tejano|duranguense|grupero|bachata|chicha|"
                       r"música|cueca|chamamé|zamba|candombe|murga|plena|bomba|mambo|cha-cha|(?<!congolese )rumba|guaracha|danzón|frevo|funk carioca|"
                       r"baião|tecnobrega|lambada|guajira|huayno|peruvian|chilean|argentin|colombian|venezuel|puerto ric|dominican|regional mexican"),
    ("reggae", "Reggae, Caribbean and African popular", r"maloya|\bsega\b|gwo ka|biguine|konpa|reggae|dancehall|\bska\b|rocksteady|\bdub\b|dub music|calypso|soca|mento|kompa|"
                                                        r"afrobeat|afro-?pop|afropop|highlife|juju|jùjú|fuji|soukous|rumba congolaise|"
                                                        r"ndombolo|makossa|mbalax|bongo flava|kwaito|amapiano|gqom|taarab|benga|chimurenga|"
                                                        r"music of africa|african(?!-american)|congolese|zouk|kizomba|zouglou|coupé-décalé|azonto|hiplife|genge|mbaqanga|isicathamiya|"
                                                        r"marabi|gnawa|ra[iï]\b|music of the caribbean|caribbean|lovers rock|ragga|roots reggae"),
    ("country", "Country", r"country|bluegrass|americana|honky|old-time|cajun|zydeco|western swing|outlaw|rockabilly|cowboy|appalachian|"
                           r"red dirt|nashville|hillbilly|dansband"),
    ("jazz", "Jazz", r"jazz|(?<!new jack )swing|bebop|bop\b|big band|dixieland|ragtime|boogie|free improvisation|fusion|scat|stride|third stream|"
                     r"m-base|manouche|gypsy jazz"),
    ("rnb", "R&B, soul, blues and gospel", r"r&b|rhythm and blues|soul|blues|gospel|funk|motown|doo-?wop|new jack|quiet storm|urban contemporary|"
                                           r"spiritual|contemporary christian|christian music|praise|worship|go-go|northern soul|disco funk"),
    ("electronic", "Electronic and dance", r"electro|house|techno|trance|dubstep|drum and bass|jungle|ambient|edm|\bidm\b|intelligent dance|"
                                           r"rave|chill-?out|freestyle music|breakbeat|big beat|disco|eurodance|hardstyle|hardcore techno|gabber|uk garage|speed garage|garage house|"
                                           r"synth ?wave|vaporwave|chillwave|downtempo|trip hop|chiptune|industrial music|ebm|electronic body|"
                                           r"dance music|club music|witch house|glitch|bass music|footwork|future bass|moombahton|"
                                           r"new age|lo-fi|electronica|italo|hi-nrg|eurobeat|dark ambient|drone|noise music|electroacoustic|"
                                           r"musique concr|tape music|computer music|video game music|psytrance|goa"),
    ("rock", "Rock and punk", r"psychobilly|coldwave|queercore|prog|no wave|skiffle|ethereal wave|powerviolence|rock|punk|grunge|indie|new wave|shoegaze|emo\b|emo pop|screamo|post-hardcore|hardcore|britpop|"
                              r"garage|surf|psychedel|krautrock|beat music|merseybeat|mod\b|power pop|dream pop|noise pop|"
                              r"post-punk|gothic|goth|dark ?wave|cold wave|oi!|crust|skate|math|stoner|space rock|jangle|"
                              r"alternative|independent music|lo-fi|neue deutsche|madchester|baggy|twee|riot grrrl|sadcore|slowcore"),
    ("classical", "Classical and opera", r"byzantine|minimalist music|classical|opera|operetta|zarzuela|symphon|baroque(?! pop)|romantic music|renaissance music|medieval music|"
                                         r"early music|chamber music|choral|oratorio|cantata|requiem|mass\b|liturg|sacred music|church music|"
                                         r"religious music|art music|art song|lied\b|lieder|ballet|concerto|sonata|string quartet|"
                                         r"^contemporary music$|avant-garde music|serial|minimal music|minimalism|neoclassic|impressionis|"
                                         r"film score|incidental music|program music|musical theatre|musical play|musical\b|"
                                         r"carnatic|hindustani|indian classical|gregorian|polyphon|madrigal|motet|organ music|piano music|"
                                         r"orchestral|instrumental music|experimental music|spectral|aleatoric|twelve-tone|atonal|"
                                         r"contemporary classical|vocal music|a cappella|chant|hymn|plainsong|sacred harp"),
    ("pop", "Pop", r"adult contemporary|pop|schlager|chanson|estrada|ballad|easy listening|middle of the road|adult contemporary|teen|bubblegum|"
                   r"variety|light music|popular music|^song$|singer-songwriter|cabaret|music hall|vaudeville|crooner|lounge|"
                   r"exotica|yé-yé|canzone|laïko|chalga|turbo-folk|disco polo|sentimental|romance|arabesk|filmi|playback|"
                   r"bollywood|indian film music|bhangra|levenslied|kleinkunst|liedermacher|novelty|comedy|children"),
    ("folk", "Folk and traditional", r"hasidic|khaliji|éntekhno|volkst|sevdalinka|folk|traditional|world music|celtic|music of|sardana|flamenco|fado|rebetiko|klezmer|romani|gypsy|"
                                     r"polka|bard|ashik|mugham|maqam|qawwali|sufi|nasheed|arabic|persian|turkish|throat|joik|yoik|"
                                     r"kantele|tamburica|fiddle|bagpipe|pibroch|sean-nós|shanty|sea shant|bertso|volksmusik|"
                                     r"narodn|visa\b|bylina|kobzar|duma|fandango|jota|copla|cante|sevillanas|mizrahi|"
                                     r"chaabi|andalusi|griot|kirtan|bhajan|qawwal|ghazal|thumri|bhangra|lavani|baul|"
                                     r"min'yō|minyo|gagaku|p'ansori|pansori|guqin|kunqu|peking opera|cantonese opera|"
                                     r"acoustic|americana|old-time|dance hall|ceilidh|morris|bluegrass|ethnic|indigenous|tribal|aboriginal|"
                                     r"tango|choro|joropo|gaita|tarantella|canzone napoletana|neapolitan|schrammel|alpine|jodel|yodel"),
]
OCC_NAMES = {k: n for k, n, _ in OCC_FAM}
GEN_NAMES = {k: n for k, n, _ in GEN_FAM}
OCC_NAMES["other"] = "Other musicians"
GEN_NAMES["other"] = "Other or unlabelled genre"


def classify(label, rules):
    s = (label or "").lower().strip()
    if not s:
        return "other"
    for k, _, rx in rules:
        if re.search(rx, s):
            return k
    return "other"


def read_tsv(path):
    out = []
    for ln in open(path, encoding="utf-8").read().split("\n")[1:]:
        p = ln.split("\t")
        if p and p[0].startswith("Q"):
            out.append(p)
    return out


def unq(s):
    s = (s or "").strip()
    return s[1:-1].replace('\\"', '"') if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s


def occupations():
    rows = read_tsv(f"{RAW4}/music_occupations.tsv")
    m = {}
    for p in rows:
        lab = unq(p[1]) if len(p) > 1 else ""
        fam = classify(lab, OCC_FAM)
        if fam == "other" and lab and re.search(OCC_FAM[0][2], lab.lower()) is None:
            fam = "other"
        m[p[0]] = (lab, fam)
    # the root class itself and plain 'musician' are 'other'
    return m


def genres():
    rows = read_tsv(f"{RAW4}/genre_labels.tsv")
    return {p[0]: (unq(p[1]) if len(p) > 1 else "", classify(unq(p[1]) if len(p) > 1 else "", GEN_FAM)) for p in rows}


if __name__ == "__main__":
    OM = occupations(); GM = genres()
    # usage counts (people per occupation is counted in the parse step; here: rows in the musicians export, if present)
    occ_use = Counter()
    try:
        for ln in open(f"{RAW4}/musicians.tsv", encoding="utf-8"):
            p = ln.split("\t")
            if len(p) >= 9 and p[0].startswith("Q"):
                occ_use[p[2]] += 1
    except FileNotFoundError:
        pass
    gen_use = Counter()
    for f in ("musician_genres.tsv", "band_genres.tsv"):
        for p in read_tsv(f"{RAW4}/{f}"):
            if len(p) > 1:
                gen_use[p[1].strip()] += 1
    with open(f"{DATA}/occupation_families.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["occupation_wikidata", "occupation", "family", "family_name", "rows_in_musicians_export"])
        for q, (lab, fam) in sorted(OM.items(), key=lambda kv: -occ_use[kv[0]]):
            w.writerow([q, lab, fam, OCC_NAMES[fam], occ_use[q]])
    with open(f"{DATA}/genre_families.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["genre_wikidata", "genre", "family", "family_name", "links"])
        for q in sorted(set(GM) | set(gen_use), key=lambda q: -gen_use[q]):
            lab, fam = GM.get(q, ("", "other"))
            w.writerow([q, lab, fam, GEN_NAMES[fam], gen_use[q]])
    oc = Counter(); gc = Counter()
    for q, (lab, fam) in OM.items(): oc[fam] += occ_use[q]
    for q, n in gen_use.items(): gc[GM.get(q, ("", "other"))[1]] += n
    print("occupation rows by family", oc.most_common())
    print("genre links by family", gc.most_common())
