# -*- coding: utf-8 -*-
"""Actions the advice model can choose for each topic, and their wording."""

# topic -> action -> (urgency, English, Chichewa)
ACTIONS: dict[str, dict[str, tuple[str, str, str]]] = {
    "fertilizer": {
        "apply_now": ("normal",
            "Conditions are suitable for fertilizer today. The soil should be moist enough for the bushes to take it up, so you can go ahead.",
            "Nyengo ya lero ndi yabwino pa kuthira fetereza. Nthaka iyenera kukhala yonyowa mokwanira kuti zitsamba zitenge fetereza, choncho mukhoza kupitiriza."),
        "delay_heavy_rain": ("urgent",
            "Do not apply fertilizer now. Heavy rain is expected and would wash it off the field before the bushes can use it. Wait until the rain has passed and the soil is moist but not waterlogged.",
            "Osathira fetereza pano. Mvula yaikulu ikuyembekezeka ndipo ingakokolole fetereza asanagwiritsidwe ntchito ndi zitsamba. Dikirani mvula itatha, nthaka ikhale yonyowa koma osadzaza madzi."),
        "delay_dry_soil": ("caution",
            "The soil is too dry for fertilizer. The bushes cannot take up nutrients from dry ground, so wait for good rain before applying.",
            "Nthaka ndi youma kwambiri pa fetereza. Zitsamba sizingatenge chakudya m'nthaka youma, choncho dikirani mvula yabwino musanathire."),
        "delay_off_season": ("caution",
            "This is outside the main fertilizer window. Plan your applications for the rainy season, from November to March.",
            "Ino si nthawi yayikulu ya kuthira fetereza. Konzani kuthira nyengo ya mvula, kuyambira Novembala mpaka Malichi."),
    },
    "plucking": {
        "pluck_normal": ("normal",
            "Conditions are good for plucking. Keep to your 10 to 11 day round so the leaf stays fine and earns the better grade.",
            "Nyengo ndi yabwino pa kuthyola. Sungani nyengo yanu ya masiku 10 mpaka 11 kuti masamba akhale abwino ndipo mulandire mtengo wabwino."),
        "pluck_before_rain": ("caution",
            "Rain is likely tomorrow, so pluck today if your round is due and deliver the leaf quickly.",
            "Mvula ikuyembekezeka mawa, choncho thyolani lero ngati nyengo yakwana ndipo fikitsani masamba msanga."),
        "pluck_wet_leaf": ("caution",
            "The leaf is wet from rain. Pluck later in the day if you can, keep the basket loose and get the leaf to the buying centre quickly so it does not heat and lose grade.",
            "Masamba ndi onyowa chifukwa cha mvula. Thyolani masana ngati mungathe, musathine masamba mu dengu, ndipo fikitsani ku malo ogulira msanga kuti asatenthe ndi kuonongeka."),
        "pluck_early_morning": ("normal",
            "It will be hot today. Pluck early in the morning while it is cool, keep baskets in the shade and deliver before the afternoon heat.",
            "Kukhala kotentha lero. Thyolani m'mawa kwambiri pamene kuli kozizira, sungani madengu pa mthunzi ndipo fikitsani masamba dzuwa lisanakwere."),
    },
    "pruning": {
        "prune_now": ("normal",
            "This is a good time to prune. The weather is cool and dry, so the bushes will recover well. Make clean, sloping cuts.",
            "Ino ndi nthawi yabwino ya kutema. Nyengo ndi yozizira youma, choncho zitsamba zichira bwino. Temani modula bwino mopendeka."),
        "delay_wet": ("caution",
            "Postpone pruning for now. Cuts made in wet weather heal slowly and invite disease. Wait for a dry spell.",
            "Imitsani kutema pano. Mabala opangidwa nyengo yonyowa amachedwa kuchira ndipo amayitanitsa matenda. Dikirani masiku owuma."),
        "delay_not_season": ("caution",
            "Do not prune at this time of year. Pruning is best done in the cool dry months, June to August, when the bushes recover well.",
            "Osatema nthawi ino ya chaka. Kutema kuli bwino miyezi yozizira youma, Juni mpaka Ogasiti, pamene zitsamba zimachira bwino."),
    },
    "pest_disease": {
        "check_fungal": ("caution",
            "Damp, wet weather favours leaf and root diseases. Inspect your field this week, remove and burn badly affected material, and weed so air can move.",
            "Nyengo yonyowa imathandiza matenda a masamba ndi mizu. Yendererani munda wanu sabata ino, chotsani ndi kutentha zowonongeka, ndipo palirani kuti mpweya uzizungulira."),
        "check_mites": ("caution",
            "Hot, dry weather lets red spider mite multiply quickly. Check the mature leaves for a bronze colour and fine webs, especially on dusty field edges.",
            "Nyengo yotentha youma imachulukitsa nthata zofiira msanga. Onani masamba akulu ngati ali ndi mtundu wa mkuwa ndi ukonde, makamaka m'mbali mwa munda."),
        "routine_check": ("normal",
            "There is no particular weather risk for pests today. Keep to your weekly field walk so you catch any build-up early.",
            "Palibe chiopsezo cha nyengo pa tizilombo lero. Pitirizani kuyendera munda sabata iliyonse kuti muzindikire msanga."),
    },
    "harvest": {
        "harvest_normal": ("normal",
            "Growth is steady. Keep your plucking round on time and arrange enough labour for the coming weeks.",
            "Kukula kuli bwino. Sungani nyengo ya kuthyola pa nthawi yake ndipo konzani antchito okwanira masabata akubwera."),
        "harvest_protect": ("caution",
            "Rain is likely, so plan transport to the buying centre early in the day. Wet leaf left waiting loses grade quickly.",
            "Mvula ikuyembekezeka, choncho konzani mayendedwe a masamba kupita ku malo ogulira m'mawa. Masamba onyowa akadikira amaonongeka msanga."),
        "harvest_low": ("normal",
            "Growth is slow in this dry weather, so expect a lighter crop. You can space the round slightly and concentrate on leaf quality.",
            "Kukula kuli pang'onopang'ono nyengo youma iyi, choncho yembekezerani tiyi wochepa. Mukhoza kutalikitsa pang'ono nyengo ya kuthyola ndi kusamalira khalidwe la masamba."),
    },
    "planting": {
        "plant_now": ("normal",
            "Conditions are right for planting or filling gaps. The soil has enough moisture for young plants to establish.",
            "Nyengo ndi yoyenera kubzala kapena kudzaza mipata. Nthaka ili ndi chinyezi chokwanira kuti mbande zikhazikike."),
        "plant_wait_moisture": ("caution",
            "Wait before planting. The soil is too dry for young plants. Plant after the rains have soaked the ground.",
            "Dikirani musanabzale. Nthaka ndi youma kwambiri pa mbande. Bzalani mvula ikanyowetsa nthaka."),
        "plant_wait_season": ("caution",
            "Do not plant now. Young plants will not survive without the rains. Dig your holes and order seedlings so you are ready in November.",
            "Osabzala panopa. Mbande sizipulumuka popanda mvula. Kumbani maenje ndi kuyitanitsa mbande kuti mukhale okonzeka mu Novembala."),
    },
    "weather": {
        "weather_dry": ("normal",
            "Dry weather is expected. It is a good time for field work, but young plants may need water.",
            "Nyengo youma ikuyembekezeka. Ndi nthawi yabwino ya ntchito za m'munda, koma mbande zingafunike madzi."),
        "weather_rain": ("caution",
            "Rain is likely. Hold off on fertilizer and spraying, and plan for handling wet leaf.",
            "Mvula ikuyembekezeka. Imitsani kuthira fetereza ndi kupopera, ndipo konzekerani masamba onyowa."),
        "weather_heavy": ("urgent",
            "Heavy rain is expected. Do not apply fertilizer, clear your drains and deliver plucked leaf quickly.",
            "Mvula yamphamvu ikuyembekezeka. Musathire fetereza, konzani ngalande ndipo fikitsani masamba othyola msanga."),
    },
    "shade": {
        "shade_protect": ("normal",
            "It is hot and dry, so shade trees and mulch are protecting your bushes. Do not thin the shade now; add mulch if you can.",
            "Kukutentha ndi kouma, choncho mitengo yamthunzi ndi malichi zikuteteza zitsamba zanu. Musachepetse mthunzi pano; onjezerani malichi ngati mungathe."),
        "shade_thin": ("normal",
            "In wet weather a heavily shaded field stays damp, which encourages disease. Thin the shade so light and air reach the bushes.",
            "Nyengo yonyowa munda wa mthunzi wambiri umakhala wonyowa, zomwe zimayambitsa matenda. Chepetsani mthunzi kuti kuwala ndi mpweya zifike pa zitsamba."),
    },
}

