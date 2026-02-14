from app import db
import sqlalchemy.orm as so
import sqlalchemy as sa


class Item(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(256), index=True, nullable=False)
