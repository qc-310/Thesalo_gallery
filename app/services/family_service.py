from app.extensions import db
from app.models.auth import Family, FamilyMember, User
from sqlalchemy import select
import uuid6

class FamilyService:
    def create_family(self, name: str, user: User) -> Family:
        """Create a new family and assign the creator as admin"""
        family = Family(name=name)
        db.session.add(family)
        db.session.flush() # get ID

        membership = FamilyMember(
            family_id=family.id,
            user_id=user.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        return family

    def get_user_families(self, user_id: uuid6.UUID):
        """Get all families a user belongs to"""
        stmt = select(Family).join(FamilyMember).where(FamilyMember.user_id == user_id)
        return db.session.execute(stmt).scalars().all()

    def add_member(self, family_id: uuid6.UUID, email: str, role: str = 'member'):
        """Add a member by email (if user exists). For invitation flow, we might need more logic."""
        user = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()
        if not user:
             # In a real app we might create a pending invitation or shadow user
             return None # Or raise exception
        
        # Check if already member
        existing = db.session.execute(
            select(FamilyMember).filter_by(family_id=family_id, user_id=user.id)
        ).scalar_one_or_none()
        
        if existing:
            return existing

        member = FamilyMember(family_id=family_id, user_id=user.id, role=role)
        db.session.add(member)
        db.session.commit()
        return member
