from __future__ import annotations

import random
from dataclasses import dataclass, field


TOPIC_POOL = {
    "university_maths": {
        "linear_algebra": [
            {
                "title": "Why eigenvectors reveal invariant directions",
                "hook": "A matrix moves everything — except these special directions.",
                "visual_richness": 9,
                "novelty": 7,
            },
            {
                "title": "What singular values measure about a linear map",
                "hook": "Forget eigenvalues — singular values tell you what a matrix actually does to space.",
                "visual_richness": 10,
                "novelty": 8,
            },
            {
                "title": "Why the determinant measures volume scaling",
                "hook": "The determinant is not a formula. It is a measure of how much a matrix stretches space.",
                "visual_richness": 9,
                "novelty": 7,
            },
            {
                "title": "What orthogonality really means geometrically",
                "hook": "Two perpendicular vectors share no information about each other.",
                "visual_richness": 8,
                "novelty": 6,
            },
            {
                "title": "Why row reduction preserves the solution set",
                "hook": "You can replace one equation with a combination of two — and keep all solutions intact.",
                "visual_richness": 7,
                "novelty": 6,
            },
        ],
        "real_analysis": [
            {
                "title": "What epsilon-delta really means visually",
                "hook": "Limits are not about infinity. They are about control.",
                "visual_richness": 8,
                "novelty": 7,
            },
            {
                "title": "Why uniform convergence preserves continuity",
                "hook": "Pointwise convergence can lose continuity. Uniform convergence cannot.",
                "visual_richness": 8,
                "novelty": 8,
            },
            {
                "title": "What compactness means in plain terms",
                "hook": "Compact sets are the finite sets of analysis — they behave as if they have no escape.",
                "visual_richness": 7,
                "novelty": 8,
            },
        ],
        "probability": [
            {
                "title": "Why variance is squared deviation",
                "hook": "Variance is not about average distance. It is about squared penalty — and that shape matters.",
                "visual_richness": 8,
                "novelty": 6,
            },
            {
                "title": "What conditional probability changes geometrically",
                "hook": "Conditioning shrinks the sample space. That is all it does.",
                "visual_richness": 9,
                "novelty": 7,
            },
            {
                "title": "Why the central limit theorem surprises everyone",
                "hook": "Add enough random variables and you always get a bell curve. Always.",
                "visual_richness": 10,
                "novelty": 7,
            },
        ],
        "complex_analysis": [
            {
                "title": "What Cauchy's integral formula actually says",
                "hook": "The value at a point is completely determined by values on a circle around it.",
                "visual_richness": 9,
                "novelty": 9,
            },
            {
                "title": "Why holomorphic functions are rigid",
                "hook": "In complex analysis, a function that is differentiable once is differentiable infinitely many times.",
                "visual_richness": 8,
                "novelty": 9,
            },
        ],
    },
    "maths_for_ai": {
        "gradients_optimization": [
            {
                "title": "Why gradient descent follows the steepest path",
                "hook": "Gradient descent asks: which direction makes the loss drop fastest right now?",
                "visual_richness": 10,
                "novelty": 6,
            },
            {
                "title": "What the chain rule does in backpropagation",
                "hook": "Backprop is just the chain rule applied backwards through a computation graph.",
                "visual_richness": 10,
                "novelty": 7,
            },
            {
                "title": "Why learning rate matters more than you think",
                "hook": "Too small and you stall. Too large and you explode. The learning rate is everything.",
                "visual_richness": 9,
                "novelty": 6,
            },
            {
                "title": "What momentum does to gradient descent",
                "hook": "Momentum remembers where it has been. That memory smooths out noisy gradients.",
                "visual_richness": 9,
                "novelty": 7,
            },
        ],
        "linear_algebra_for_ml": [
            {
                "title": "Why SVD explains data compression",
                "hook": "Singular value decomposition decomposes any matrix into a sum of rank-1 updates — and most are negligible.",
                "visual_richness": 10,
                "novelty": 8,
            },
            {
                "title": "Why PCA is just SVD on centered data",
                "hook": "Principal component analysis finds the directions that capture the most variance. SVD computes them.",
                "visual_richness": 10,
                "novelty": 7,
            },
            {
                "title": "What the attention mechanism computes geometrically",
                "hook": "Attention is a learned, dynamic, weighted sum. The weights depend on similarity.",
                "visual_richness": 9,
                "novelty": 8,
            },
        ],
        "probability_for_ml": [
            {
                "title": "What KL divergence measures between distributions",
                "hook": "KL divergence measures how much information you lose by approximating one distribution with another.",
                "visual_richness": 9,
                "novelty": 7,
            },
            {
                "title": "Why cross-entropy is the right training loss for classification",
                "hook": "Cross-entropy penalizes confident wrong predictions exponentially. That is exactly what you want.",
                "visual_richness": 8,
                "novelty": 6,
            },
            {
                "title": "What softmax does to raw scores",
                "hook": "Softmax turns arbitrary numbers into probabilities that sum to one. But how?",
                "visual_richness": 8,
                "novelty": 5,
            },
            {
                "title": "Why Bayesian updating works the way it does",
                "hook": "Every new observation is evidence. Bayes rule is just how you update your beliefs with evidence.",
                "visual_richness": 9,
                "novelty": 7,
            },
        ],
        "information_theory": [
            {
                "title": "What entropy measures in a probability distribution",
                "hook": "Entropy is not disorder. It is uncertainty — the minimum bits needed to encode a random variable.",
                "visual_richness": 9,
                "novelty": 7,
            },
            {
                "title": "Why mutual information captures dependence between variables",
                "hook": "Correlation misses nonlinear dependence. Mutual information does not.",
                "visual_richness": 9,
                "novelty": 8,
            },
        ],
    },
}

