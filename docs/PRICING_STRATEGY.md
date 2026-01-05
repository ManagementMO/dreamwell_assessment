# Dreamwell AI - CPM Pricing Strategy

> **Purpose:** This document defines the transparent, data-driven pricing model used by the Dreamwell Influencer Agent to calculate fair market value for influencer partnerships.

---

## Overview

Dreamwell uses a **CPM-based pricing model** (Cost Per Mille / Cost Per Thousand Views) with dynamic multipliers based on channel performance metrics. This ensures:

- **Transparency:** Influencers see exactly how their price is calculated
- **Fairness:** Prices reflect actual channel value, not arbitrary rates
- **ROI-Focused:** Brands pay based on expected performance

---

## CPM Formula

```
Final CPM = Base CPM × Engagement Multiplier × Niche Multiplier × Consistency Multiplier

Total Price = (Average Views / 1000) × Final CPM
```

---

## 1. Base CPM Tiers

Base CPM is determined by subscriber count:

| Tier | Subscribers | Base CPM | Rationale |
|------|-------------|----------|-----------|
| **Micro** | 1K - 10K | $12.50 | High engagement, niche audiences |
| **Small** | 10K - 50K | $17.50 | Growing channels with loyal bases |
| **Mid** | 50K - 100K | $20.00 | Established presence |
| **Macro** | 100K - 500K | $27.50 | Significant reach |
| **Large** | 500K - 1M | $50.00 | Major influence |
| **Mega** | 1M+ | $70.00 | Mass market reach |

---

## 2. Engagement Multiplier

Engagement rate = (Likes + Comments) / Views

| Engagement Rate | Multiplier | Classification |
|-----------------|------------|----------------|
| < 5% | 0.7x | Low engagement |
| 5% - 15% | 1.0x | Average |
| 15% - 30% | 1.3x | High engagement |
| > 30% | 1.5x | Viral/Cult following |

**Why it matters:** High engagement signals an active, trusting audience more likely to convert.

---

## 3. Niche Multiplier

Content category affects advertiser demand:

| Niche | Multiplier | Notes |
|-------|------------|-------|
| **Finance** | 1.4x | High CPM vertical, affluent audience |
| **Tech/AI** | 1.2x | Decision-makers, high intent |
| **Business** | 1.2x | B2B friendly |
| **Marketing** | 1.1x | Marketing professionals |
| **Lifestyle** | 1.0x | General audience |
| **Gaming** | 0.9x | High volume, lower CPM typical |

---

## 4. Consistency Multiplier

Upload regularity affects reliability:

| Score | Multiplier | Criteria |
|-------|------------|----------|
| **High** | 1.1x | Weekly+ uploads, low variance in views |
| **Medium** | 1.0x | Biweekly uploads, moderate variance |
| **Low** | 0.9x | Irregular posting, high view variance |

---

## Negotiation Boundaries

When influencers counter-offer, we apply these rules:

| Difference from Fair Value | Action | Response |
|---------------------------|--------|----------|
| ≤ 10% | **Auto-Accept** | "That works for us!" |
| 10% - 25% | **Negotiate** | Counter with middle ground |
| 25% - 40% | **Counter-Offer** | Explain fair value, offer max budget |
| > 40% | **Polite Decline** | "Unfortunately outside our budget" |

---

## Example Calculation

**Channel:** Tech Review Alex
- Subscribers: 100,000
- Avg Views: 25,000
- Engagement: 25%
- Category: Tech
- Consistency: High

```
Base CPM: $27.50 (100K = Macro tier)
Engagement: 1.3x (25% = High)
Niche: 1.2x (Tech)
Consistency: 1.1x (High)

Final CPM = $27.50 × 1.3 × 1.2 × 1.1 = $47.19

Total Price = (25,000 / 1,000) × $47.19 = $1,179.75

Recommended Offer: ~$1,180
Negotiation Cap: $1,416 (+20%)
```

---

## Implementation

The pricing logic is implemented in `mcp_server.py`:

- `get_base_cpm(subscribers)` - Returns tier-based CPM
- `get_engagement_multiplier(rate)` - Returns engagement factor
- `get_niche_multiplier(title, description)` - Detects content category
- `get_consistency_multiplier(score)` - Returns reliability factor
- `calculate_offer_price()` - MCP tool combining all factors
- `validate_counter_offer()` - MCP tool for negotiation analysis

---

## Data Sources

| Metric | Source | Fallback |
|--------|--------|----------|
| Subscribers | YouTube Data API v3 | Local JSON profiles |
| Views | YouTube Data API v3 | Local JSON profiles |
| Engagement | Calculated from recent videos | Profile estimate |
| Category | Channel description analysis | Manual tagging |

---

*Last Updated: January 2026*
