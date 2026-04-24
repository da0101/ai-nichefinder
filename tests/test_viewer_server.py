from __future__ import annotations

import json
import threading
import time
from functools import partial
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from nichefinder_cli.commands.viewer import view
from nichefinder_cli.viewer_server import ViewerHandler
from nichefinder_core.models import Article, ContentType, Keyword
from nichefinder_core.settings import Settings
from http.server import ThreadingHTTPServer
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


def _start_server(settings: Settings):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(ViewerHandler, settings=settings))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _seed_article(settings: Settings, tmp_path: Path, *, status: str, title: str) -> str:
    create_db_and_tables(settings)
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keyword = repository.upsert_keyword(
            Keyword(
                term=f"{title.lower()} keyword",
                seed_keyword=f"{title.lower()} keyword",
                source="manual",
                monthly_volume=500,
                difficulty_score=35,
                opportunity_score=68.0,
            )
        )
        article = repository.create_article(
            Article(
                keyword_id=keyword.id,
                title=title,
                slug=title.lower().replace(" ", "-"),
                content_type=ContentType.HOW_TO,
                status=status,
                word_count=1200,
                file_path=str(tmp_path / f"{title.lower().replace(' ', '-')}.md"),
            ),
            "# Article",
        )
        return article.id


def test_viewer_command_opens_browser(monkeypatch, tmp_path: Path):
    opened: list[tuple[str, int]] = []
    served: list[tuple[str, int]] = []
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    monkeypatch.setattr("nichefinder_cli.commands.viewer.get_runtime", lambda: (settings, None, None))
    monkeypatch.setattr("nichefinder_cli.commands.viewer.serve_viewer", lambda settings, host, port: served.append((host, port)))
    monkeypatch.setattr("nichefinder_cli.commands.viewer.webbrowser.open", lambda url, new=0: opened.append((url, new)))

    view(host="127.0.0.1", port=9876)

    assert opened == [("http://127.0.0.1:9876", 2)]
    assert served == [("127.0.0.1", 9876)]


