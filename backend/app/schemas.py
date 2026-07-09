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
