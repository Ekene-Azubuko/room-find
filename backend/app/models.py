from datetime import datetime, timezone

from .extensions import db


def utc_now():
    """Return an aware UTC timestamp for database defaults and updates."""
    return datetime.now(timezone.utc)


class User(db.Model):
    """Store account credentials and the user's editable profile."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    onboarding_completed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now,
                           server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now,
                           onupdate=utc_now, server_default=db.func.now())
    housing_preference = db.relationship("HousingPreference", back_populates="user",
                                        uselist=False, cascade="all, delete-orphan",
                                        passive_deletes=True)
    lifestyle_preferences = db.relationship("LifestylePreference", back_populates="user",
                                            cascade="all, delete-orphan", passive_deletes=True)

    def public_identity(self):
        """Serialize only the account identity safe for public API responses."""
        return {"id": self.id, "email": self.email}


class HousingPreference(db.Model):
    """Store one set of housing answers and requirement flags per user."""

    __tablename__ = "housing_preferences"
    __table_args__ = (
        db.CheckConstraint("budget_min >= 0", name="housing_budget_min_nonnegative"),
        db.CheckConstraint("budget_max >= 0", name="housing_budget_max_nonnegative"),
        db.CheckConstraint("budget_min <= budget_max", name="housing_budget_order"),
        db.CheckConstraint("lease_months > 0", name="housing_lease_positive"),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    city = db.Column(db.String(100))
    budget_min = db.Column(db.Numeric(10, 2))
    budget_max = db.Column(db.Numeric(10, 2))
    move_in_date = db.Column(db.Date)
    lease_months = db.Column(db.Integer)
    city_is_requirement = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    budget_is_requirement = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    move_in_is_requirement = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    lease_is_requirement = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now,
                           onupdate=utc_now, server_default=db.func.now())
    user = db.relationship("User", back_populates="housing_preference")


class LifestylePreference(db.Model):
    """Reserve NULL for unanswered values and no_preference for an explicit choice."""

    __tablename__ = "lifestyle_preferences"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    question_key = db.Column(db.String(50), primary_key=True)
    own_answer = db.Column(db.String(100))
    roommate_answer = db.Column(db.String(100))
    is_requirement = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now,
                           onupdate=utc_now, server_default=db.func.now())
    user = db.relationship("User", back_populates="lifestyle_preferences")


def lock_user(user_id):
    """Serialize account edits and refresh identity-map data after acquiring the lock."""
    return db.session.execute(db.select(User).where(User.id == user_id).with_for_update()
                              .execution_options(populate_existing=True)).scalar_one()
