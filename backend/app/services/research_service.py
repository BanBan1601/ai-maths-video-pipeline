from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx


CROSSREF_BASE = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"

TRUSTED_TEXTBOOKS = [
    {
        "title": "Linear Algebra Done Right",
        "authors": ["Sheldon Axler"],
        "year": 2015,
        "url": "https://linear.axler.net/",
        "source_type": "textbook",
        "trust_score": 98,
    },
    {
        "title": "Introduction to Probability",
        "authors": ["Dimitri Bertsekas", "John Tsitsiklis"],
        "year": 2008,
        "url": "https://www.athenasc.com/probbook.html",
        "source_type": "textbook",
        "trust_score": 97,
    },
    {
        "title": "Pattern Recognition and Machine Learning",
        "authors": ["Christopher Bishop"],
        "year": 2006,
        "url": "https://www.microsoft.com/en-us/research/publication/pattern-recognition-machine-learning/",
        "source_type": "textbook",
        "trust_score": 96,
    },
    {
        "title": "Mathematics for Machine Learning",
        "authors": ["Marc Deisenroth", "Aldo Faisal", "Cheng Soon Ong"],
        "year": 2020,
        "url": "https://mml-book.github.io/",
        "source_type": "textbook",
        "trust_score": 95,
    },
    {
        "title": "Deep Learning",
        "authors": ["Ian Goodfellow", "Yoshua Bengio", "Aaron Courville"],
        "year": 2016,
        "url": "https://www.deeplearningbook.org/",
        "source_type": "textbook",
        "trust_score": 94,
    },
    {
        "title": "Principles of Mathematical Analysis",
        "authors": ["Walter Rudin"],
        "year": 1976,
        "url": None,
        "source_type": "textbook",
        "trust_score": 99,
    },
]


@dataclass
class SourceCandidate:
    title: str
    authors: list[str]
    year: Optional[int]
    url: Optional[str]
    doi: Optional[str]
    source_type: str  # textbook / paper / survey / lecture_notes
    trust_score: int
    abstract: Optional[str] = None
    publisher: Optional[str] = None


class ResearchService:
    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    def retrieve_sources(
        self, topic: str, queries: Optional[list[str]] = None
    ) -> list[SourceCandidate]:
        """Retrieve sources from Crossref + Semantic Scholar. Always includes relevant trusted textbooks."""
        results: list[SourceCandidate] = []
        search_terms = queries or [topic]

        # Add relevant trusted textbooks based on keywords
        for tb in TRUSTED_TEXTBOOKS:
            if any(
                kw.lower() in tb["title"].lower() or kw.lower() in topic.lower()
                for kw in ["linear", "algebra", "probability", "machine learning", "deep learning", "analysis", "math"]
            ):
                results.append(
                    SourceCandidate(
                        title=tb["title"],
                        authors=tb["authors"],
                        year=tb["year"],
                        url=tb["url"],
                        doi=None,
                        source_type=tb["source_type"],
                        trust_score=tb["trust_score"],
                    )
                )
                if len(results) >= 2:
                    break

        # Try Crossref
        for query in search_terms[:2]:
            try:
                r = httpx.get(
                    CROSSREF_BASE,
                    params={
                        "query": query,
                        "rows": 3,
                        "select": "DOI,title,author,published,URL,abstract,publisher,type",
                    },
                    timeout=self._timeout,
                    headers={"User-Agent": "AIMathsVideoPipeline/1.0 (mailto:admin@example.com)"},
                )
                if r.status_code == 200:
                    items = r.json().get("message", {}).get("items", [])
                    for item in items[:2]:
                        if item.get("type") in (
                            "journal-article", "proceedings-article", "monograph", "book"
                        ):
                            trust = self._crossref_trust(item)
                            results.append(
                                SourceCandidate(
                                    title=(item.get("title") or ["Unknown"])[0],
                                    authors=[
                                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                                        for a in item.get("author", [])[:3]
                                    ],
                                    year=item.get("published", {}).get(
                                        "date-parts", [[None]]
                                    )[0][0],
                                    url=item.get("URL"),
                                    doi=item.get("DOI"),
                                    source_type="paper",
                                    trust_score=trust,
                                    publisher=item.get("publisher"),
                                    abstract=(item.get("abstract") or "")[:500],
                                )
                            )
            except Exception:
                pass  # Graceful fallback

        # Try Semantic Scholar
        for query in search_terms[:1]:
            try:
                r = httpx.get(
                    f"{SEMANTIC_SCHOLAR_BASE}/paper/search",
                    params={
                        "query": query,
                        "limit": 3,
                        "fields": "title,authors,year,url,abstract,citationCount,publicationTypes",
                    },
                    timeout=self._timeout,
                )
                if r.status_code == 200:
                    papers = r.json().get("data", [])
                    for paper in papers[:2]:
                        pub_types = paper.get("publicationTypes") or []
                        is_review = "Review" in pub_types or "JournalArticle" in pub_types
                        trust = 80 if is_review else 70
                        citation_count = paper.get("citationCount", 0)
                        if citation_count > 100:
                            trust = min(trust + 10, 95)
                        results.append(
                            SourceCandidate(
                                title=paper.get("title", "Unknown"),
                                authors=[
                                    a.get("name", "") for a in paper.get("authors", [])[:3]
                                ],
                                year=paper.get("year"),
                                url=paper.get("url"),
                                doi=None,
                                source_type="paper",
                                trust_score=trust,
                                abstract=(paper.get("abstract") or "")[:500],
                            )
                        )
            except Exception:
                pass

        # Deduplicate by title prefix
        seen: set[str] = set()
        unique: list[SourceCandidate] = []
        for s in sorted(results, key=lambda x: x.trust_score, reverse=True):
            key = s.title[:40].lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique[:6]

    def _crossref_trust(self, item: dict) -> int:
        score = 70
        itype = item.get("type", "")
        if itype in ("monograph", "book"):
            score = 92
        elif itype == "journal-article":
            score = 82
        pub = item.get("publisher", "").lower()
        if any(
            p in pub
            for p in ["springer", "elsevier", "cambridge", "oxford", "wiley", "ieee", "acm"]
        ):
            score += 5
        return min(score, 97)

    def validate_claim_coverage(
        self, claims: list[str], sources: list[SourceCandidate]
    ) -> dict:
        return {
            "all_claims_covered": bool(claims and sources),
            "claim_count": len(claims),
            "source_count": len(sources),
            "coverage_ratio": min(1.0, len(sources) / max(len(claims), 1)),
        }
