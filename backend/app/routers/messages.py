from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..auth_utils import get_current_user
from ..database import get_db
from ..models import Conversation, Listing, Message, User
from ..schemas import ConversationOut, MessageIn, MessageOut

router = APIRouter(prefix="/messages", tags=["messages"])


def _conversation_out(conv: Conversation, user: User) -> dict:
    unread = sum(
        1
        for m in conv.messages
        if m.sender_id != user.id and m.read_at is None
    )
    return {
        "id": conv.id,
        "listing_id": conv.listing_id,
        "buyer": conv.buyer,
        "seller": conv.seller,
        "updated_at": conv.updated_at,
        "created_at": conv.created_at,
        "unread_count": unread,
    }


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    convs = (
        db.query(Conversation)
        .options(
            joinedload(Conversation.listing),
            joinedload(Conversation.buyer),
            joinedload(Conversation.seller),
            joinedload(Conversation.messages),
        )
        .filter((Conversation.buyer_id == user.id) | (Conversation.seller_id == user.id))
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_conversation_out(c, user) for c in convs]


@router.post("/conversations", response_model=ConversationOut)
def start_conversation(
    listing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id == user.id:
        raise HTTPException(status_code=400, detail="You cannot message yourself")

    existing = (
        db.query(Conversation)
        .filter(
            Conversation.listing_id == listing_id,
            Conversation.buyer_id == user.id,
            Conversation.seller_id == listing.seller_id,
        )
        .first()
    )
    if existing:
        return _conversation_out(existing, user)

    conv = Conversation(
        listing_id=listing_id,
        buyer_id=user.id,
        seller_id=listing.seller_id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _conversation_out(conv, user)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.buyer_id != user.id and conv.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not your conversation")
    return (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut)
def send_message(
    conversation_id: int,
    payload: MessageIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.buyer_id != user.id and conv.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not your conversation")
    msg = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        text=payload.text.strip(),
    )
    db.add(msg)
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


@router.post("/conversations/{conversation_id}/read")
def mark_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conv.buyer_id != user.id and conv.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Not your conversation")
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != user.id,
        Message.read_at.is_(None),
    ).update({"read_at": datetime.utcnow()}, synchronize_session=False)
    db.commit()
    return {"message": "Marked as read"}
