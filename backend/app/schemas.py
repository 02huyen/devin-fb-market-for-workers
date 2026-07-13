from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class RequestLinkIn(BaseModel):
    email: EmailStr


class RequestLinkOut(BaseModel):
    message: str
    # Dev-mode only: returned so the flow is testable without an email provider.
    dev_magic_link: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    domain: str
    company_name: str
    display_name: str
    is_verified: bool


class UserUpdate(BaseModel):
    display_name: str


class SellerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    domain: str
    company_name: str
    display_name: str


class ListingImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    created_at: datetime


class CommentIn(BaseModel):
    text: str


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    user: UserOut


class ConversationParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    company_name: str


class ListingSnippetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    listing_type: str


class MessageIn(BaseModel):
    text: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    text: str
    created_at: datetime
    read_at: datetime | None
    sender: ConversationParticipantOut


class ConversationIn(BaseModel):
    text: str | None = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    listing_id: int
    buyer_id: int
    listing: ListingSnippetOut
    other_participant: ConversationParticipantOut
    unread_count: int
    created_at: datetime
    updated_at: datetime
    last_message: MessageOut | None


class ListingIn(BaseModel):
    title: str
    description: str = ""
    listing_type: str  # sell | buy | giveaway
    price: float = 0.0
    location_name: str = ""
    latitude: float | None = None
    longitude: float | None = None
    expiry_days: int | None = None  # for frontend compatibility
    expires_in_days: int | None = None  # default 7 | 14 | 30


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    listing_type: str
    price: float
    location_name: str
    latitude: float | None
    longitude: float | None
    status: str  # open | sold | expired | removed
    expires_at: datetime
    sold_at: datetime | None
    is_active: bool
    created_at: datetime
    seller: SellerOut
    images: list[ListingImageOut] = []


class ListingStatusPatchIn(BaseModel):
    status: str  # open | sold | removed
    expires_in_days: int | None = None
    expiry_days: int | None = None


class RenewIn(BaseModel):
    expires_in_days: int | None = None
    expiry_days: int | None = None
