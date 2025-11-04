import httpx
import secrets
import hashlib
import os
from typing import TypedDict

API_URL = "https://apilendaswap.lendasat.com/swap"
REFERRAL_CODE = os.getenv("LENDASAT_REFERRAL_CODE")
REFUND_PK = "024b4b4b4f6e4e4593fd430ec04f23f6b56276f1a8e4280d5988b326374aee050a"


class SwapSecret(TypedDict):
    preimage: str
    hash_lock: str


class LendasatResponse(TypedDict):
    id: str
    polygon_address: str
    arkade_address: str
    ln_invoice: str
    sats_required: int
    fee_sats: int
    usd_amount: float
    usd_per_sat: float
    hash_lock: str
    sender_pk: str
    receiver_pk: str
    server_pk: str
    refund_locktime: int
    unilateral_claim_delay: int
    unilateral_refund_delay: int
    unilateral_refund_without_receiver_delay: int
    network: str


def generate_hash_lock() -> SwapSecret:
    preimage = secrets.token_bytes(32)
    hash_lock = "0x" + hashlib.sha256(preimage).hexdigest()
    return {"preimage": "0x" + preimage.hex(), "hash_lock": hash_lock}


async def create_lightning_invoice(
    polygon_address: str, usd_amount: float
) -> tuple[LendasatResponse, str]:
    secret = generate_hash_lock()
    payload = {
        "polygon_address": polygon_address,
        "usd_amount": usd_amount,
        "target_token": "usdc_pol",
        "hash_lock": secret["hash_lock"],
        "refund_pk": REFUND_PK,
        "referral_code": REFERRAL_CODE,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, json=payload)

    response.raise_for_status()
    return response.json(), secret["preimage"]


async def create_ln_payment_for_rozo(
    receiving_address: str, usd_amount: float
) -> tuple[str, str, int]:
    invoice_data, preimage = await create_lightning_invoice(
        receiving_address, usd_amount
    )
    return invoice_data["ln_invoice"], preimage, invoice_data["sats_required"]
