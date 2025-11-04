import asyncio
from rozo import create_rozo_payment
from lendasat import create_ln_payment_for_rozo


async def main() -> None:
    local_amount = 50.0

    receiving_address, usdc_amount = await create_rozo_payment(
        merchant_id="cafe", local_amount=local_amount
    )
    print(f"Payment created: {receiving_address} - {usdc_amount} USDC")

    ln_invoice, preimage = await create_ln_payment_for_rozo(
        receiving_address=receiving_address, usd_amount=usdc_amount
    )
    print(f"\nLightning Invoice: {ln_invoice}")
    print(f"Preimage (keep safe!): {preimage}")


if __name__ == "__main__":
    asyncio.run(main())
