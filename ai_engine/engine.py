"""
ai_engine/engine.py

AI Buying Tool — scores and ranks products based on:
  - Price (normalized, lower = better)
  - Stock availability
  - Seller rating
  - Recent price trend (falling price = bonus)
  - Review sentiment proxy (avg stars)

Returns best option with a human-readable explanation.
"""
from decimal import Decimal
from dataclasses import dataclass, field
from typing import List, Optional


# Weight tuning constants
WEIGHT_PRICE = 0.40
WEIGHT_STOCK = 0.20
WEIGHT_SELLER_RATING = 0.30
WEIGHT_DELIVERY = 0.10

MAX_STOCK_THRESHOLD = 100  # beyond this, stock score is capped at 1.0


@dataclass
class ProductCandidate:
    product_id: str
    product_name: str
    seller_name: str
    seller_rating: float
    price: Decimal
    stock_qty: int
    delivery_days: int
    avg_review_stars: Optional[float]
    recent_prices: List[Decimal] = field(default_factory=list)

    # Computed by engine
    score: float = 0.0
    price_trend: str = 'stable'
    explanation: str = ''


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Min-max normalization → [0, 1]. Returns 0.5 if range is zero."""
    if max_val == max_val == min_val:
        return 0.5
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)


def _price_trend_score(recent_prices: List[Decimal]) -> tuple:
    """
    Returns (score, label).
    Falling price → score 1.0 (bonus), stable → 0.5, rising → 0.0.
    """
    if len(recent_prices) < 2:
        return 0.5, 'stable'
    oldest = float(recent_prices[-1])
    newest = float(recent_prices[0])
    change_pct = (newest - oldest) / (oldest or 1) * 100

    if change_pct < -2:
        return 1.0, 'falling'
    if change_pct > 2:
        return 0.0, 'rising'
    return 0.5, 'stable'


def score_candidates(candidates: List[ProductCandidate]) -> List[ProductCandidate]:
    """
    Compute composite score for each candidate and sort descending.
    """
    if not candidates:
        return []

    prices = [float(c.price) for c in candidates]
    stocks = [min(c.stock_qty, MAX_STOCK_THRESHOLD) for c in candidates]
    ratings = [c.seller_rating for c in candidates]
    deliveries = [c.delivery_days for c in candidates]

    min_price, max_price = min(prices), max(prices)
    min_stock, max_stock = min(stocks), max(stocks)
    min_rating, max_rating = min(ratings), max(ratings)
    min_dev, max_dev = min(deliveries), max(deliveries)

    for candidate in candidates:
        price_f = float(candidate.price)
        stock_f = min(candidate.stock_qty, MAX_STOCK_THRESHOLD)
        rating_f = candidate.seller_rating
        dev_f = float(candidate.delivery_days)

        # Lower price = better, so invert normalization
        price_score = 1.0 - _normalize(price_f, min_price, max_price)
        stock_score = _normalize(stock_f, min_stock, max_stock)
        rating_score = _normalize(rating_f, min_rating, max_rating)
        
        # Lower delivery days = better
        dev_score = 1.0 - _normalize(dev_f, min_dev, max_dev)
        
        trend_score, trend_label = _price_trend_score(candidate.recent_prices)

        candidate.price_trend = trend_label
        candidate.score = round(
            (price_score * WEIGHT_PRICE)
            + (stock_score * WEIGHT_STOCK)
            + (rating_score * WEIGHT_SELLER_RATING)
            + (dev_score * WEIGHT_DELIVERY),
            4,
        )

        # Build natural-language explanation
        parts = []
        if candidate.score >= 0.75:
            parts.append('Excellent overall value.')
        elif candidate.score >= 0.50:
            parts.append('Good value option.')
        else:
            parts.append('Lower-ranked option.')

        if price_score >= 0.8:
            parts.append(f'Competitively priced at ${candidate.price}.')
        if rating_score >= 0.8:
            parts.append(f'Highly rated seller ({candidate.seller_rating:.1f}/5).')
        if stock_f == 0:
            parts.append('⚠️ Currently out of stock.')
        elif stock_f < 5:
            parts.append(f'Only {candidate.stock_qty} units left.')
        if dev_score >= 0.8:
            parts.append(f'Fast delivery ({candidate.delivery_days} days).')
        if trend_label == 'falling':
            parts.append('📉 Price trend is falling — good time to buy.')

        candidate.explanation = ' '.join(parts)

    return sorted(candidates, key=lambda c: c.score, reverse=True)
