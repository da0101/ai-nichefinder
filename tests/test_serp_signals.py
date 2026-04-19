from nichefinder_core.models import SerpFeatures, SerpPage
from nichefinder_core.utils.serp_signals import avg_interest_to_volume_score, estimate_difficulty


def _features(**kwargs) -> SerpFeatures:
    defaults = dict(
        has_featured_snippet=False,
        has_people_also_ask=False,
        has_local_pack=False,
        has_image_pack=False,
        has_video_results=False,
        has_shopping_results=False,
        ad_count_top=0,
        organic_result_count=10,
    )
    return SerpFeatures(**{**defaults, **kwargs})


def _page(domain: str) -> SerpPage:
    return SerpPage(position=1, title="Test", url=f"https://{domain}/page", domain=domain, snippet="")


def test_empty_serp_has_zero_difficulty():
    assert estimate_difficulty(_features(), []) == 0


def test_featured_snippet_adds_20():
    score = estimate_difficulty(_features(has_featured_snippet=True), [])
    assert score == 20


def test_paa_adds_10():
    score = estimate_difficulty(_features(has_people_also_ask=True), [])
    assert score == 10


def test_ads_capped_at_15():
    # 4 ads × 5 = 20, but cap is 15
    score = estimate_difficulty(_features(ad_count_top=4), [])
    assert score == 15


def test_single_ad_adds_5():
    score = estimate_difficulty(_features(ad_count_top=1), [])
    assert score == 5


def test_wikipedia_in_top5_adds_15():
    pages = [_page("en.wikipedia.org")]
    score = estimate_difficulty(_features(), pages)
    assert score == 15


def test_reddit_in_top5_adds_15():
    pages = [_page("www.reddit.com")]
    score = estimate_difficulty(_features(), pages)
    assert score == 15


def test_medium_authority_adds_8():
    pages = [_page("medium.com")]
    score = estimate_difficulty(_features(), pages)
    assert score == 8


def test_unknown_domain_adds_nothing():
    pages = [_page("some-random-blogger.com")]
    score = estimate_difficulty(_features(), pages)
    assert score == 0


def test_capped_at_100():
    # featured(20) + paa(10) + 3 ads(15) + shopping(5) + local(5)
    # + 3× wikipedia (45) = 100
    pages = [_page("wikipedia.org"), _page("youtube.com"), _page("reddit.com")]
    score = estimate_difficulty(
        _features(
            has_featured_snippet=True,
            has_people_also_ask=True,
            ad_count_top=3,
            has_shopping_results=True,
            has_local_pack=True,
        ),
        pages,
    )
    assert score == 100


def test_low_competition_blog_serp():
    # No features, no known authority — a solo blogger's SERP
    pages = [_page("myblog.io"), _page("another-dev.com"), _page("personal-site.ca")]
    score = estimate_difficulty(_features(), pages)
    assert score == 0


def test_hard_web_dev_keyword():
    # "hire a web developer" type SERP: PAA, ads, clutch.co, upwork
    pages = [_page("clutch.co"), _page("upwork.com"), _page("toptal.com")]
    score = estimate_difficulty(_features(has_people_also_ask=True, ad_count_top=3), pages)
    # 10 + 15 + 8 + 8 + 8 = 49
    assert score == 49


def test_avg_interest_to_volume_score_direct_mapping():
    assert avg_interest_to_volume_score(0.0) == 0.0
    assert avg_interest_to_volume_score(50.0) == 50.0
    assert avg_interest_to_volume_score(100.0) == 100.0
    assert avg_interest_to_volume_score(73.4) == 73.4


def test_avg_interest_clamped():
    assert avg_interest_to_volume_score(-5.0) == 0.0
    assert avg_interest_to_volume_score(105.0) == 100.0
