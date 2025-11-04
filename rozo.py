import httpx
import json
import time
import secrets
from typing import cast, TypedDict, Any

API_URL = "https://intentapiv2.rozo.ai/functions/v1//payment-api"
AUTH_HEADER = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4Y3Zmb2xobmNtdXZmYXp1cXViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI4Mzg2NjYsImV4cCI6MjA2ODQxNDY2Nn0.B4dV5y_-zCMKSNm3_qyCbAvCPJmoOGv_xB783LfAVUA"
AUTH_HEADER_MERCHANTS = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVzZ3NvaWxpdGFkd3V0ZnZ4ZnpxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI0NjM2ODMsImV4cCI6MjA1ODAzOTY4M30.bq18ZyzdwRXi0AFLip_37urLoAI1wk6giYjQAho-Q5E"
MERCHANTS_API_URL = (
    "https://usgsoilitadwutfvxfzq.supabase.co/rest/v1/merchants?select=*"
)


class MerchantDict(TypedDict, total=False):
    id: str
    name: str
    logo_url: str | None
    description: str
    currency: str
    prepaid_amount: float
    owner_id: str | None
    created_at: str
    updated_at: str
    user_id: str | None
    phone: str | None
    cashback: int | None


class ServiceConfigDict(TypedDict):
    app_id: str
    intent_template: str
    item_name: str
    item_desc_template: str
    currency_local: str
    order_prefix: str
    deeplink: str


SERVICE_CONFIG: dict[str, ServiceConfigDict] = {}


async def fetch_merchants() -> list[MerchantDict]:
    headers = {
        "Authorization": AUTH_HEADER_MERCHANTS,
        "apikey": AUTH_HEADER_MERCHANTS.replace("Bearer ", ""),
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(MERCHANTS_API_URL, headers=headers)
    response.raise_for_status()
    merchants = [
        m for m in cast(list[MerchantDict], response.json()) if m["id"] != "cafee"
    ]

    for m in merchants:
        if m["id"] == "ride":
            m["name"] = "Ride (SG <> NS)"

    priority_order = ["cafe", "laundry", "ride", "spa", "meisan"]
    priority_map = {mid: i for i, mid in enumerate(priority_order)}

    return sorted(
        merchants,
        key=lambda m: (priority_map.get(m["id"], len(priority_order)), m["name"]),
    )


def build_service_config(merchant: MerchantDict) -> ServiceConfigDict:
    return {
        "app_id": f"nsrozoRewardsMP-{merchant['id']}",
        "intent_template": f"Pay for {merchant['name']} - ${{usd_amount}}",
        "item_name": merchant["name"],
        "item_desc_template": f"{merchant['currency']} {{local_amount}} ({{usd_amount}} USD)",
        "currency_local": merchant["currency"],
        "order_prefix": merchant["id"].upper(),
        "deeplink": f"https://ns.rozo.ai/ns/{merchant['id']}?amount={{local_amount}}",
    }


async def load_service_config() -> None:
    global SERVICE_CONFIG
    merchants = await fetch_merchants()
    SERVICE_CONFIG = {m["id"]: build_service_config(m) for m in merchants}


class DisplayDict(TypedDict):
    intent: str
    currency: str


class DestinationDict(TypedDict):
    destinationAddress: str
    txHash: str | None
    chainId: str
    amountUnits: str
    tokenSymbol: str
    tokenAddress: str


class ItemDict(TypedDict):
    name: str
    description: str


class MetadataDict(TypedDict, total=False):
    preferredChain: str
    preferredToken: str
    preferredTokenAddress: str
    intent: str
    items: list[ItemDict]
    payer: dict[str, Any]
    appId: str
    amount_local: str
    currency_local: str
    merchant_order_id: str
    receiptUrl: str
    customDeeplinkUrl: str
    provider: str
    receivingAddress: str
    memo: str | None
    payinchainid: str
    payintokenaddress: str
    daimoOrderId: str


class PaymentApiResponseDict(TypedDict):
    id: str
    status: str
    createdAt: str
    display: DisplayDict
    source: Any | None
    destination: DestinationDict
    metadata: MetadataDict
    url: str


def generate_order_id() -> str:
    return secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:11].lower()


def parse_payment_response(response: PaymentApiResponseDict) -> tuple[str, float]:
    return (
        response["metadata"].get(
            "receivingAddress", response["destination"]["destinationAddress"]
        ),
        float(response["destination"]["amountUnits"]),
    )


def create_payment_request(
    service: str, local_amount: float, usd_amount: float
) -> dict:
    config = SERVICE_CONFIG[service]
    timestamp = int(time.time() * 1000)
    order_id = f"{config['order_prefix']}-{timestamp}"
    daimo_order_id = generate_order_id()

    intent = config["intent_template"].format(usd_amount=f"{usd_amount:.2f}")
    item_desc = config["item_desc_template"].format(
        local_amount=int(local_amount) if local_amount.is_integer() else local_amount,
        usd_amount=f"{usd_amount:.2f}",
    )

    return {
        "appId": config["app_id"],
        "display": {
            "intent": intent,
            "paymentValue": str(usd_amount),
            "currency": "USD",
        },
        "destination": {
            "destinationAddress": "0x5772FBe7a7817ef7F586215CA8b23b8dD22C8897",
            "chainId": "8453",
            "amountUnits": str(usd_amount),
            "tokenSymbol": "USDC",
            "tokenAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        },
        "externalId": "",
        "metadata": {
            "daimoOrderId": daimo_order_id,
            "preferredChain": "137",
            "preferredToken": "USDC",
            "preferredTokenAddress": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "intent": intent,
            "items": [
                {"name": config["item_name"], "description": item_desc},
                {"name": "Order ID", "description": order_id},
            ],
            "payer": {},
            "appId": config["app_id"],
            "amount_local": str(
                int(local_amount) if local_amount.is_integer() else local_amount
            ),
            "currency_local": config["currency_local"],
            "merchant_order_id": order_id,
            "receiptUrl": f"https://ns.rozo.ai/payment/success?order_id={order_id}",
            "customDeeplinkUrl": config["deeplink"].format(
                local_amount=int(local_amount)
                if local_amount.is_integer()
                else local_amount
            ),
        },
        "preferredChain": "137",
        "preferredToken": "USDC",
        "preferredTokenAddress": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    }


async def convert_currency_to_usd(amount: float, currency: str = "MYR") -> float:
    currency_map = {"RM": "MYR", "MYR": "MYR"}
    iso_currency = currency_map.get(currency, currency)
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.exchangerate-api.com/v4/latest/USD")
    response.raise_for_status()
    data = response.json()
    rate = 1.0 / data["rates"][iso_currency]
    return round(amount * rate, 2)


async def create_rozo_payment(
    merchant_id: str, local_amount: float
) -> tuple[str, float]:
    currency = SERVICE_CONFIG[merchant_id]["currency_local"]
    usd_amount = (
        await convert_currency_to_usd(local_amount, currency)
        if currency != "USD"
        else local_amount
    )
    payload = create_payment_request(merchant_id, local_amount, usd_amount)
    headers = {"Content-Type": "application/json", "Authorization": AUTH_HEADER}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            API_URL, headers=headers, content=json.dumps(payload)
        )

    response.raise_for_status()
    return parse_payment_response(cast(PaymentApiResponseDict, response.json()))
