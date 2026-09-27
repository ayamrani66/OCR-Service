import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


def parse_number(value):
    if value is None or isinstance(value, (int, float)):
        return value

    text = str(value).strip()
    text = re.sub(r"[^\d,.\-]", "", text)

    # Format français : 4 300,00 → 4300.00
    if "," in text:
        text = text.replace(".", "").replace(",", ".")

    return float(text)


class Vendor(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    tax_number: Optional[str] = None


class Client(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    tax_number: Optional[str] = None


class LineItem(BaseModel):
    description: str = ""
    quantity: float = 0
    unit_price: float = 0
    tax_rate: Optional[float] = None
    total: float = 0

    @field_validator(
        "quantity",
        "unit_price",
        "tax_rate",
        "total",
        mode="before",
    )
    @classmethod
    def convert_numbers(cls, value):
        if value is None:
            return None

        is_percentage = isinstance(value, str) and "%" in value
        number = parse_number(value)

        # "20 %" devient 0.20
        if is_percentage:
            return number / 100

        return number


class Invoice(BaseModel):
    pages: list[int] = Field(default_factory=list)
    document_type: str = "unknown"
    vendor: Vendor = Field(default_factory=Vendor)
    client: Client = Field(default_factory=Client)
    number: Optional[str] = None
    issued_at: Optional[str] = None
    due_at: Optional[str] = None
    currency: Optional[str] = None
    line_items: list[LineItem] = Field(default_factory=list)
    sub_total: Optional[float] = None
    tax_total: Optional[float] = None
    grand_total: Optional[float] = None
    raw_text: str = ""

    @field_validator(
        "sub_total",
        "tax_total",
        "grand_total",
        mode="before",
    )
    @classmethod
    def convert_totals(cls, value):
        return parse_number(value)


class OcrResult(BaseModel):
    invoices: list[Invoice] = Field(default_factory=list)