TRACK_SUBTOPIC_MAP = {
    "university_maths": list(TOPIC_POOL["university_maths"].keys()),
    "maths_for_ai": list(TOPIC_POOL["maths_for_ai"].keys()),
}


@dataclass
class TopicCandidate:
    title: str
    hook: str
    track: str
    subtopic: str
    video_type: str
    visual_richness: int
    novelty: int
    audience: str = field(default="")
    reference_queries: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.track == "university_maths":
            self.audience = "early undergraduate / advanced high school"
            self.video_type = "theory"
        else:
            self.audience = "ML practitioners / AI learners"
            self.video_type = "application"
        # Build reference search queries from title
        self.reference_queries = [self.title, self.subtopic.replace("_", " ")]


class TopicEngine:
    def __init__(self):
        self._used_titles: set[str] = set()

    def propose(self) -> TopicCandidate:
        """Propose a high-scoring topic, avoiding recent repeats."""
        candidates = []
        for track, subtopics in TOPIC_POOL.items():
            for subtopic, topics in subtopics.items():
                for t in topics:
                    if t["title"] not in self._used_titles:
                        candidates.append((track, subtopic, t))
        if not candidates:
            self._used_titles.clear()
            return self.propose()
        # Score: visual_richness * 0.5 + novelty * 0.3 + random jitter 0.2
        def score(c):
            _, _, t = c
            return t["visual_richness"] * 0.5 + t["novelty"] * 0.3 + random.uniform(0, 2)
        candidates.sort(key=score, reverse=True)
        track, subtopic, topic = candidates[0]
        self._used_titles.add(topic["title"])
        return TopicCandidate(
            title=topic["title"],
            hook=topic["hook"],
            track=track,
            subtopic=subtopic,
            video_type="theory" if track == "university_maths" else "application",
            visual_richness=topic["visual_richness"],
            novelty=topic["novelty"],
        )

    def propose_batch(self, n: int) -> list[TopicCandidate]:
        return [self.propose() for _ in range(n)]
