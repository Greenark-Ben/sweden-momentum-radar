# Momentum signal model

The dashboard's KÖP / AVVAKTA / SÄLJ label is a deterministic high-risk screening signal, not personal investment advice.

## Technical base

Inputs: 1D, 5D, 1M and 3M performance, relative volume, liquidity risk and daily overextension.

- KÖP: broad positive momentum with volume confirmation and no severe overextension.
- AVVAKTA: mixed momentum, weak volume confirmation, or an overextended daily move.
- SÄLJ: deteriorating medium-term momentum or a short-lived bounce against negative 1M/3M trend.

## Catalyst adjustment

Catalyst Intelligence may adjust the technical score only when both a numeric Catalyst Strength exists and confidence is at least 70%.

Positive evidence:
- Bud / M&A, Myndighetsbesked, Kliniskt resultat: +3 base catalyst points.
- Stor order, Rapport / prognos: +2.
- Partnerskap, Produkt / lansering, Insider: +1.

Negative evidence:
- Finansiering / emission: -2.

Very strong evidence (strength >= 90) and very high confidence (>= 85%) can add one extra point each, with the catalyst adjustment capped at +/-4.

Low-confidence matches, volume-only explanations and unverified catalysts contribute zero points.

## Guardrails

- An extreme >50% same-day move cannot become KÖP solely because of catalyst evidence; it is forced to AVVAKTA by the anti-FOMO guardrail.
- A negative financing/emission catalyst cannot upgrade a technically weak setup.
- Catalyst evidence never replaces price/volume confirmation.

The signal tooltip exposes final score, technical contribution and catalyst contribution separately so the decision remains inspectable.