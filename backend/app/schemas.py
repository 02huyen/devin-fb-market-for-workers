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


class SellerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    domain: str
    company_name: str
    display_name: str


class ListingIn(BaseModel):
    title: str
    description: str = ""
    listing_type: str  # sell | buy | giveaway
    price: float = 0.0
    location_name: str = ""
    latitude: float | None = None
    longitude: float | None = None


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
    is_active: bool
    created_at: datetime
    seller: SellerOut


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
    body: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: int
    body: str
    created_at: datetime
    read_at: datetime | None
    sender: ConversationParticipantOut


class ConversationIn(BaseModel):
    body: str | None = None


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
