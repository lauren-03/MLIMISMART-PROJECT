// About MlimiSmart page.
import { Link } from 'react-router-dom'

import { useAreas } from '../components/AreaSelect'
import { Footer, PageHead } from '../components/Shared'
import { useApp } from '../context/AppContext'

const CONTENT = {
  EN: {
    title: 'About MlimiSmart',
    intro: 'MlimiSmart helps smallholder tea farmers in Thyolo and Mulanje decide what to do on their farms, using today\'s weather and proven tea farming practice.',
    whyTitle: 'Why MlimiSmart exists',
    why: [
      'Tea is one of Malawi\'s most important crops, and most of it is grown in Thyolo and Mulanje by thousands of smallholder farmers.',
      'Good tea farming depends on timing: when to apply fertilizer, when to prune, how often to pluck. The right time changes with the weather, and the weather is becoming harder to predict.',
      'Extension officers do valuable work, but there are too few of them to visit every farm when a decision has to be made. MlimiSmart gives farmers timely advice in between those visits.',
    ],
    doesTitle: 'What MlimiSmart does',
    does: [
      ['Weather for your area', 'Today\'s weather and the next five days for 23 tea areas, with warnings for heavy rain, heat, cold and dry spells.'],
      ['Answers to your questions', 'Ask about fertilizer, plucking, pruning, pest risk, planting or harvesting, and get advice that fits your area and today\'s weather.'],
      ['Farm records', 'A tea calendar for each month and a harvest diary that adds up your kilograms and income.'],
    ],
    howTitle: 'How the advice is made',
    how: [
      'MlimiSmart reads your question and works out what it is about.',
      'It checks the weather for your own area, and its own rain model predicts whether it will rain tomorrow. This model has learnt from ten years of daily weather in all 23 areas.',
      'A second model, the advice model, looks at the whole situation and chooses the best action, for example to wait before applying fertilizer because heavy rain is coming.',
      'After each piece of advice you can say whether it helped. The advice model learns from these answers, and both models are retrained every day as new weather comes in.',
      'It gives you the advice in English or Chichewa, together with the reason behind it.',
    ],
    reachTitle: 'Three ways to use MlimiSmart',
    reach: [
      ['On the website', 'Register with your phone number to see your dashboard, ask questions and keep your records.'],
      ['By USSD on any phone', 'Dial *384*211# and choose from the menu. No internet and no smartphone are needed.'],
      ['By SMS', 'Send a word such as FERTILIZER or WEATHER, or ask a question in your own words. Send HELP to see everything you can ask.'],
    ],
    reachNote: 'All three give the same advice, because they all use the same system.',
    whereTitle: 'Where MlimiSmart works',
    caution: 'MlimiSmart is a guide, not a replacement for your extension officer. Before using any chemical, or if a problem is spreading, ask your extension officer.',
    cta: 'Create your account',
    ctaUssd: 'Try the USSD menu',
  },
  NY: {
    title: 'Za MlimiSmart',
    intro: 'MlimiSmart amathandiza alimi ang\'onoang\'ono a tiyi ku Thyolo ndi Mulanje kusankha zoyenera kuchita m\'minda yawo, pogwiritsa ntchito nyengo ya lero ndi njira zotsimikizika za ulimi wa tiyi.',
    whyTitle: 'Chifukwa chake MlimiSmart alipo',
    why: [
      'Tiyi ndi imodzi mwa mbewu zofunika kwambiri ku Malawi, ndipo yambiri imalimidwa ku Thyolo ndi Mulanje ndi alimi ang\'onoang\'ono ambirimbiri.',
      'Ulimi wabwino wa tiyi umadalira nthawi: nthawi yothira fetereza, yotema, ndi kangati kusenda. Nthawi yoyenera imasintha malinga ndi nyengo, ndipo nyengo ikukhala yovuta kuneneratu.',
      'Alangizi a zaulimi amagwira ntchito yofunika, koma ndi ochepa kuti afike pa munda uliwonse pamene chisankho chikufunika. MlimiSmart amapereka uphungu pa nthawi yake pakati pa maulendo awo.',
    ],
    doesTitle: 'Zomwe MlimiSmart amachita',
    does: [
      ['Nyengo ya dera lanu', 'Nyengo ya lero ndi masiku asanu akubwera m\'madera 23 a tiyi, pamodzi ndi machenjezo a mvula yamphamvu, kutentha, kuzizira ndi chilala.'],
      ['Mayankho a mafunso anu', 'Funsani za fetereza, kusenda, kutema, tizilombo, kubzala kapena kukolola, ndipo mulandire uphungu woyenera dera lanu ndi nyengo ya lero.'],
      ['Zolemba za munda', 'Kalendala ya tiyi ya mwezi uliwonse ndi kaundula wa zokolola amene amawerengera makilogalamu ndi ndalama zanu.'],
    ],
    howTitle: 'Momwe uphungu umapangidwira',
    how: [
      'MlimiSmart amawerenga funso lanu ndi kumvetsa kuti likukhudza chiyani.',
      'Amayang\'ana nyengo ya dera lanu, ndipo model yake ya mvula imaneneratu ngati mvula igwa mawa. Model imeneyi yaphunzira kuchokera ku nyengo ya tsiku ndi tsiku ya zaka khumi m\'madera onse 23.',
      'Model yachiwiri, ya uphungu, imaona zonse zomwe zikuchitika ndi kusankha choyenera kuchita, mwachitsanzo kudikira musanathire fetereza chifukwa mvula yamphamvu ikubwera.',
      'Mukalandira uphungu mungatiuze ngati wakuthandizani. Model ya uphungu imaphunzira kuchokera ku mayankho amenewa, ndipo ma model onse awiri amaphunzitsidwanso tsiku lililonse.',
      'Amakupatsani uphungu mu Chingerezi kapena Chichewa, pamodzi ndi chifukwa chake.',
    ],
    reachTitle: 'Njira zitatu zogwiritsira ntchito MlimiSmart',
    reach: [
      ['Pa webusaiti', 'Lembetsani ndi nambala yanu ya foni kuti muone chiwonetsero chanu, mufunse mafunso ndi kusunga zolemba zanu.'],
      ['Pa USSD pa foni iliyonse', 'Imbani *384*211# ndipo sankhani pa menyu. Simufuna intaneti kapena foni yamakono.'],
      ['Pa SMS', 'Tumizani mawu monga FETEREZA kapena NYENGO, kapena funsani funso m\'mawu anu. Tumizani THANDIZO kuti muone zonse zomwe mungafunse.'],
    ],
    reachNote: 'Njira zonse zitatu zimapereka uphungu womwewo, chifukwa zonse zimagwiritsa ntchito makina amodzi.',
    whereTitle: 'Kumene MlimiSmart amagwira ntchito',
    caution: 'MlimiSmart ndi chitsogozo, osati m\'malo mwa alangizi a zaulimi. Musanagwiritse ntchito mankhwala aliwonse, kapena ngati vuto likufalikira, funsani alangizi a zaulimi.',
    cta: 'Pangani akaunti yanu',
    ctaUssd: 'Yesani menyu ya USSD',
  },
}