TOPICS = list(ACTIONS)
ALL_ACTIONS = [(topic, action) for topic in TOPICS for action in ACTIONS[topic]]


def wording(topic: str, action: str, language: str) -> tuple[str, str]:
    """(urgency, text) for an action."""
    urgency, en, ny = ACTIONS[topic][action]
    return urgency, ny if language == "NY" else en


# Soil moisture limits (ERA5-Land, top 7 cm). 0.22 is about the dry-season
# median in Thyolo and Mulanje; young plants need wetter soil.
DRY_SOIL = 0.22
PLANTING_SOIL = 0.30


def expert_label(topic: str, f: dict) -> str:
    """The action tea agronomy guidance recommends for situation `f`.

    `f` holds: rain_today, rain_tomorrow (mm), rain_prob (0-1, from the rain
    model), rain_3d (mm over the last 3 days), tmax, humidity, wind, month and
    soil_moisture (ERA5-Land, m3/m3, may be missing).
    """
    wet_soon = f["rain_prob"] >= 0.7 or f["rain_tomorrow"] >= 15
    soil = f.get("soil_moisture")
    soil_known = soil is not None and soil == soil  # not missing / NaN
    if soil_known:
        dry_spell = soil < DRY_SOIL and f["rain_today"] < 1
    else:
        dry_spell = f["rain_3d"] < 2 and f["rain_today"] < 1
    m = f["month"]

    if topic == "fertilizer":
        if m in (5, 6, 7, 8):
            return "delay_off_season"
        if wet_soon or f["rain_today"] >= 15:
            return "delay_heavy_rain"
        if dry_spell:
            return "delay_dry_soil"
        return "apply_now"
    if topic == "plucking":
        if f["rain_today"] >= 10:
            return "pluck_wet_leaf"
        if wet_soon:
            return "pluck_before_rain"
        if f["tmax"] >= 30:
            return "pluck_early_morning"
        return "pluck_normal"
    if topic == "pruning":
        if m not in (6, 7, 8):
            return "delay_not_season"
        if f["rain_prob"] >= 0.6 or f["rain_today"] >= 5:
            return "delay_wet"
        return "prune_now"
    if topic == "pest_disease":
        if f["humidity"] >= 85 and f["rain_3d"] >= 10:
            return "check_fungal"
        if f["tmax"] >= 28 and dry_spell:
            return "check_mites"
        return "routine_check"
    if topic == "harvest":
        if f["rain_prob"] >= 0.7:
            return "harvest_protect"
        if m in (6, 7, 8, 9, 10) and dry_spell:
            return "harvest_low"
        return "harvest_normal"
    if topic == "planting":
        if m not in (11, 12, 1, 2):
            return "plant_wait_season"
        too_dry = soil < PLANTING_SOIL if soil_known else f["rain_3d"] < 5
        if too_dry and f["rain_prob"] < 0.4:
            return "plant_wait_moisture"
        return "plant_now"
    if topic == "weather":
        if f["rain_tomorrow"] >= 15 or f["rain_prob"] >= 0.8:
            return "weather_heavy"
        if f["rain_prob"] >= 0.5:
            return "weather_rain"
        return "weather_dry"
    if topic == "shade":
        if f["tmax"] >= 29 and dry_spell:
            return "shade_protect"
        return "shade_thin"
    raise ValueError(topic)
