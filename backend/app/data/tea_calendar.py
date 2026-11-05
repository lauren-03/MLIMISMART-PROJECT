# -*- coding: utf-8 -*-
"""Month-by-month tea farming calendar for Thyolo and Mulanje.

The field operations follow the Tea Research Association Planters' Calendar,
shifted six months. That calendar is written for Assam in the northern
hemisphere, where the monsoon falls in June to September; Malawi's rains fall
in November to April, so each operation is placed in the Malawian month that
matches the same point in the growing year, not the same month number.
"""

MONTHS: list[dict] = [
    {
        "month": 1, "season": "rainy",
        "name_en": "January", "name_ny": "Januwale",
        "focus_en": "Peak crop - pluck often and finish the fertilizer.",
        "focus_ny": "Nthawi ya zokolola zambiri - thyolani pafupipafupi ndipo malizani fetereza.",
        "tasks": [
            ("basket", "Pluck every 7 days: two leaves and a bud.",
             "Thyolani masiku 7 aliwonse: masamba awiri ndi mphukira."),
            ("droplet", "Apply the second split of fertilizer when the soil is moist, not waterlogged.",
             "Thirani gawo lachiwiri la fetereza nthaka ili yonyowa, osati yodzaza madzi."),
            ("water", "Keep drains flowing freely; standing water weakens the bushes.",
             "Onetsetsani kuti ngalande zikuyenda; madzi oima amafooketsa zitsamba."),
            ("leaf", "On weak or waterlogged patches, use a foliar feed rather than more soil fertilizer.",
             "M'malo ofooka kapena odzaza madzi, popererani mankhwala pamasamba m'malo mowonjezera fetereza wa m'nthaka."),
            ("tree", "Fill gaps by planting new tea while the rains are steady.",
             "Dzazani malo opanda tiyi pobzala mbande pamene mvula ikugwa bwino."),
        ],
    },
    {
        "month": 2, "season": "rainy",
        "name_en": "February", "name_ny": "Febuluwale",
        "focus_en": "Keep plucking rounds short and the field weed free.",
        "focus_ny": "Pitirizani kuthyola pafupipafupi ndipo munda ukhale wopanda udzu.",
        "tasks": [
            ("basket", "Keep a 7 to 10 day plucking round; do not let shoots grow too long.",
             "Thyolani masiku 7 mpaka 10 aliwonse; musalole mphukira kutalika kwambiri."),
            ("scissors", "Weed a second time by hand or slashing; avoid digging that damages tea roots.",
             "Palirani kachiwiri ndi manja kapena kusenga; musakumbe kwambiri kuopa kuononga mizu ya tiyi."),
            ("water", "Walk the drains after heavy rain and clear any silt.",
             "Yendererani ngalande mvula yamphamvu ikagwa ndipo chotsani matope."),
            ("bug", "Check for wilting bushes and white fungus at the stem base (root rot).",
             "Yang'anani zitsamba zofota ndi bowa woyera pansi pa tsinde (kuola kwa mizu)."),
        ],
    },
    {
        "month": 3, "season": "rainy",
        "name_en": "March", "name_ny": "Malichi",
        "focus_en": "Last strong rains - finish feeding and stop weeds seeding.",
        "focus_ny": "Mvula yomaliza yamphamvu - malizani kudyetsa ndi kuletsa udzu kubala mbewu.",
        "tasks": [
            ("droplet", "Finish the last split of fertilizer this month while the soil still holds moisture.",
             "Malizani gawo lomaliza la fetereza mwezi uno nthaka ikadali ndi chinyezi."),
            ("scissors", "Cut weeds at ground level before they flower and seed.",
             "Dulani udzu pafupi ndi nthaka usanaphuke ndi kubala mbewu."),
            ("tree", "Plant shade trees in gaps while the soil is still wet.",
             "Bzalani mitengo yamthunzi m'malo opanda kanthu nthaka ikadali yonyowa."),
            ("layers", "Spread mulch around young tea to hold the moisture that is left.",
             "Yalani malichi mozungulira tiyi wamng'ono kuti chinyezi chotsala chisathe."),
            ("basket", "Continue regular plucking; record your kilograms each round.",
             "Pitirizani kuthyola; lembani makilogalamu anu nthawi iliyonse."),
        ],
    },
    {
        "month": 4, "season": "rainy",
        "name_en": "April", "name_ny": "Epulo",
        "focus_en": "Rains are ending - keep moisture in the soil.",
        "focus_ny": "Mvula ikutha - sungani chinyezi m'nthaka.",
        "tasks": [
            ("layers", "Spread mulch (grass or prunings) between rows to keep the soil moist.",
             "Yalani udzu kapena nthambi pakati pa mizere kuti nthaka isunge chinyezi."),
            ("basket", "Plucking rounds can lengthen to 10 to 14 days as growth slows.",
             "Mungathe kuthyola masiku 10 mpaka 14 aliwonse chifukwa kukula kukuchepa."),
            ("leaf", "If the bush looks thin, leave one extra leaf when plucking so it can feed itself.",
             "Ngati chitsamba chikuoneka chopyapyala, siyani tsamba limodzi lowonjezera mukamathyola kuti chidzidyetse."),
            ("clipboard", "Plan which fields will be pruned from June to August.",
             "Konzani minda yomwe mudzatema kuyambira Juni mpaka Ogasiti."),
            ("water", "Repair erosion channels before the dry season.",
             "Konzani malo okokoloka nthaka nyengo youma isanafike."),
        ],
    },
    {
        "month": 5, "season": "cool_dry",
        "name_en": "May", "name_ny": "Meyi",
        "focus_en": "Growth slows - test the soil and prepare tools.",
        "focus_ny": "Kukula kukuchepa - yesani nthaka ndi kukonza zipangizo.",
        "tasks": [
            ("clipboard", "Take a soil sample now; the result decides next season's fertilizer.",
             "Tengani dothi tsopano; zotsatira zake zidzasankha fetereza wa nyengo ikubwera."),
            ("tools", "Sharpen pruning knives and saws, and repair baskets.",
             "Nolani mipeni ndi macheka otemera, ndipo konzani madengu."),
            ("basket", "Light plucking only; leave enough leaves for the bush to rest.",
             "Thyolani pang'ono; siyani masamba okwanira kuti chitsamba chipume."),
            ("tree", "Finish any planting left over from the rains.",
             "Malizani kubzala kulikonse kotsalira kuchokera ku nyengo ya mvula."),
        ],
    },
    {
        "month": 6, "season": "cool_dry",
        "name_en": "June", "name_ny": "Juni",
        "focus_en": "Pruning season begins - and open the drains while it is dry.",
        "focus_ny": "Nyengo yotema ikuyamba - ndipo konzani ngalande kukadali kouma.",
        "tasks": [
            ("scissors", "Prune bushes that are due (usually every 3 to 4 years) with clean, sloping cuts.",
             "Temani zitsamba zomwe nthawi yake yakwana (zaka 3 mpaka 4 zilizonse) modula bwino mopendeka."),
            ("water", "Deepen and re-shape the drains now, before the next rains arrive.",
             "Kuzani ndi kukonzanso ngalande tsopano, mvula ina isanafike."),
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
            ("leaf", "On bushes not due for a full prune, cut only the top growth level (a light trim).",
             "Pa zitsamba zomwe sizikufuna kutemedwa kotheratu, dulani pamwamba pokha kuti pafanane."),
            ("bug", "Wash the cut frames and treat for termites while the bush is open.",
             "Tsukani nthambi zodulidwa ndi kuthana ndi chiswe chitsamba chili chotseguka."),
            ("tree", "Prepare a nursery: take cuttings from good mother bushes.",
             "Konzani nazale: tengani zidutswa kuchokera ku zitsamba zabwino."),
            ("thermometer", "Watch low-lying fields on very cold mornings.",
             "Yang'anani minda ya m'zigwa m'mawa wozizira kwambiri."),
        ],
    },
    {
        "month": 8, "season": "cool_dry",
        "name_en": "August", "name_ny": "Ogasiti",
        "focus_en": "Finish pruning, finish the drains, protect from fire.",
        "focus_ny": "Malizani kutema, malizani ngalande, tetezani ku moto.",
        "tasks": [
            ("scissors", "Complete all pruning this month.",
             "Malizani kutema konse mwezi uno."),
            ("water", "Finish cleaning and deepening every drain before the rains.",
             "Malizani kuyeretsa ndi kukuza ngalande zonse mvula isanafike."),
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
            ("tree", "Keep nursery beds moist and shaded; sow shade tree seed now.",
             "Sungani nazale yonyowa ndi ya mthunzi; bzalani mbewu za mitengo yamthunzi tsopano."),
        ],
    },
    {
        "month": 10, "season": "hot_dry",
        "name_en": "October", "name_ny": "Okutobala",
        "focus_en": "Hottest month - get everything ready for the rains.",
        "focus_ny": "Mwezi wotentha kwambiri - konzekerani zonse za mvula.",
        "tasks": [
            ("cart", "Buy fertilizer early so it is ready the day the rains start.",
             "Gulani fetereza msanga kuti akhale wokonzeka tsiku lomwe mvula iyamba."),
            ("shovel", "Dig planting holes for new tea and shade trees.",
             "Kumbani maenje obzalira tiyi watsopano ndi mitengo yamthunzi."),
            ("sun", "Keep shade trees; do not prune tea in this heat.",
             "Sungani mitengo yamthunzi; musateme tiyi kotentha kotere."),
            ("clipboard", "Mark out which pruned fields will be tipped first when growth starts.",
             "Onetsani minda yotemedwa yomwe mudzakonza poyamba kukula kukayamba."),
        ],
    },
    {
        "month": 11, "season": "rainy",
        "name_en": "November", "name_ny": "Novembala",
        "focus_en": "Rains start - first fertilizer, and bring pruned bushes back.",
        "focus_ny": "Mvula ikuyamba - fetereza woyamba, ndi kubweza zitsamba zotemedwa.",
        "tasks": [
            ("droplet", "Apply the first fertilizer split after good rain has soaked the soil.",
             "Thirani gawo loyamba la fetereza mvula yabwino ikanyowetsa nthaka."),
            ("scissors", "Tip the bushes you pruned: cut level about 30 cm above the pruning cut.",
             "Konzani zitsamba zomwe munatema: dulani mofanana pafupifupi masentimita 30 pamwamba pa pomwe munatema."),
            ("basket", "Restart regular plucking as new shoots appear.",
             "Yambaninso kuthyola pafupipafupi pamene mphukira zatsopano zikutuluka."),
            ("scissors", "Do the first round of weeding before the weeds get ahead of you.",
             "Chitani ulendo woyamba wopalira udzu usanakupitireni."),
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
            ("tree", "Plant new tea and shade trees once rains are well established; firm the soil around each plant.",
             "Bzalani tiyi watsopano ndi mitengo yamthunzi mvula ikakhazikika; limbikitsani nthaka mozungulira mbande iliyonse."),
            ("basket", "Pluck every 7 to 10 days; keep the plucking table level.",
             "Thyolani masiku 7 mpaka 10 aliwonse; sungani pamwamba pa zitsamba pofanana."),
            ("leaf", "Remove shoots that have stopped growing and carry no bud.",
             "Chotsani mphukira zomwe zasiya kukula ndipo zilibe phukusi."),
            ("scissors", "Weed a second time; weeds compete with tea for the fertilizer you just applied.",
             "Palirani kachiwiri; udzu umalimbirana ndi tiyi fetereza amene mwangothira."),
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
