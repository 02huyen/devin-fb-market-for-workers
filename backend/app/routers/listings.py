import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..auth_utils import get_current_user
from ..database import get_db
from ..models import Listing, User
from ..schemas import ListingIn, ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])

LISTING_TYPES = {"sell", "buy", "giveaway"}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@router.get("", response_model=list[ListingOut])
def list_listings(
    q: str | None = None,
    listing_type: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    radius_miles: float = Query(default=50.0, gt=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = (
        db.query(Listing)
        .options(joinedload(Listing.seller))
        .filter(Listing.is_active.is_(True))
    )
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


@router.post("", response_model=ListingOut)
def create_listing(
    payload: ListingIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.listing_type not in LISTING_TYPES:
        raise HTTPException(status_code=400, detail="Invalid listing type")
    listing = Listing(**payload.model_dump(), seller_id=user.id)
    db.add(listing)
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
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own listings")
    listing.is_active = False
    db.commit()
    return {"message": "Listing removed"}
