KEYWORD_INTENT_PROMPT = """
You are an SEO search intent classifier.
Given a list of keywords and the context of a website that offers AI development,
SaaS development, mobile apps, and technical consulting services, classify the
search intent of each keyword.
Respond ONLY with a JSON array:
[
  {{
    "keyword": "string",
    "intent": "informational" | "commercial" | "transactional" | "navigational",
    "reasoning": "one sentence"
  }}
]
Context: {site_description}
Keywords: {keywords_json}
""".strip()

KEYWORD_EXPANSION_PROMPT = """
You are an SEO keyword research assistant for a personal technical consulting site.
Generate long-tail keyword ideas that a real person could search when looking for
services or expertise related to the seed keyword.
Respond ONLY with a JSON array:
[
  {{
    "keyword": "string",
    "reasoning": "one sentence"
  }}
]
Rules:
- Focus on realistic search queries, not marketing slogans.
- Prefer long-tail, specific, problem-aware phrases.
- Include both informational and commercial opportunities when they fit.
- Avoid duplicates and keep the intent relevant to the site context.
Site description: {site_description}
Target audience: {target_audience}
Services: {services}
Seed keyword: {seed_keyword}
Max keywords: {max_keywords}
""".strip()

SERP_ANALYSIS_PROMPT = """
You are an SEO competition analyst. Analyze these SERP results for the keyword
"{keyword}" and assess ranking difficulty for a personal portfolio website that
focuses on AI development and consulting.
SERP data: {serp_json}
Respond ONLY with JSON:
{{
  "competition_level": "low" | "medium" | "high",
  "rankable": true | false,
  "rankable_reasoning": "2 sentences max",
  "dominant_content_type": "article" | "tool" | "forum" | "mixed",
  "featured_snippet_capturable": true | false,
  "authority_sites_present": true | false,
  "recommended_content_angle": "one specific suggestion for differentiating content"
}}
Be honest and critical. "rankable: false" is a valid and often correct answer
for competitive terms. Do not be optimistic.
""".strip()

COMPETITOR_ANALYSIS_PROMPT = """
You are analyzing the top-ranking competitor pages for the keyword "{keyword}".
Your goal is to identify what a NEW article must cover to compete, and what
gaps exist that could differentiate a new article.
Pages analyzed: {pages_json}
Respond ONLY with JSON:
{{
  "table_stakes_topics": ["topic covered by all 3"],
  "differentiator_topics": ["topic covered by only 1-2"],
  "gap_opportunities": ["important topic none of them cover"],
  "questions_answered": ["list of all questions addressed across pages"],
  "recommended_word_count": 1800,
  "content_differentiation_angle": "specific suggestion for being better"
}}
""".strip()

SYNTHESIS_PROMPT = """
You are an SEO content strategist for a personal portfolio website offering
AI development, SaaS, mobile apps, and technical consulting.
The keyword "{keyword}" has been analyzed. Here is the data:
Opportunity score: {composite_score}/100
Monthly volume: {volume}
Keyword difficulty: {difficulty}
Trend direction: {trend_direction}
Search intent: {intent}
Average competitor word count: {avg_word_count}
Content gaps identified: {gaps}
People also ask: {paa_questions}
Generate a content brief for this keyword.
Respond ONLY with JSON:
{{
  "why_good_fit": "2 sentences: why this keyword fits the site",
  "content_type": "how_to" | "listicle" | "comparison" | "thought_leadership",
  "suggested_title": "SEO-optimized article title",
  "suggested_h2_structure": ["H2 1", "H2 2", "H2 3", "H2 4", "H2 5"],
  "questions_to_answer": ["question 1", "question 2", "question 3"],
  "secondary_keywords": ["kw1", "kw2", "kw3"],
  "tone": "technical" | "accessible" | "conversational",
  "cta_type": "contact_form" | "portfolio" | "case_study",
  "action": "new_article" | "rewrite_existing",
  "existing_article_url": null
}}
""".strip()

ADS_ANALYSIS_PROMPT = """
You are an SEO and paid search analyst. Review the following ad snippets and
extract the main commercial angles. Return JSON:
{{
  "top_ad_angles": ["angle one", "angle two", "angle three"]
}}
Ads: {ads_json}
""".strip()

CONTENT_GENERATION_PROMPT = """
You are a technical content writer for {author_name}, a software developer
and consultant specializing in AI tools, SaaS development, and mobile apps.
Write a {word_count_target}-word {content_type} article for the following brief.
The article will be published on danilulmashev.com to attract potential clients
who need technical help with their digital products.
TARGET KEYWORD: {target_keyword}
SECONDARY KEYWORDS (include naturally): {secondary_keywords}
TITLE: {suggested_title}
STRUCTURE (use these H2s): {h2_structure}
QUESTIONS TO ANSWER: {questions_to_answer}
TONE: {tone}
CTA TYPE: {cta_type}
CONTENT RULES:
Include the target keyword in the title, first paragraph, and at least
2 subheadings naturally.
Include secondary keywords at least once each.
Write in first person where appropriate - this is a personal site.
Do not use filler phrases like "In today's world" or "In conclusion".
End with a clear CTA relevant to the CTA type specified.
Write for humans first, search engines second.
Minimum depth: every H2 section must have at least 150 words.
Include at least one concrete example or mini case study per major section.

{rewrite_instruction}
OUTPUT FORMAT:
Return the complete article in markdown with the H2/H3 structure specified.
Start directly with the article title as # H1.
Do not include any preamble or explanation before the article.
""".strip()
