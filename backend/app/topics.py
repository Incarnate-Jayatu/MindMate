from .models import Concept, UserTopic

def selected_ids(db, user_id):
    """Concept ids the learner chose, or None meaning every topic (the default)."""
    ids = [t.concept_id for t in db.query(UserTopic).filter_by(user_id=user_id)]
    return ids or None

def set_selected(db, user_id, ids):
    valid = {c.id for c in db.query(Concept)}
    ids = list(dict.fromkeys(ids))
    if not ids or any(i not in valid for i in ids):
        raise ValueError("choose at least one valid topic")
    db.query(UserTopic).filter_by(user_id=user_id).delete()
    db.add_all([UserTopic(user_id=user_id, concept_id=i) for i in ids])
    db.commit()
    return ids