def test_viewer_server_serves_dist_assets_and_rejects_traversal(monkeypatch, tmp_path: Path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>react</html>", encoding="utf-8")
    (dist / "app.js").write_text("console.log('ok')", encoding="utf-8")
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    monkeypatch.setattr("nichefinder_cli.viewer_server._dist_dir", lambda: dist)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        assert urlopen(f"{base}/").read() == b"<html>react</html>"
        assert urlopen(f"{base}/app.js").read() == b"console.log('ok')"

        try:
            urlopen(f"{base}/../secret.txt")
            assert False, "expected traversal request to fail"
        except HTTPError as exc:
            assert exc.code == 403

        try:
            urlopen(f"{base}/missing.js")
            assert False, "expected missing asset request to fail"
        except HTTPError as exc:
            assert exc.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_falls_back_to_inline_html_when_dist_missing(monkeypatch, tmp_path: Path):
    dist = tmp_path / "dist"
    dist.mkdir()
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    monkeypatch.setattr("nichefinder_cli.viewer_server._dist_dir", lambda: dist)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        body = urlopen(f"{base}/").read().decode("utf-8")
        assert "Nichefinder" in body
        assert "Local SEO research viewer" in body
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_profile_and_training_endpoints(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.load_profiles",
        lambda: {
            "active_profile": "restaurant",
            "profiles": [{
                "slug": "restaurant",
                "site_name": "Restaurant",
                "site_url": "https://example.com",
                "site_description": "Restaurant operations software",
                "is_default": False,
                "site_config": {"site_name": "Restaurant", "site_url": "https://example.com", "site_description": "", "target_audience": "", "services": [], "primary_language": "en", "blog_url": "", "existing_articles": [], "seed_keywords": [], "target_persona": "", "competitors": [], "geographic_focus": []},
            }],
        },
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.load_training_review",
        lambda profile_slug=None, min_runs=2, limit=18: {
            "profile": {"slug": profile_slug or "restaurant", "site_name": "Restaurant", "site_url": "https://example.com", "runs": 3, "approved_noise": 1, "approved_validity": 2, "approved_legitimacy": 1},
            "approved": {"noise": {"keyword_phrases": [], "secondary_phrases": [], "domains": []}, "validity": {"keyword_phrases": [], "secondary_phrases": []}, "legitimacy": {"domains": []}},
            "candidates": [{"scope": "keyword_phrase", "label": "validity", "value": "food cost percentage", "support_runs": 2, "support_count": 2, "examples": ["food cost percentage restaurant"]}],
        },
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.load_final_review",
        lambda profiles=None, min_runs=2, limit=9: {
            "summary": [{"slug": "restaurant", "runs": 3, "approved_noise": 1, "approved_validity": 2, "approved_legitimacy": 1}],
            "shared_valid_keywords": ["food cost percentage"],
            "shared_trusted_domains": ["restaurant.org"],
            "profiles": [],
        },
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.switch_active_profile",
        lambda profile: {"active_profile": profile or "default", "profiles": []},
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.approve_training_review",
        lambda **kwargs: {"profile": {"slug": kwargs["profile_slug"], "site_name": "Restaurant", "site_url": "https://example.com", "runs": 3, "approved_noise": 1, "approved_validity": 3, "approved_legitimacy": 1}, "approved": {"noise": {"keyword_phrases": [], "secondary_phrases": [], "domains": []}, "validity": {"keyword_phrases": ["food cost percentage"], "secondary_phrases": []}, "legitimacy": {"domains": []}}, "candidates": []},
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.load_profile_config",
        lambda profile_slug=None: {
            "profile": profile_slug or "restaurant",
            "site_config": {"site_name": "Restaurant", "site_url": "https://example.com", "site_description": "", "target_audience": "", "services": [], "primary_language": "en", "blog_url": "", "existing_articles": [], "seed_keywords": [], "target_persona": "", "competitors": [], "geographic_focus": []},
            "paths": {"site_config_path": "/tmp/site.json", "database_url": "sqlite:///tmp.db"},
        },
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.save_profile_config_action",
        lambda profile_slug=None, payload=None: {
            "profile": profile_slug or "restaurant",
            "site_config": payload,
            "paths": {"site_config_path": "/tmp/site.json", "database_url": "sqlite:///tmp.db"},
        },
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.create_profile_action",
        lambda slug, from_current=False, use=False, payload=None: {
            "slug": slug,
            "site_config": payload or {"site_name": "", "site_url": "", "site_description": "", "target_audience": "", "services": [], "primary_language": "en", "blog_url": "", "existing_articles": [], "seed_keywords": [], "target_persona": "", "competitors": [], "geographic_focus": []},
            "site_config_path": f"/tmp/{slug}.json",
            "database_url": f"sqlite:///{slug}.db",
            "active": use,
        },
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.delete_profile_action",
        lambda profile_slug: {"deleted": profile_slug, "active_profile": "default"},
    )
    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.run_validate_free_action",
        lambda profile_slug=None, keyword="", sources=("ddgs", "bing", "yahoo"): {
            "profile": profile_slug or "restaurant",
            "keyword": keyword,
            "sources": list(sources),
            "location": "Montreal, Quebec, Canada",
            "buyer_problems": [{"problem": "High food cost", "article_angle": "Fix food cost"}],
            "shortlist": [{"term": "food cost percentage", "score": 78, "selected": True, "notes": [], "breakdown": {}}],
            "keyword_validations": [],
            "problem_validations": [],
            "article_evidence": [],
        },
    )

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        profiles = urlopen(f"{base}/api/profiles").read().decode("utf-8")
        assert "restaurant" in profiles

        training = urlopen(f"{base}/api/training-review?profile=restaurant").read().decode("utf-8")
        assert "food cost percentage" in training

        final_review = urlopen(f"{base}/api/final-review?profiles=restaurant").read().decode("utf-8")
        assert "restaurant.org" in final_review

        switch_req = Request(
            f"{base}/api/profiles/active",
            data=b'{"profile":"restaurant"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        switched = urlopen(switch_req).read().decode("utf-8")
        assert '"active_profile": "restaurant"' in switched

        approve_req = Request(
            f"{base}/api/training-approve",
            data=b'{"profile":"restaurant","valid_keyword_phrases":["food cost percentage"]}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        approved = urlopen(approve_req).read().decode("utf-8")
        assert '"approved_validity": 3' in approved

        config = urlopen(f"{base}/api/profile-config?profile=restaurant").read().decode("utf-8")
        assert '"profile": "restaurant"' in config

        create_req = Request(
            f"{base}/api/profiles",
            data=b'{"slug":"salon"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        created = urlopen(create_req).read().decode("utf-8")
        assert '"slug": "salon"' in created

        delete_req = Request(
            f"{base}/api/profiles/salon",
            method="DELETE",
        )
        deleted = urlopen(delete_req).read().decode("utf-8")
        assert '"deleted": "salon"' in deleted

        delete_post_req = Request(
            f"{base}/api/profiles/delete",
            data=b'{"profile":"salon"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        deleted_post = urlopen(delete_post_req).read().decode("utf-8")
        assert '"deleted": "salon"' in deleted_post

        save_req = Request(
            f"{base}/api/profile-config",
            data=b'{"profile":"restaurant","site_config":{"site_name":"Restaurant Suite","site_url":"https://example.com","site_description":"","target_audience":"","services":[],"primary_language":"en","blog_url":"","existing_articles":[],"seed_keywords":[],"target_persona":"","competitors":[],"geographic_focus":[]}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        saved = urlopen(save_req).read().decode("utf-8")
        assert 'Restaurant Suite' in saved

        validate_req = Request(
            f"{base}/api/validate-free",
            data=b'{"profile":"restaurant","keyword":"how to reduce food cost in a restaurant"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        validated = urlopen(validate_req).read().decode("utf-8")
        assert 'how to reduce food cost in a restaurant' in validated
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_rejects_invalid_training_payload(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    monkeypatch.setattr("nichefinder_cli.viewer_server.approve_training_review", lambda **kwargs: kwargs)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        bad_req = Request(
            f"{base}/api/training-approve",
            data=b'{"profile":"restaurant","valid_keyword_phrases":{"bad":"shape"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(bad_req)
            assert False, "expected invalid payload request to fail"
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_exposes_status_and_validate_free_job(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    def fake_validate(profile_slug=None, keyword="", sources=("ddgs", "bing", "yahoo"), settings_override=None):
        return {
            "profile": profile_slug or "default",
            "keyword": keyword,
            "sources": list(sources),
            "shortlist": [{"term": keyword, "selected": True, "score": 88}],
        }

    monkeypatch.setattr("nichefinder_cli.viewer_jobs.run_validate_free_action", fake_validate)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        status = json.loads(urlopen(f"{base}/api/status").read().decode("utf-8"))
        assert status["status"] == "ok"

        submit_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"validate-free","params":{"profile":"restaurant","keyword":"food cost percentage","sources":["ddgs"]}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        submitted_response = urlopen(submit_req)
        assert submitted_response.status == 202
        submitted = json.loads(submitted_response.read().decode("utf-8"))
        assert submitted["action"] == "validate-free"
        assert submitted["status"] in {"queued", "running", "succeeded"}

        job = submitted
        for _ in range(20):
            job = json.loads(urlopen(f"{base}/api/jobs/{submitted['id']}").read().decode("utf-8"))
            if job["status"] == "succeeded":
                break
            time.sleep(0.05)

        assert job["status"] == "succeeded"
        assert job["result"]["keyword"] == "food cost percentage"
        assert job["result"]["sources"] == ["ddgs"]

        jobs = json.loads(urlopen(f"{base}/api/jobs").read().decode("utf-8"))
        assert any(item["id"] == submitted["id"] for item in jobs["jobs"])

        bad_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"shell","params":{"cmd":"rm -rf /"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(bad_req)
            assert False, "expected unsupported job action to fail"
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_runs_research_job(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    def fake_research(profile_slug=None, keyword="", settings_override=None):
        return {
            "profile": profile_slug or "default",
            "keyword": keyword,
            "location": "Montreal, Quebec, Canada",
            "keywords_found": 2,
            "keywords_saved": 1,
            "keyword_ids": ["kw_1"],
            "buyer_problems": [{"problem": "Need to reduce costs"}],
            "analyses": [{
                "keyword": {"id": "kw_1", "term": keyword, "intent": "informational"},
                "opportunity": {"keyword_id": "kw_1", "keyword_term": keyword, "composite_score": 77, "priority": "high"},
                "should_create_content": True,
                "content_angle": "Cost reduction guide",
                "serp": {},
                "trend": {},
                "ads": {},
                "competitor": {},
            }],
        }

    monkeypatch.setattr("nichefinder_cli.viewer_jobs.run_research_action", fake_research)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        submit_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"research","params":{"profile":"restaurant","keyword":"restaurant cost control"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        submitted = json.loads(urlopen(submit_req).read().decode("utf-8"))
        assert submitted["action"] == "research"
        assert submitted["params"]["keyword"] == "restaurant cost control"

        job = submitted
        for _ in range(20):
            job = json.loads(urlopen(f"{base}/api/jobs/{submitted['id']}").read().decode("utf-8"))
            if job["status"] == "succeeded":
                break
            time.sleep(0.05)

        assert job["status"] == "succeeded"
        assert job["result"]["profile"] == "restaurant"
        assert job["result"]["keywords_saved"] == 1
        assert job["result"]["analyses"][0]["should_create_content"] is True

        invalid_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"research","params":{"keyword":"restaurant cost control","sources":["ddgs"]}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(invalid_req)
            assert False, "expected sources on research job to fail"
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_job_result_survives_restart(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    def fake_research(profile_slug=None, keyword="", settings_override=None):
        return {
            "profile": profile_slug or "default",
            "keyword": keyword,
            "keywords_saved": 1,
        }

    monkeypatch.setattr("nichefinder_cli.viewer_jobs.run_research_action", fake_research)

    first_server, first_thread = _start_server(settings)
    first_base = f"http://127.0.0.1:{first_server.server_port}"
    try:
        submit_req = Request(
            f"{first_base}/api/jobs",
            data=b'{"action":"research","params":{"profile":"restaurant","keyword":"restart readable job"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        submitted = json.loads(urlopen(submit_req).read().decode("utf-8"))

        job = submitted
        for _ in range(20):
            job = json.loads(urlopen(f"{first_base}/api/jobs/{submitted['id']}").read().decode("utf-8"))
            if job["status"] == "succeeded":
                break
            time.sleep(0.05)

        assert job["status"] == "succeeded"
    finally:
        first_server.shutdown()
        first_server.server_close()
        first_thread.join(timeout=2)

    second_server, second_thread = _start_server(settings)
    second_base = f"http://127.0.0.1:{second_server.server_port}"
    try:
        restored = json.loads(urlopen(f"{second_base}/api/jobs/{submitted['id']}").read().decode("utf-8"))
        assert restored["status"] == "succeeded"
        assert restored["result"]["keyword"] == "restart readable job"
        assert restored["result"]["keywords_saved"] == 1
    finally:
        second_server.shutdown()
        second_server.server_close()
        second_thread.join(timeout=2)


def test_viewer_server_rejects_non_loopback_write_without_token(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    monkeypatch.setattr(
        "nichefinder_cli.viewer_server.ViewerHandler._client_is_loopback",
        lambda self: False,
    )

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        submit_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"research","params":{"keyword":"remote write"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(submit_req)
            assert False, "expected non-loopback write to fail"
        except HTTPError as exc:
            assert exc.code == 403
            body = json.loads(exc.read().decode("utf-8"))
            assert "loopback clients" in body["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_rejects_non_loopback_origin_without_token(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        submit_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"research","params":{"keyword":"cross site write"}}',
            headers={
                "Content-Type": "application/json",
                "Origin": "https://evil.example",
            },
            method="POST",
        )
        try:
            urlopen(submit_req)
            assert False, "expected non-loopback origin write to fail"
        except HTTPError as exc:
            assert exc.code == 403
            body = json.loads(exc.read().decode("utf-8"))
            assert "origin must be loopback" in body["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_requires_token_for_writes_when_configured(monkeypatch, tmp_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'seo.db'}",
        viewer_api_token="secret-token",
    )

    def fake_validate(profile_slug=None, keyword="", sources=("ddgs", "bing", "yahoo")):
        return {"profile": profile_slug or "default", "keyword": keyword, "sources": list(sources)}

    monkeypatch.setattr("nichefinder_cli.viewer_jobs.run_validate_free_action", fake_validate)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        missing_token_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"validate-free","params":{"keyword":"token protected"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(missing_token_req)
            assert False, "expected missing token write to fail"
        except HTTPError as exc:
            assert exc.code == 403

        bad_token_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"validate-free","params":{"keyword":"token protected"}}',
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer wrong-token",
            },
            method="POST",
        )
        try:
            urlopen(bad_token_req)
            assert False, "expected bad token write to fail"
        except HTTPError as exc:
            assert exc.code == 403

        good_token_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"validate-free","params":{"keyword":"token protected"}}',
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer secret-token",
            },
            method="POST",
        )
        response = urlopen(good_token_req)
        assert response.status == 202
        submitted = json.loads(response.read().decode("utf-8"))
        assert submitted["action"] == "validate-free"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_exposes_articles_report_and_budget(tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    article_id = _seed_article(settings, tmp_path, status="published", title="Report Ready")
    with get_session(settings) as session:
        repository = SeoRepository(session)
        repository.record_api_usage(provider="gemini", tokens_in=12, tokens_out=34)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        articles = json.loads(urlopen(f"{base}/api/articles").read().decode("utf-8"))
        assert articles["summary"]["total_articles"] == 1
        assert articles["articles"][0]["id"] == article_id
        assert articles["articles"][0]["status"] == "published"
        assert articles["articles"][0]["keyword_term"] == "report ready keyword"

        report = json.loads(urlopen(f"{base}/api/report").read().decode("utf-8"))
        assert report["summary"]["published_articles"] == 1
        assert report["top_keywords"][0]["term"] == "report ready keyword"

        budget = json.loads(urlopen(f"{base}/api/budget").read().decode("utf-8"))
        gemini = next(item for item in budget["usage"] if item["provider"] == "gemini")
        assert gemini["tokens_in"] == 12
        assert gemini["tokens_out"] == 34
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_article_approve_and_publish_endpoints(tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    draft_article_id = _seed_article(settings, tmp_path, status="draft", title="Needs Approval")
    approved_article_id = _seed_article(settings, tmp_path, status="approved", title="Ready To Publish")

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        approve_req = Request(
            f"{base}/api/articles/{draft_article_id}/approve",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        approved = json.loads(urlopen(approve_req).read().decode("utf-8"))
        assert approved["article"]["status"] == "approved"

        publish_draft_req = Request(
            f"{base}/api/articles/{draft_article_id}/publish",
            data=b'{"url":"https://example.com/draft"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        published_from_approved = json.loads(urlopen(publish_draft_req).read().decode("utf-8"))
        assert published_from_approved["article"]["status"] == "published"
        assert published_from_approved["article"]["published_url"] == "https://example.com/draft"

        publish_req = Request(
            f"{base}/api/articles/{approved_article_id}/publish",
            data=b'{"url":"https://example.com/post"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        published = json.loads(urlopen(publish_req).read().decode("utf-8"))
        assert published["article"]["status"] == "published"
        assert published["article"]["published_url"] == "https://example.com/post"

        blocked_article_id = _seed_article(settings, tmp_path, status="draft", title="Still Draft")
        blocked_req = Request(
            f"{base}/api/articles/{blocked_article_id}/publish",
            data=b'{"url":"https://example.com/blocked"}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(blocked_req)
            assert False, "expected publish without approval to fail"
        except HTTPError as exc:
            assert exc.code == 400
            body = json.loads(exc.read().decode("utf-8"))
            assert "must be approved before it can be published" in body["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_runs_brief_job(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    def fake_generate_brief(profile_slug=None, keyword_id="", force=False, settings_override=None):
        return {
            "profile": profile_slug or "default",
            "keyword_id": keyword_id,
            "force": force,
            "brief": {
                "should_create_content": True,
                "content_angle": "Practical guide",
                "content_brief": {
                    "target_keyword": "food cost percentage",
                    "secondary_keywords": ["restaurant food cost formula"],
                    "content_type": "how_to",
                    "suggested_title": "Food Cost Percentage Guide",
                    "suggested_h2_structure": ["What it is", "How to calculate it"],
                    "questions_to_answer": ["How do you calculate food cost percentage?"],
                    "word_count_target": 1400,
                    "tone": "practical",
                    "cta_type": "consultation",
                    "competing_urls": [],
                    "is_rewrite": False,
                    "existing_article_url": None,
                    "existing_article_content": None,
                },
            },
        }

    monkeypatch.setattr("nichefinder_cli.viewer_jobs.run_generate_brief_action", fake_generate_brief)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        submit_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"brief","params":{"profile":"restaurant","keyword_id":"kw_1","force":true}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        submitted = json.loads(urlopen(submit_req).read().decode("utf-8"))
        assert submitted["action"] == "brief"
        assert submitted["params"]["keyword_id"] == "kw_1"
        assert submitted["params"]["force"] is True

        job = submitted
        for _ in range(20):
            job = json.loads(urlopen(f"{base}/api/jobs/{submitted['id']}").read().decode("utf-8"))
            if job["status"] == "succeeded":
                break
            time.sleep(0.05)

        assert job["status"] == "succeeded"
        assert job["result"]["brief"]["content_brief"]["target_keyword"] == "food cost percentage"
        assert job["result"]["force"] is True

        invalid_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"brief","params":{"keyword":"missing keyword id"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(invalid_req)
            assert False, "expected missing keyword_id to fail"
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_viewer_server_runs_write_job(monkeypatch, tmp_path: Path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")

    def fake_write_article(profile_slug=None, keyword_id="", force=False, settings_override=None):
        return {
            "profile": profile_slug or "default",
            "keyword_id": keyword_id,
            "force": force,
            "article": {
                "article_id": "article_1",
                "file_path": "/tmp/article.md",
                "word_count": 1520,
                "title": "Reduce Restaurant Food Costs",
                "meta_description": "A practical guide to food cost control.",
                "slug": "reduce-restaurant-food-costs",
            },
        }

    monkeypatch.setattr("nichefinder_cli.viewer_jobs.run_write_article_action", fake_write_article)

    server, thread = _start_server(settings)
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        submit_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"write","params":{"profile":"restaurant","keyword_id":"kw_1"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        submitted = json.loads(urlopen(submit_req).read().decode("utf-8"))
        assert submitted["action"] == "write"
        assert submitted["params"]["keyword_id"] == "kw_1"

        job = submitted
        for _ in range(20):
            job = json.loads(urlopen(f"{base}/api/jobs/{submitted['id']}").read().decode("utf-8"))
            if job["status"] == "succeeded":
                break
            time.sleep(0.05)

        assert job["status"] == "succeeded"
        assert job["result"]["article"]["article_id"] == "article_1"
        assert job["result"]["article"]["slug"] == "reduce-restaurant-food-costs"

        invalid_req = Request(
            f"{base}/api/jobs",
            data=b'{"action":"write","params":{"keyword_id":"kw_1","force":"yes"}}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(invalid_req)
            assert False, "expected non-boolean force to fail"
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
