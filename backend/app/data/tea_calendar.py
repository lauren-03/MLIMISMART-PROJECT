# -*- coding: utf-8 -*-
"""Month-by-month tea farming calendar for Thyolo and Mulanje."""

MONTHS: list[dict] = [
    {
        "month": 1, "season": "rainy",
        "name_en": "January", "name_ny": "Januwale",
        "focus_en": "Peak crop - pluck often and finish fertilizer.",
        "focus_ny": "Nthawi ya zokolola zambiri - senderani pafupipafupi ndipo malizani fetereza.",
        "tasks": [
            ("basket", "Pluck every 7 days: two leaves and a bud.",
             "Senderani masiku 7 aliwonse: masamba awiri ndi mphukira."),
            ("droplet", "Apply the second split of fertilizer when the soil is moist, not waterlogged.",
             "Thirani gawo lachiwiri la fetereza nthaka ili yonyowa, osati yodzaza madzi."),
            ("tree", "Fill gaps by planting new tea plants while rains are steady.",
             "Dzazani malo opanda tiyi pobzala mbande pamene mvula ikugwa bwino."),
            ("water", "Clear drains so water does not stand in the field.",
             "Konzani ngalande kuti madzi asaime m'munda."),
        ],
    },
    {
        "month": 2, "season": "rainy",
        "name_en": "February", "name_ny": "Febuluwale",
        "focus_en": "Keep plucking rounds short and the field weed free.",
        "focus_ny": "Pitirizani kusenda pafupipafupi ndipo munda ukhale wopanda udzu.",
        "tasks": [
            ("basket", "Keep a 7 to 10 day plucking round; do not let shoots grow too long.",
             "Senderani masiku 7 mpaka 10 aliwonse; musalole mphukira kutalika kwambiri."),
            ("scissors", "Weed by hand or slashing; avoid digging that damages tea roots.",
             "Palirani ndi manja kapena kusenga; musakumbe kwambiri kuopa kuononga mizu ya tiyi."),
            ("bug", "Check for wilting bushes and white fungus at the stem base (root rot).",
             "Yang'anani zitsamba zofota ndi bowa woyera pansi pa tsinde (kuola kwa mizu)."),
        ],
    },
    {
        "month": 3, "season": "rainy",
        "name_en": "March", "name_ny": "Malichi",
        "focus_en": "Last strong rains - plant shade trees and look after drains.",
        "focus_ny": "Mvula yomaliza yamphamvu - bzalani mitengo yamthunzi ndi kusamalira ngalande.",
        "tasks": [
            ("tree", "Plant shade trees in gaps while the soil is still wet.",
             "Bzalani mitengo yamthunzi m'malo opanda kanthu nthaka ikadali yonyowa."),
            ("basket", "Continue regular plucking; record your kilograms each round.",
             "Pitirizani kusenda; lembani makilogalamu anu nthawi iliyonse."),
            ("water", "Repair soil erosion channels before the dry season.",
             "Konzani malo okokoloka nthaka nyengo youma isanafike."),
        ],
    },
    {
        "month": 4, "season": "rainy",
        "name_en": "April", "name_ny": "Epulo",
        "focus_en": "Rains are ending - start keeping moisture in the soil.",
        "focus_ny": "Mvula ikutha - yambani kusunga chinyezi m'nthaka.",
        "tasks": [
            ("layers", "Spread mulch (grass or prunings) between rows to keep the soil moist.",
             "Yalani udzu kapena nthambi pakati pa mizere kuti nthaka isunge chinyezi."),
            ("basket", "Plucking rounds can lengthen to 10 to 14 days as growth slows.",
             "Mungathe kusenda masiku 10 mpaka 14 aliwonse chifukwa kukula kukuchepa."),
            ("clipboard", "Plan which fields will be pruned in June to August.",
             "Konzani minda yomwe mudzatema mu Juni mpaka Ogasiti."),
        ],
    },
    {
        "month": 5, "season": "cool_dry",
        "name_en": "May", "name_ny": "Meyi",
        "focus_en": "Growth slows - prepare tools and soil.",
        "focus_ny": "Kukula kukuchepa - konzani zipangizo ndi nthaka.",
        "tasks": [
            ("tools", "Sharpen pruning knives and repair baskets.",
             "Nolani mipeni yotemera ndi kukonza mabasiketi."),
            ("clipboard", "Take a soil sample to your extension officer for fertilizer advice.",
             "Tengani dothi lanu kwa alangizi a zaulimi kuti akupatseni uphungu wa fetereza."),
            ("basket", "Light plucking only; leave enough leaves for the bush to rest.",
             "Senderani pang'ono; siyani masamba okwanira kuti chitsamba chipume."),
        ],
    },
    {
        "month": 6, "season": "cool_dry",
        "name_en": "June", "name_ny": "Juni",
        "focus_en": "Pruning season begins.",
        "focus_ny": "Nyengo yotema ikuyamba.",
        "tasks": [
            ("scissors", "Prune bushes that are due (usually every 3 to 4 years) with clean, sloping cuts.",
             "Temani zitsamba zomwe nthawi yake yakwana (zaka 3 mpaka 4 zilizonse) modula bwino mopendeka."),
            ("layers", "Leave prunings on the ground as mulch unless they are diseased.",
             "Siyani nthambi zotemedwa pansi ngati malichi pokhapokha ngati zili ndi matenda."),
            ("fire", "Remove and burn wood with black crust or rot (wood rot).",
             "Chotsani ndi kutentha nthambi zakuda kapena zowola (kuola kwa nthambi)."),
        ],
    },
    {
        "month": 7, "season": "cool_dry",
        "name_en": "July", "name_ny": "Julayi",
        "focus_en": "Main pruning month - cold and dry.",
        "focus_ny": "Mwezi waukulu wotema - kuzizira ndi kouma.",
        "tasks": [
            ("scissors", "Continue pruning; finish before the hot weather in September.",
             "Pitirizani kutema; malizani nyengo yotentha ya Seputembala isanafike."),
            ("tree", "Prepare a nursery: cuttings from good mother bushes.",
             "Konzani nazale: zidutswa kuchokera ku zitsamba zabwino."),
            ("thermometer", "Watch low-lying fields on very cold mornings.",
             "Yang'anani minda ya m'zigwa m'mawa wozizira kwambiri."),
        ],
    },
    {
        "month": 8, "season": "cool_dry",
        "name_en": "August", "name_ny": "Ogasiti",
        "focus_en": "Finish pruning and protect the field from fire.",
        "focus_ny": "Malizani kutema ndi kuteteza munda ku moto.",
        "tasks": [
            ("scissors", "Complete all pruning this month.",
             "Malizani kutema konse mwezi uno."),
            ("fire", "Clear firebreaks around your field.",
             "Konzani njira zoletsa moto kuzungulira munda wanu."),
            ("layers", "Add mulch before the hot dry season.",
             "Onjezerani malichi nyengo yotentha isanafike."),
        ],
    },
    {
        "month": 9, "season": "hot_dry",
        "name_en": "September", "name_ny": "Seputembala",
        "focus_en": "Hot and dry - protect bushes from stress and mites.",
        "focus_ny": "Kotentha ndi kouma - tetezani zitsamba ku kutentha ndi nthata.",
        "tasks": [
            ("bug", "Check mature leaves for a bronze colour and fine webs (red spider mite).",
             "Yang'anani masamba akulu ngati ali ndi mtundu wa mkuwa ndi ukonde (nthata zofiira)."),
            ("water", "Water young plants if you can; mulch around them.",
             "Thirirani mbande ngati mungathe; ikani malichi mozungulira."),
            ("droplet", "Do not apply fertilizer on dry soil - wait for the rains.",
             "Musathire fetereza pa nthaka youma - dikirani mvula."),
        ],
    },
    {
        "month": 10, "season": "hot_dry",
        "name_en": "October", "name_ny": "Okutobala",
        "focus_en": "Hottest month - prepare for the rains.",
        "focus_ny": "Mwezi wotentha kwambiri - konzekerani mvula.",
        "tasks": [
            ("cart", "Buy fertilizer early so it is ready when the rains start.",
             "Gulani fetereza msanga kuti ikhale yokonzeka mvula ikayamba."),
            ("shovel", "Dig planting holes for new tea and shade trees.",
             "Kumbani maenje obzalira tiyi watsopano ndi mitengo yamthunzi."),
            ("sun", "Keep shade trees; do not prune tea in this heat.",
             "Sungani mitengo yamthunzi; musateme tiyi kotentha kotere."),
        ],
    },
    {
        "month": 11, "season": "rainy",
        "name_en": "November", "name_ny": "Novembala",
        "focus_en": "Rains start - first fertilizer and plucking resumes.",
        "focus_ny": "Mvula ikuyamba - fetereza yoyamba ndipo kusenda kukuyambanso.",
        "tasks": [
            ("droplet", "Apply the first fertilizer split after good rain has soaked the soil.",
             "Thirani gawo loyamba la fetereza mvula yabwino ikanyowetsa nthaka."),
            ("basket", "Restart regular plucking as new shoots appear.",
             "Yambaninso kusenda pafupipafupi pamene mphukira zatsopano zikutuluka."),
            ("water", "Open and clean drains before heavy rain.",
             "Tsegulani ndi kukonza ngalande mvula yamphamvu isanafike."),
        ],
    },
    {
        "month": 12, "season": "rainy",
        "name_en": "December", "name_ny": "Disembala",
        "focus_en": "Planting time and strong growth.",
        "focus_ny": "Nthawi yobzala ndi kukula kwamphamvu.",
        "tasks": [
            ("tree", "Plant new tea and shade trees once rains are well established.",
             "Bzalani tiyi watsopano ndi mitengo yamthunzi mvula ikakhazikika."),
            ("basket", "Pluck every 7 to 10 days; keep the plucking table level.",
             "Senderani masiku 7 mpaka 10 aliwonse; sungani pamwamba pa zitsamba pofanana."),
            ("scissors", "Weed regularly; weeds compete with tea for fertilizer.",
             "Palirani pafupipafupi; udzu umalimbirana fetereza ndi tiyi."),
        ],
    },
]


def month_entry(month: int, language: str = "EN") -> dict:
    """One month, shaped for the API in the requested language."""
    raw = MONTHS[(month - 1) % 12]
    ny = language == "NY"
    return {
        "month": raw["month"],
        "season": raw["season"],
        "name": raw["name_ny"] if ny else raw["name_en"],
        "focus": raw["focus_ny"] if ny else raw["focus_en"],
        "tasks": [
            {"icon": icon, "text": text_ny if ny else text_en}
            for icon, text_en, text_ny in raw["tasks"]
        ],
    }


def month_text(month: int, language: str = "EN") -> str:
    """Plain text version for SMS and USSD."""
    entry = month_entry(month, language)
    tasks = " ".join(f"{i}. {task['text']}" for i, task in enumerate(entry["tasks"], 1))
    return f"{entry['name'].upper()}: {entry['focus']} {tasks}"
