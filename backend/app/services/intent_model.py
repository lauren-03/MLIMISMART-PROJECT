"""Topic classifier for farmer questions (scikit-learn)."""
import logging
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ..data.training_data import KEYWORDS, TRAINING_DATA

log = logging.getLogger(__name__)

# Below this probability the classifier is treated as undecided, and the
# engine asks the farmer to rephrase rather than guessing a topic.
# Below this the guess is too weak to commit to a topic. At 0.18 the
# question "what time is rain expected to start" was answered with
# pruning advice on a 0.28 score. Weak guesses now go to "general",
# where the question is answered openly instead of being forced into
# the nearest topic.
CONFIDENCE_FLOOR = 0.35


class TopicClassifier:
    def __init__(self) -> None:
        self.pipeline: Pipeline | None = None
        self.accuracy: float | None = None
        self.n_examples = 0
        self.topics: list[str] = []

    def train(self) -> None:
        texts = [normalise(q) for q, _ in TRAINING_DATA]
        labels = [topic for _, topic in TRAINING_DATA]
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 5),
                sublinear_tf=True,
                min_df=1,
            )),
            ("clf", MultinomialNB(alpha=0.15)),
        ])
        self.pipeline.fit(texts, labels)
        self.n_examples = len(texts)
        self.topics = sorted(set(labels))
        # Training-set accuracy. Reported for the admin dashboard as a sanity
        # check that the model fitted, not as a held-out evaluation figure.
        self.accuracy = float(self.pipeline.score(texts, labels))
        log.info(
            "Topic classifier trained on %d examples, %d topics, fit accuracy %.2f",
            self.n_examples, len(self.topics), self.accuracy,
        )

    def predict(self, question: str) -> tuple[str, float, str]:
        """Return (topic, confidence, method).

        A bare keyword is resolved by lookup so that single-word SMS messages
        are deterministic; anything longer goes to the model.
        """
        cleaned = normalise(question)
        if not cleaned:
            return "general", 1.0, "empty"

        keyword_hit = _keyword_lookup(cleaned)
        if keyword_hit:
            return keyword_hit, 1.0, "keyword"

        if self.pipeline is None:
            self.train()
        assert self.pipeline is not None

        probabilities = self.pipeline.predict_proba([cleaned])[0]
        classes = list(self.pipeline.named_steps["clf"].classes_)
        best_index = int(probabilities.argmax())
        # str() because scikit-learn returns numpy string scalars, which do
        # not serialise cleanly to JSON.
        topic = str(classes[best_index])
        confidence = float(probabilities[best_index])
        if confidence < CONFIDENCE_FLOOR:
            return "general", confidence, "low_confidence"
        return topic, confidence, "model"

    def info(self) -> dict:
        return {
            "algorithm": "TF-IDF (char 2-5 grams) + Multinomial Naive Bayes",
            "training_examples": self.n_examples,
            "topics": self.topics,
            "fit_accuracy": round(self.accuracy, 3) if self.accuracy else None,
            "confidence_floor": CONFIDENCE_FLOOR,
        }


def normalise(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _keyword_lookup(cleaned: str) -> str | None:
    """Match a single-word message, or a two-word message like 'fertilizer today'."""
    words = cleaned.split()
    if len(words) == 1:
        return KEYWORDS.get(words[0])
    if len(words) == 2:
        for word in words:
            if word in KEYWORDS and KEYWORDS[word] != "general":
                return KEYWORDS[word]
    return None


classifier = TopicClassifier()
