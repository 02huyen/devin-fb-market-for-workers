from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from ..auth_utils import get_current_user
from ..database import get_db
from ..models import Conversation, Listing, Message, User
from ..schemas import ConversationIn, ConversationOut, MessageIn, MessageOut

router = APIRouter(tags=["messages"])


def _participant_check(conversation: Conversation, user: User) -> None:
    seller_id = conversation.listing.seller_id if conversation.listing else None
    if conversation.buyer_id != user.id and seller_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the buyer and the listing seller can access this conversation",
        )


def _build_conversation(
    db: Session, conversation: Conversation, user: User
) -> ConversationOut:
    listing = conversation.listing
    seller = listing.seller
    buyer = conversation.buyer
    other = seller if user.id == conversation.buyer_id else buyer

    if user.id == conversation.buyer_id:
        unread_count = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id,
                Message.read_at.is_(None),
                Message.sender_id == seller.id,
            )
            .count()
        )
    else:
        unread_count = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id,
                Message.read_at.is_(None),
                Message.sender_id == buyer.id,
            )
            .count()
        )

    last_message = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .first()
    )

    return ConversationOut(
        id=conversation.id,
        listing_id=conversation.listing_id,
        buyer_id=conversation.buyer_id,
        listing={
            "id": listing.id,
            "title": listing.title,
            "listing_type": listing.listing_type,
        },
        other_participant={
            "id": other.id,
            "display_name": other.display_name,
            "company_name": other.company_name,
        },
        unread_count=unread_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_message=MessageOut.model_validate(last_message)
        if last_message
        else None,
    )


@router.post("/listings/{listing_id}/conversations", response_model=ConversationOut, status_code=201)
def start_conversation(
    listing_id: int,
    payload: ConversationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id == user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot start a conversation about your own listing",
        )

    conversation = (
        db.query(Conversation)
        .filter_by(listing_id=listing_id, buyer_id=user.id)
        .first()
    )
    if not conversation:
        conversation = Conversation(listing_id=listing_id, buyer_id=user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    if payload.body:
        message = Message(
            conversation_id=conversation.id,
            sender_id=user.id,
            body=payload.body,
        )
        db.add(message)
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)

    # Eager-load the relationships needed for the response.
    conversation = (
        db.query(Conversation)
        .options(joinedload(Conversation.listing).joinedload(Listing.seller))
        .options(joinedload(Conversation.buyer))
        .filter(Conversation.id == conversation.id)
        .first()
    )
    return _build_conversation(db, conversation, user)


@router.get("/conversations", response_model=list[ConversationOut])
def get_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .join(Conversation.listing)
        .filter(
            or_(
                Conversation.buyer_id == user.id,
                Listing.seller_id == user.id,
            )
        )
        .options(joinedload(Conversation.listing).joinedload(Listing.seller))
        .options(joinedload(Conversation.buyer))
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [_build_conversation(db, c, user) for c in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .options(joinedload(Conversation.listing))
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    _participant_check(conversation, user)

    # Mark messages from the other participant as read when this participant opens
    # the thread.
    db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != user.id,
        Message.read_at.is_(None),
    ).update({Message.read_at: datetime.utcnow()})
    db.commit()

    messages = (
        db.query(Message)
        .options(joinedload(Message.sender))
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def create_message(
    conversation_id: int,
    payload: MessageIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .options(joinedload(Conversation.listing))
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    _participant_check(conversation, user)

    message = Message(
        conversation_id=conversation_id,
        sender_id=user.id,
        body=payload.body,
    )
    db.add(message)
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message
