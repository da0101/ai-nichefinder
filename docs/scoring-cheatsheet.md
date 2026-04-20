# Scoring Cheat Sheet

Use this when reading `uv run seo validate-free ...` and `uv run seo research ...`.

## 1. Pre-SERP Shortlist

`Pre-score` is the internal deterministic ranking **before** SERP analysis.

It is not a percentage and it is not a final SEO score.
It is just a relative shortlist score used to decide which keywords deserve deeper validation.

Higher usually means:
- stronger match to the original seed
- better article-fit
- better buyer-language fit
- less drift into agency/framework/hire noise

Main positive signals:
- `intent`
- `seed_fidelity`
- `article_fit`
- `business_fit`
- `local_intent`

Main negative signals:
- query drift away from the seed
- developer/framework wording
- duplicate/near-duplicate variants

How to read it:
- `120+` = extremely aligned to the seed/problem
- `70–100` = plausible shortlist candidate
- `below ~60` = weaker fit or more drift

Important:
- only compare `Pre-score` values **within the same run**
- do not compare them across unrelated seeds as if they were calibrated globally

## 2. Keyword Validation

This score comes from an external source bucket like `DDGS`, `Bing`, `Yahoo`, or `Tavily`.

It answers:
- does this exact keyword show up in real search results?
- do those results look relevant?
- do multiple domains discuss it?

Raw scoring logic:
- `+2` if there are at least 2 results
- `+4` if at least 2 results are meaningfully relevant
- `+2` if the exact query appears in result text
- `+2` if evidence comes from at least 2 different domains
- `-4` if relevance is weak
- `-6` if there are no results

How to read it:
- `10` = very strong external evidence
- `8` = strong evidence
- `2–6` = partial evidence
- `0 or below` = weak or no evidence

Important:
- this is **research evidence**, not Google truth
- Bing/Yahoo/DDGS are helping us collect market language and article candidates
- they should not override seed fidelity

## 3. Buyer Problem Validation

Same scoring model as Keyword Validation, but applied to the buyer-problem seed phrases.

It answers:
- is this problem framing actually discussed on the web?

Use it to judge whether the buyer-problem hypothesis feels real.

## 4. Free Article Evidence

This is not a single “SEO score.”

It is a summary built from scraped pages behind validated search results.

Columns:
- `Score`
  - the validation score for the keyword that led to those pages
- `Pages`
  - how many validated pages were actually scraped
- `Recurring headings`
  - heading patterns repeated across scraped pages
- `Secondary keywords`
  - repeated phrases worth considering in the article brief
- `Questions`
  - reusable question patterns found in headings

How to read it:
- more scraped pages = more trustworthy evidence
- repeated practical phrases are more valuable than catchy landing-page copy
- use this section to build:
  - article angle
  - H2 ideas
  - secondary keyword bank
  - FAQ/question bank

## 5. Final Opportunity Score

This is the later `/100` score used after deeper analysis in `seo research`.

It is built from:
- `volume_score`
- `difficulty_score`
- `trend_score`
- `intent_score`
- `competition_score`

Current weights:
- volume: `25%`
- difficulty: `30%`
- trend: `20%`
- intent: `15%`
- competition: `10%`

How to read it:
- `70+` = strong opportunity
- `50–69` = mixed or situational
- `below 50` = weak opportunity

Important:
- this is the score closest to “should we actually write this?”
- unlike `Pre-score`, this one is intended to be read as a real final decision aid

## 6. Practical Reading Order

When auditing a run, read in this order:

1. `Buyer Problems`
   - did Gemini identify sane buyer pains?
2. `Pre-SERP Shortlist`
   - did the top keywords stay faithful to the seed?
3. `Keyword Validation`
   - do real results exist across free buckets?
4. `Buyer Problem Validation`
   - do those buyer-problem frames exist in the wild?
5. `Free Article Evidence`
   - what language, headings, and questions repeat?

## 7. Red Flags

Treat the output cautiously if you see:
- top shortlist keywords drifting away from the original buyer question
- one engine showing `no evidence` while others show strong evidence
- article evidence based on only `1` scraped page
- secondary keywords that look like marketing slogans instead of search phrases
- video/search verticals showing up as “evidence” domains

## 8. Short Version

- `Pre-score` = internal shortlist ranking
- `Keyword Validation` = does this wording show up in real search results?
- `Buyer Problem Validation` = is this buyer pain discussed on the web?
- `Free Article Evidence` = what recurring headings/questions/phrases do real pages use?
- `Opportunity Score /100` = should we actually pursue this keyword?
