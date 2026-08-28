from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class WhatsAppVerificationParams(BaseModel):
    hub_mode: Optional[str] = Field(None, alias="hub.mode")
    hub_verify_token: Optional[str] = Field(None, alias="hub.verify_token")
    hub_challenge: Optional[str] = Field(None, alias="hub.challenge")

    model_config = ConfigDict(populate_by_name=True)


class WhatsAppTextMessage(BaseModel):
    body: str
    model_config = ConfigDict(extra="ignore")


class WhatsAppIncomingMessage(BaseModel):
    id: str
    from_: str = Field(..., alias="from")
    timestamp: str
    type: str
    text: Optional[WhatsAppTextMessage] = None
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class WhatsAppContactProfile(BaseModel):
    name: Optional[str] = None
    model_config = ConfigDict(extra="ignore")


class WhatsAppContact(BaseModel):
    profile: Optional[WhatsAppContactProfile] = None
    wa_id: str
    model_config = ConfigDict(extra="ignore")


class WhatsAppMetadata(BaseModel):
    display_phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None
    model_config = ConfigDict(extra="ignore")


class WhatsAppChangeValue(BaseModel):
    messaging_product: Optional[str] = "whatsapp"
    metadata: Optional[WhatsAppMetadata] = None
    contacts: Optional[List[WhatsAppContact]] = None
    messages: Optional[List[WhatsAppIncomingMessage]] = None
    statuses: Optional[List[Dict[str, Any]]] = None
    model_config = ConfigDict(extra="ignore")


class WhatsAppChange(BaseModel):
    value: WhatsAppChangeValue
    field: str
    model_config = ConfigDict(extra="ignore")


class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChange]
    model_config = ConfigDict(extra="ignore")


class WhatsAppWebhookPayload(BaseModel):
    object: Optional[str] = None
    entry: Optional[List[WhatsAppEntry]] = None
    model_config = ConfigDict(extra="ignore")
