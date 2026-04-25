from fastapi import FastAPI

from nichefinder_core.settings import Settings

from nichefinder_cli.services.article_service import approve_article_action, publish_article_action
from nichefinder_cli.services.profile_service import (
    create_profile_action,
    delete_profile_action,
    load_profile_config,
    save_profile_config_action,
)
from nichefinder_cli.services.research_service import run_validate_free_action
from nichefinder_cli.viewer_data import (
    load_articles,
    load_budget,
    load_dashboard,
    load_keyword_clusters,
    load_keyword_detail,
    load_keywords,
    load_report,
    load_status,
)
from nichefinder_cli.viewer_jobs import get_job, list_jobs, submit_job
from nichefinder_cli.viewer_profile_data import (
    approve_noise_review,
    approve_training_review,
    load_final_review,
    load_noise_review,
    load_profiles,
    load_training_review,
    switch_active_profile,
)
from nichefinder_cli.viewer_article_routes import register_article_routes
from nichefinder_cli.viewer_job_routes import register_job_routes
from nichefinder_cli.viewer_profile_routes import register_profile_routes
from nichefinder_cli.viewer_read_routes import register_read_routes
from nichefinder_cli.viewer_review_routes import register_review_routes


def register_api_routes(app: FastAPI, settings: Settings) -> None:
    register_read_routes(
        app,
        settings,
        load_dashboard=load_dashboard,
        load_keywords=load_keywords,
        load_keyword_clusters=load_keyword_clusters,
        load_keyword_detail=load_keyword_detail,
        load_status=load_status,
        load_articles=load_articles,
        load_report=load_report,
        load_budget=load_budget,
    )
    register_profile_routes(
        app,
        settings,
        load_profiles=load_profiles,
        switch_active_profile=switch_active_profile,
        load_profile_config=load_profile_config,
        save_profile_config_action=save_profile_config_action,
        create_profile_action=create_profile_action,
        delete_profile_action=delete_profile_action,
    )
    register_review_routes(
        app,
        settings,
        load_training_review=load_training_review,
        load_noise_review=load_noise_review,
        load_final_review=load_final_review,
        approve_training_review=approve_training_review,
        approve_noise_review=approve_noise_review,
    )
    register_job_routes(
        app,
        settings,
        run_validate_free_action=run_validate_free_action,
        list_jobs=list_jobs,
        get_job=get_job,
        submit_job=submit_job,
    )
    register_article_routes(
        app,
        settings,
        approve_article_action=approve_article_action,
        publish_article_action=publish_article_action,
    )
