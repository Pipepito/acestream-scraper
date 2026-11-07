"""Policy writes and admission serialize through one DB write claim."""
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from app.models.import_sources import ImportPolicyState, ImportExclusionRule
from app.models.models import AcestreamChannel


class ImportExclusionRepository:
    def __init__(self, db):
        self.db = db

    def claim(self):
        # Also supports metadata-created test DBs. No commit: caller owns the
        # entire admission + channel mutation transaction, including TV rows.
        self.db.execute(insert(ImportPolicyState).values(id=1, revision=0).on_conflict_do_nothing())
        self.db.execute(update(ImportPolicyState).where(ImportPolicyState.id == 1).values(
            revision=ImportPolicyState.revision))
        self.db.expire_all()

    def revision(self):
        return self.db.scalar(select(ImportPolicyState.revision).where(ImportPolicyState.id == 1)) or 0

    def bump(self):
        self.db.execute(update(ImportPolicyState).where(ImportPolicyState.id == 1).values(
            revision=ImportPolicyState.revision + 1))
        return self.revision()

    def rules(self, enabled=None):
        q = self.db.query(ImportExclusionRule)
        if enabled is not None:
            q = q.filter(ImportExclusionRule.enabled == enabled)
        return q.order_by(ImportExclusionRule.id)

    def get(self, rule_id):
        return self.db.get(ImportExclusionRule, rule_id)

    def inventory(self, after, limit):
        return self.db.query(AcestreamChannel.id, AcestreamChannel.name).filter(
            AcestreamChannel.id > after).order_by(AcestreamChannel.id).limit(limit).all()
