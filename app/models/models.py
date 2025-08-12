import datetime
import enum
from typing import List, Optional

from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Boolean,
    Float,
    LargeBinary,
    Double,
    DateTime,
    func,
    Enum as SAEnum,
    select
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker
)

# --- Base and Enum Definitions ---

class Base(DeclarativeBase):
    """The base class for all declarative models."""
    pass

class SubscriptionType(enum.IntEnum):
    """Enum for subscription quality types."""
    HD = 1
    FHD = 2
    UHD_4K = 3

# --- Models ---

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String, server_default="user")
    password: Mapped[bytes] = mapped_column(LargeBinary)
    access_token: Mapped[Optional[bytes]] = mapped_column(LargeBinary)
    user_sub: Mapped[Optional[int]] = mapped_column(ForeignKey("subscription.id"), nullable=True, server_default=None)
    is_deleted: Mapped[bool] = mapped_column(server_default="false")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="users")
    wishlist: Mapped["Wishlist"] = relationship(back_populates="user", cascade="all, delete-orphan")
    cart: Mapped["Cart"] = relationship(back_populates="user", cascade="all, delete-orphan")
    movies: Mapped[List["UserMovie"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscriptions_history: Mapped[List["UserSubscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def purchase_subscription(self, session, new_subscription: "Subscription"):
        """
        Handles the logic for purchasing a new subscription.
        - If the user has an active subscription of the same type, it extends the duration.
        - If the user has an active subscription of a different type, it deactivates the old one and creates a new one.
        - If the user has no active subscription, it creates a new one.
        """
        # Check for an active subscription
        active_subscription_stmt = select(UserSubscription).where(
            UserSubscription.user_id == self.id,
            UserSubscription.is_active == True
        )
        active_subscription = session.scalars(active_subscription_stmt).first()

        if active_subscription:
            if active_subscription.subscription_id == new_subscription.id:
                # Extend the current subscription
                active_subscription.end_date += datetime.timedelta(days=new_subscription.duration_days)
            else:
                # Upgrade: Deactivate the old subscription and create a new one
                active_subscription.is_active = False
                new_user_subscription = UserSubscription(
                    user_id=self.id,
                    subscription_id=new_subscription.id,
                    start_date=datetime.datetime.now(datetime.timezone.utc),
                    end_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=new_subscription.duration_days),
                    is_active=True
                )
                session.add(new_user_subscription)
        else:
            # No active subscription: Create a new one
            new_user_subscription = UserSubscription(
                user_id=self.id,
                subscription_id=new_subscription.id,
                start_date=datetime.datetime.now(datetime.timezone.utc),
                end_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=new_subscription.duration_days),
                is_active=True
            )
            session.add(new_user_subscription)

class Subscription(Base):
    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    type: Mapped[SubscriptionType] = mapped_column(SAEnum(SubscriptionType))
    duration_days: Mapped[int] = mapped_column(server_default="30")
    price: Mapped[float] = mapped_column(Double)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="subscription")
    user_subscriptions: Mapped[List["UserSubscription"]] = relationship(back_populates="subscription")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscription.id"))
    start_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(server_default="true")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscriptions_history")
    subscription: Mapped["Subscription"] = relationship(back_populates="user_subscriptions")

class Movie(Base):
    __tablename__ = "movie"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    time: Mapped[Optional[int]]
    price: Mapped[Optional[float]] = mapped_column(Double)
    description: Mapped[Optional[str]] = mapped_column(String)
    imdb_rate: Mapped[Optional[float]] = mapped_column(Float(2, 1))
    cover_url: Mapped[Optional[str]] = mapped_column(String)
    genre: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    wishlist_entries: Mapped[List["WishlistMovie"]] = relationship(back_populates="movie", cascade="all, delete-orphan")
    cart_entries: Mapped[List["CartMovie"]] = relationship(back_populates="movie", cascade="all, delete-orphan")
    user_movies: Mapped[List["UserMovie"]] = relationship(back_populates="movie")

class Wishlist(Base):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="wishlist")
    movies: Mapped[List["WishlistMovie"]] = relationship(back_populates="wishlist", cascade="all, delete-orphan")

class WishlistMovie(Base):
    __tablename__ = "wishlist_movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    wishlist_id: Mapped[int] = mapped_column(ForeignKey("wishlist.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    wishlist: Mapped["Wishlist"] = relationship(back_populates="movies")
    movie: Mapped["Movie"] = relationship(back_populates="wishlist_entries")

class Cart(Base):
    __tablename__ = "cart"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cart")
    movies: Mapped[List["CartMovie"]] = relationship(back_populates="cart", cascade="all, delete-orphan")

class CartMovie(Base):
    __tablename__ = "cart_movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart.id", ondelete="CASCADE"))
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id", ondelete="CASCADE"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="movies")
    movie: Mapped["Movie"] = relationship(back_populates="cart_entries")

class UserMovie(Base):
    __tablename__ = "user_movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movie.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    movie: Mapped["Movie"] = relationship(back_populates="user_movies")
    user: Mapped["User"] = relationship(back_populates="movies")