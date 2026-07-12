import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..auth_utils import get_current_user
from ..database import get_db
from ..models import Listing, User
from ..schemas import ListingIn, ListingOut, ListingStatusPatchIn, RenewIn

router = APIRouter(prefix="/listings", tags=["listings"])

LISTING_TYPES = {"sell", "buy", "giveaway"}
LISTING_STATUSES = {"open", "sold", "expired", "removed"}
PATCHABLE_STATUSES = {"open", "sold", "removed"}
VALID_EXPIRY_DAYS = {7, 14, 30}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _expire_old_listings(db: Session) -> None:
    db.query(Listing).filter(
        Listing.status == "open",
        Listing.expires_at <= datetime.utcnow(),
    ).update({"status": "expired"}, synchronize_session=False)
    db.commit()


def _expire_listing_if_needed(listing: Listing, db: Session) -> None:
    if listing.status == "open" and listing.expires_at <= datetime.utcnow():
        listing.status = "expired"
        db.commit()
        db.refresh(listing)


def _require_seller(listing: Listing, user: User) -> None:
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="You can only modify your own listings")


@router.get("", response_model=list[ListingOut])
def list_listings(
    q: str | None = None,
    listing_type: str | None = None,
    status: str = Query(default="open"),
    lat: float | None = None,
    lng: float | None = None,
    radius_miles: float = Query(default=50.0, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _expire_old_listings(db)
    if not status:
        status = "open"
    if status not in LISTING_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    query = db.query(Listing).options(joinedload(Listing.seller))
    if status == "removed":
        query = query.filter(Listing.status == status, Listing.seller_id == user.id)
    else:
        query = query.filter(Listing.status == status)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Listing.title.ilike(like), Listing.description.ilike(like)))
    if listing_type:
        if listing_type not in LISTING_TYPES:
            raise HTTPException(status_code=400, detail="Invalid listing type")
        query = query.filter(Listing.listing_type == listing_type)

    listings = query.order_by(Listing.created_at.desc()).all()

    if lat is not None and lng is not None:
        listings = [
            item
            for item in listings
            if item.latitude is not None
            and item.longitude is not None
            and haversine_miles(lat, lng, item.latitude, item.longitude) <= radius_miles
        ]
    return listings


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status == "removed" and listing.seller_id != user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
    _expire_listing_if_needed(listing, db)
    return listing


@router.post("", response_model=ListingOut)
def create_listing(
    payload: ListingIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.listing_type not in LISTING_TYPES:
        raise HTTPException(status_code=400, detail="Invalid listing type")
    if payload.expires_in_days not in VALID_EXPIRY_DAYS:
        raise HTTPException(status_code=400, detail="expires_in_days must be 7, 14, or 30")

    data = payload.model_dump(exclude={"expires_in_days"})
    data["expires_at"] = datetime.utcnow() + timedelta(days=payload.expires_in_days)
    listing = Listing(**data, seller_id=user.id)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.patch("/{listing_id}/status", response_model=ListingOut)
def patch_listing_status(
    listing_id: int,
    payload: ListingStatusPatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    _require_seller(listing, user)

    if payload.status not in PATCHABLE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if payload.expires_in_days not in VALID_EXPIRY_DAYS:
        raise HTTPException(status_code=400, detail="expires_in_days must be 7, 14, or 30")

    _expire_listing_if_needed(listing, db)

    if payload.status == "sold":
        listing.status = "sold"
        listing.sold_at = datetime.utcnow()
    elif payload.status == "open":
        listing.status = "open"
        listing.sold_at = None
        listing.expires_at = datetime.utcnow() + timedelta(days=payload.expires_in_days)
    elif payload.status == "removed":
        listing.status = "removed"

    db.commit()
    db.refresh(listing)
    return listing


@router.post("/{listing_id}/renew", response_model=ListingOut)
def renew_listing(
    listing_id: int,
    payload: RenewIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    _require_seller(listing, user)

    if listing.status == "open":
        raise HTTPException(status_code=400, detail="Listing is already open")

    expires_in_days = payload.expires_in_days if payload else 30
    if expires_in_days not in VALID_EXPIRY_DAYS:
        raise HTTPException(status_code=400, detail="expires_in_days must be 7, 14, or 30")

    listing.status = "open"
    listing.sold_at = None
    listing.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}")
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    _require_seller(listing, user)
    _expire_listing_if_needed(listing, db)
    listing.status = "removed"
    db.commit()
    return {"message": "Listing removed"}
