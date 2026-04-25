"""Compatibility re-export layer for viewer action helpers."""

from nichefinder_cli.services.article_service import approve_article_action, publish_article_action
from nichefinder_cli.services.profile_service import (
    create_profile_action,
    delete_profile_action,
    load_profile_config,
    save_profile_config_action,
)
from nichefinder_cli.services.workflow_service import (
    run_generate_brief_action,
    run_monitor_sync_action,
    run_rank_check_action,
    run_research_action,
    run_rewrite_article_action,
    run_validate_free_action,
    run_write_article_action,
)

__all__ = [
    "approve_article_action",
    "create_profile_action",
    "delete_profile_action",
    "load_profile_config",
    "publish_article_action",
    "save_profile_config_action",
    "run_generate_brief_action",
    "run_monitor_sync_action",
    "run_rank_check_action",
    "run_research_action",
    "run_rewrite_article_action",
    "run_validate_free_action",
    "run_write_article_action",
]
