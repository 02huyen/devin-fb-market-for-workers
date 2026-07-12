from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth_utils import get_current_user
from ..database import get_db
from ..models import Comment, Listing, User
from ..schemas import CommentIn, CommentOut

router = APIRouter(tags=["comments"])


@router.get("/listings/{listing_id}/comments", response_model=list[CommentOut])
def get_listing_comments(
    listing_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    comments = (
        db.query(Comment)
        .filter(Comment.listing_id == listing_id, Comment.is_deleted.is_(False))
        .order_by(Comment.created_at.asc())
        .all()
    )
    return comments


@router.post("/listings/{listing_id}/comments", response_model=CommentOut, status_code=201)
def create_comment(
    listing_id: int,
    payload: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.is_active:
        raise HTTPException(status_code=400, detail="Listing is not open for comments")

    comment = Comment(
        listing_id=listing_id,
        author_id=user.id,
        body=payload.body,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    comment = db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    listing = db.get(Listing, comment.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if comment.author_id != user.id and listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Only the author or listing owner can delete this comment")

    comment.is_deleted = True
    db.commit()
    return {"message": "Comment removed"}
