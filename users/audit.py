from .models import ActivityLog


def log_activity(*, actor_user, action, entity_type="", entity_id="", tenant=None, branch=None, metadata=None):
    if not tenant and actor_user:
        tenant = actor_user.tenant
    if not branch and actor_user:
        branch = actor_user.branch
    if not tenant:
        return

    ActivityLog.objects.create(
        tenant=tenant,
        branch=branch,
        actor_user=actor_user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
