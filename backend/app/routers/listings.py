import math
import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..auth_utils import get_current_user
from ..database import get_db
from ..models import Comment, Listing, ListingImage, User
from ..schemas import CommentIn, CommentOut, ListingImageOut, ListingIn, ListingOut

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


router = APIRouter(prefix="/listings", tags=["listings"])

LISTING_TYPES = {"sell", "buy", "giveaway"}


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


STATUSES = {"open", "sold", "expired"}


@router.get("", response_model=list[ListingOut])
def list_listings(
    q: str | None = None,
    listing_type: str | None = None,
    status: str | None = "open",
    lat: float | None = None,
    lng: float | None = None,
    radius_miles: float = Query(default=50.0, gt=0),
    seller_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    # Auto-expire any open listings past their expiration date.
    db.query(Listing).filter(
        Listing.status == "open",
        Listing.expires_at.isnot(None),
        Listing.expires_at < datetime.utcnow(),
    ).update({"status": "expired"}, synchronize_session=False)
    db.commit()

    query = (
        db.query(Listing)
        .options(joinedload(Listing.seller), joinedload(Listing.images))
        .filter(Listing.is_active.is_(True))
    )
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Listing.title.ilike(like), Listing.description.ilike(like)))
    if listing_type:
        if listing_type not in LISTING_TYPES:
            raise HTTPException(status_code=400, detail="Invalid listing type")
        query = query.filter(Listing.listing_type == listing_type)
    if status:
        if status not in STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        query = query.filter(Listing.status == status)
    if seller_id is not None:
        query = query.filter(Listing.seller_id == seller_id)

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
    data = payload.model_dump()
    expiry_days = data.pop("expiry_days", 7) or 7
    if expiry_days < 1 or expiry_days > 365:
        raise HTTPException(status_code=400, detail="expiry_days must be between 1 and 365")
    data["expires_at"] = datetime.utcnow() + timedelta(days=expiry_days)
    listing = Listing(**data, seller_id=user.id)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    listing = (
        db.query(Listing)
        .options(joinedload(Listing.seller), joinedload(Listing.images))
        .filter(Listing.id == listing_id)
        .first()
    )
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.post("/{listing_id}/images", response_model=ListingImageOut)
def upload_image(
    listing_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="You can only upload images to your own listings")

    ext = Path(file.filename or "image").suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{listing_id}_{timestamp}{ext}"
    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    image_url = f"/uploads/{filename}"
    image = ListingImage(listing_id=listing_id, url=image_url)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.post("/{listing_id}/sold", response_model=ListingOut)
def mark_sold(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="You can only update your own listings")
    listing.status = "sold"
    db.commit()
    db.refresh(listing)
    return listing


@router.post("/{listing_id}/renew", response_model=ListingOut)
def renew_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="You can only update your own listings")
    listing.status = "open"
    listing.expires_at = datetime.utcnow() + timedelta(days=7)
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


@router.get("/{listing_id}/comments", response_model=list[CommentOut])
def list_comments(
    listing_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter(Comment.listing_id == listing_id)
        .order_by(Comment.created_at.desc())
        .all()
    )


@router.post("/{listing_id}/comments", response_model=CommentOut)
def create_comment(
    listing_id: int,
    payload: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != "open":
        raise HTTPException(status_code=403, detail="This listing is no longer open for comments")
    comment = Comment(text=payload.text.strip(), listing_id=listing_id, user_id=user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
