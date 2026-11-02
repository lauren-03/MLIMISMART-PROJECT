# -*- coding: utf-8 -*-
"""Tea farming knowledge base for MlimiSmart, in English and Chichewa."""

TOPICS = [
    "fertilizer", "plucking", "pruning", "pest_disease",
    "harvest", "weather", "planting", "shade", "general",
]

# Seed content for the knowledge_items table. The admin can add to this
# through the admin dashboard; these rows are the starting body of knowledge.
KNOWLEDGE_SEED: list[dict] = [
    {
        "topic": "fertilizer",
        "season": "rainy",
        "title_en": "Fertilizer application in tea",
        "title_ny": "Kuthira fetereza mu tiyi",
        "body_en": (
            "Apply fertilizer when the soil is moist but not waterlogged. Split the "
            "yearly rate into two or three applications during the rainy season "
            "(December to March). Broadcast it evenly in a band along the plucking "
            "table edge, never against the stem. Avoid applying immediately before "
            "heavy rain, because the nutrients are washed away and the money is lost."
        ),
        "body_ny": (
            "Thirani fetereza pamene nthaka ili yonyowa koma osati yodzaza ndi madzi. "
            "Gawani fetereza wa chaka chonse maulendo awiri kapena atatu m'nyengo ya "
            "mvula (Disembala mpaka Malichi). Mwazani mofanana m'mbali mwa mizere ya "
            "tiyi, osati pa tsinde. Pewani kuthira fetereza mvula yaikulu isanayambe, "
            "chifukwa mankhwala amakokoloka ndipo ndalama zimatayika."
        ),
    },
    {
        "topic": "plucking",
        "season": "all",
        "title_en": "Plucking cycle and leaf standard",
        "title_ny": "Nyengo ya kusenda ndi mtundu wa masamba",
        "body_en": (
            "Keep to a 10 to 11 day plucking round. Pluck two leaves and a bud only. "
            "Plucking coarse leaf, or going beyond the round, lowers the grade the "
            "factory pays for. Do not pack wet leaf tightly into the basket, and "
            "deliver to the buying centre the same day so the leaf does not heat up."
        ),
        "body_ny": (
            "Sungani nyengo ya kusenda ya masiku 10 mpaka 11. Sendani masamba awiri "
            "ndi phukusi lokha. Kusenda masamba akuluakulu kapena kuchedwa kupitirira "
            "nyengo kumachepetsa mtengo umene fakitale imalipira. Osathina masamba "
            "onyowa mu dengu, ndipo tengerani ku malo ogulira tsiku lomwelo kuti "
            "masamba asatenthe."
        ),
    },
    {
        "topic": "pruning",
        "season": "dry",
        "title_en": "Pruning and tipping",
        "title_ny": "Kutema ndi kukonza pamwamba",
        "body_en": (
            "Prune at the end of the rains or in the cool dry season (May to July) "
            "when the bush has reserves, not during a dry spell or extreme heat. Use "
            "a sharp, clean saw or knife and cut at a slight angle so water runs off. "
            "After pruning, allow the bush to recover and tip in at the correct height "
            "before returning it to the plucking round."
        ),
        "body_ny": (
            "Temani mvula ikatha kapena m'nyengo yozizira youma (Meyi mpaka Julayi) "
            "pamene chitsamba chili ndi mphamvu, osati nthawi ya chilala kapena "
            "kutentha kwambiri. Gwiritsani ntchito nkhwangwa kapena mpeni wakuthwa "
            "ndi waukhondo, ndipo dulani mozondoka kuti madzi asatsalire. Mukatema, "
            "lekani chitsamba chichire ndipo konzani pamwamba pa msinkhu woyenera "
            "chisanabwerere ku kusenda."
        ),
    },
    {
        "topic": "pest_disease",
        "season": "all",
        "title_en": "Pests and diseases in tea",
        "title_ny": "Tizilombo ndi matenda a tiyi",
        "body_en": (
            "Walk your field every week and look under the leaves. Red spider mite "
            "builds up in hot dry weather; thrips and mosquito bug damage young shoots; "
            "long wet spells encourage root and leaf diseases. Remove and burn badly "
            "affected material, keep the field weeded so air can move, and report "
            "unusual damage to your extension officer or buying centre before spraying, "
            "so you use the correct chemical at the correct dose."
        ),
        "body_ny": (
            "Yendani m'munda wanu sabata iliyonse ndipo yang'anani pansi pa masamba. "
            "Kangaude wofiira amachuluka nthawi yotentha youma; thrips ndi udzudzu wa "
            "tiyi amawononga mphukira; mvula yambiri yotalikirapo imayambitsa matenda "
            "a mizu ndi masamba. Chotsani ndi kutentha zomera zowonongeka kwambiri, "
            "chotsani udzu kuti mpweya uzizungulira, ndipo uzani kapitao kapena malo "
            "ogulira musanapopere, kuti mugwiritse mankhwala oyenera ndi muyeso woyenera."
        ),
    },
    {
        "topic": "harvest",
        "season": "all",
        "title_en": "Harvest planning and leaf quality",
        "title_ny": "Kukonzekera kokolola ndi khalidwe la masamba",
        "body_en": (
            "Plan your plucking so the leaf reaches the buying centre on the same day "
            "it is picked. Keep baskets in the shade while you work, never in direct "
            "sun or closed sacks. Peak cropping is during the rains, so arrange labour "
            "in advance for that period; the dry season crop is lighter and the round "
            "can be slightly longer."
        ),
        "body_ny": (
            "Konzekerani kusenda kuti masamba akafike ku malo ogulira tsiku lomwelo "
            "limene mwawasenda. Sungani madengu pa mthunzi mukamagwira ntchito, osati "
            "pa dzuwa kapena m'matumba otsekedwa. Tiyi amachuluka m'nyengo ya mvula, "
            "choncho konzani antchito nthawi isanakwane; m'nyengo youma masamba "
            "amachepa ndipo nyengo ya kusenda ingatalikire pang'ono."
        ),
    },
    {
        "topic": "weather",
        "season": "all",
        "title_en": "Using the weather forecast on your farm",
        "title_ny": "Kugwiritsa ntchito nkhani ya nyengo m'munda wanu",
        "body_en": (
            "Check the forecast before you buy or apply inputs. Heavy rain washes away "
            "fertilizer and sprays; hot dry weather stresses young plants and favours "
            "mite build-up; strong wind damages shoots on exposed fields. Planning work "
            "two or three days ahead using the forecast saves both labour and inputs."
        ),
        "body_ny": (
            "Onani nkhani ya nyengo musanagule kapena kuthira mankhwala. Mvula yaikulu "
            "imakokolola fetereza ndi mankhwala opopera; kutentha kouma kumavutitsa "
            "mbewu zazing'ono ndipo kumathandiza kangaude kuchuluka; mphepo yamphamvu "
            "imawononga mphukira m'minda yopanda chitetezo. Kukonzekera ntchito masiku "
            "awiri kapena atatu pasadakhale kumapulumutsa antchito ndi mankhwala."
        ),
    },
    {
        "topic": "planting",
        "season": "rainy",
        "title_en": "Planting and infilling",
        "title_ny": "Kubzala ndi kukwaniritsa mipata",
        "body_en": (
            "Plant at the start of the rains once the soil is thoroughly wet, so the "
            "young plants establish before any dry spell. Use healthy nursery plants "
            "from a recognised source, keep to the recommended spacing, and firm the "
            "soil around each plant. Fill gaps in old fields during the same period "
            "rather than leaving the land bare to erosion."
        ),
        "body_ny": (
            "Bzalani mvula ikangoyamba nthaka itanyowa bwino, kuti mbewu zazing'ono "
            "zikhazikike chilala chisanafike. Gwiritsani ntchito mbewu zathanzi "
            "zochokera ku nazale yodziwika, sungani mipata yoyenera, ndipo "
            "limbikitsani nthaka mozungulira mbewu iliyonse. Kwaniritsani mipata "
            "m'minda yakale nthawi imodzimodziyi, osati kusiya nthaka yopanda kanthu "
            "kuti isakokoloke."
        ),
    },
    {
        "topic": "shade",
        "season": "all",
        "title_en": "Shade trees and soil cover",
        "title_ny": "Mitengo ya mthunzi ndi chophimba nthaka",
        "body_en": (
            "Well spaced shade trees reduce heat stress on the bush and cut moisture "
            "loss in the dry season. Thin the shade before the rains so the field does "
            "not stay too wet and dark. Keep mulch or a cover on bare soil between "
            "young plants to hold moisture and stop erosion on slopes."
        ),
        "body_ny": (
            "Mitengo ya mthunzi yoikidwa bwino imachepetsa kutentha pa chitsamba "
            "ndipo imachepetsa kutayika kwa chinyezi m'nyengo youma. Chepetsani "
            "mthunzi mvula isanayambe kuti munda usakhale wonyowa ndi wamdima "
            "kwambiri. Ikani udzu wophimba nthaka pakati pa mbewu zazing'ono kuti "
            "chinyezi chikhale ndipo nthaka isakokoloke m'matalala."
        ),
    },
]