export default function About() {
  const { language, farmer } = useApp()
  const c = CONTENT[language] ?? CONTENT.EN
  const areas = useAreas()

  return (
    <>
      <PageHead title={c.title} intro={c.intro} />
      <div className="container about">
        <section className="row g-5 mb-5" aria-labelledby="about-why">
          <div className="col-lg-7">
            <h2 id="about-why" className="section-title h3">{c.whyTitle}</h2>
            {c.why.map((p) => <p key={p} className="about-text">{p}</p>)}
          </div>
          <div className="col-lg-5">
            <img src="/images/farmers-smiling.jpg" alt="Smallholder tea farmers in their field"
                 className="section-photo" style={{ maxHeight: 340 }} />
          </div>
        </section>

        <section className="mb-5" aria-labelledby="about-does">
          <h2 id="about-does" className="section-title h3">{c.doesTitle}</h2>
          <div className="row g-4">
            {c.does.map(([title, text]) => (
              <div className="col-md-6" key={title}>
                <h3 className="h6 fw-bold mb-1">{title}</h3>
                <p className="text-muted mb-0">{text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="row g-5 mb-5" aria-labelledby="about-how">
          <div className="col-lg-6">
            <h2 id="about-how" className="section-title h3">{c.howTitle}</h2>
            <ol className="about-steps">
              {c.how.map((step) => <li key={step}>{step}</li>)}
            </ol>
          </div>
          <div className="col-lg-6">
            <h2 className="section-title h3">{c.reachTitle}</h2>
            <dl className="about-list">
              {c.reach.map(([term, text]) => (
                <div key={term}>
                  <dt>{term}</dt>
                  <dd>{text}</dd>
                </div>
              ))}
            </dl>
            <p className="small text-muted">{c.reachNote}</p>
          </div>
        </section>

        <section className="mb-5" aria-labelledby="about-where">
          <h2 id="about-where" className="section-title h3">{c.whereTitle}</h2>
          <div className="row g-4">
            {['Thyolo', 'Mulanje'].map((district) => (
              <div className="col-md-6" key={district}>
                <h3 className="h6 fw-bold">{district} District</h3>
                <p className="text-muted mb-0">
                  {areas.filter((a) => a.district === district)
                    .map((a) => (a.kind === 'boma' ? `${a.name} Boma` : a.name)).join(', ')}
                </p>
              </div>
            ))}
          </div>
        </section>

        <p className="about-caution mb-4">{c.caution}</p>

        <div className="d-flex gap-2 flex-wrap">
          {!farmer && <Link to="/register" className="btn btn-tea btn-lg">{c.cta}</Link>}
          <Link to="/ussd" className="btn btn-outline-tea btn-lg">{c.ctaUssd}</Link>
        </div>
      </div>
      <Footer />
    </>
  )
}