# Bilingual strings the backend itself emits (SMS replies, advisory headings).
# The React app keeps its own copy for interface labels.
MESSAGES: dict[str, dict[str, str]] = {
    "greeting": {
        "EN": "MlimiSmart tea advice",
        "NY": "Uphungu wa tiyi wa MlimiSmart",
    },
    "weather_today": {
        "EN": "Weather today",
        "NY": "Nyengo lero",
    },
    "no_topic": {
        "EN": (
            "I can advise on fertilizer, plucking, pruning, pests and diseases, "
            "harvesting and the weather. Please send one of those words, or ask "
            "your question again in a few words."
        ),
        "NY": (
            "Ndingakuthandize pa fetereza, kusenda, kutema, tizilombo ndi matenda, "
            "kokolola ndi nyengo. Tumizani limodzi la mawu amenewa, kapena "
            "funsani funso lanu mwachidule."
        ),
    },
    "sms_help": {
        "EN": (
            "MlimiSmart: send FERTILIZER, PLUCKING, PRUNING, PESTS, HARVEST or "
            "WEATHER, or ask any question. CALENDAR = this month's work. "
            "ALERTS ON = weather warnings. AREA Luchenza = set your area. "
            "LANG NY = Chichewa."
        ),
        "NY": (
            "MlimiSmart: tumizani FETEREZA, KUSENDA, KUTEMA, TIZILOMBO, KOKOLOLA "
            "kapena NYENGO, kapena funsani funso. KALENDALA = ntchito za mwezi uno. "
            "CHENJEZO INDE = machenjezo a nyengo. DERA Luchenza = dera lanu. "
            "LANG EN = Chingerezi."
        ),
    },
    "language_set_en": {
        "EN": "Your MlimiSmart language is now English.",
        "NY": "Your MlimiSmart language is now English.",
    },
    "language_set_ny": {
        "EN": "Chilankhulo chanu cha MlimiSmart tsopano ndi Chichewa.",
        "NY": "Chilankhulo chanu cha MlimiSmart tsopano ndi Chichewa.",
    },
    "registered_prompt": {
        "EN": (
            "Welcome to MlimiSmart. Reply with your district (Thyolo or Mulanje) "
            "to get advice for your area."
        ),
        "NY": (
            "Takulandirani ku MlimiSmart. Yankhani ndi dera lanu (Thyolo kapena "
            "Mulanje) kuti mupeze uphungu wa dera lanu."
        ),
    },
}


def msg(key: str, language: str) -> str:
    return MESSAGES[key].get(language, MESSAGES[key]["EN"])


def knowledge_for(topic: str, language: str) -> str:
    for item in KNOWLEDGE_SEED:
        if item["topic"] == topic:
            return item["body_ny"] if language == "NY" else item["body_en"]
    return msg("no_topic", language)
