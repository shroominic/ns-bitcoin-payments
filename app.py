from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import qrcode
import io
import base64
from rozo import create_rozo_payment, load_service_config, fetch_merchants, MerchantDict
from lendasat import create_ln_payment_for_rozo

app = FastAPI()


@app.on_event("startup")
async def startup_event() -> None:
    await load_service_config()


class PaymentRequest(BaseModel):
    amount: float
    service: str


@app.get("/api/merchants")
async def get_merchants() -> list[MerchantDict]:
    return await fetch_merchants()


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Lightning Payment</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container { 
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            max-width: 480px;
            width: 100%;
        }
        h1 { 
            color: #fff;
            margin-bottom: 32px;
            text-align: center;
            font-size: 28px;
            font-weight: 600;
        }
        .form-group { margin-bottom: 24px; }
        label { 
            display: block;
            margin-bottom: 12px;
            color: #999;
            font-weight: 500;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .service-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
            gap: 12px;
            padding: 2px;
        }
        .service-grid.expanded {
            max-height: 400px;
            overflow-y: auto;
        }
        .service-grid::-webkit-scrollbar {
            width: 8px;
        }
        .service-grid::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }
        .service-grid::-webkit-scrollbar-thumb {
            background: #333;
            border-radius: 4px;
        }
        .service-grid::-webkit-scrollbar-thumb:hover {
            background: #444;
        }
        .show-all-link {
            grid-column: 1 / -1;
            text-align: center;
            color: #f7931a;
            font-size: 14px;
            text-decoration: underline;
            cursor: pointer;
            padding: 8px;
            transition: color 0.2s;
        }
        .show-all-link:hover {
            color: #ff6b35;
        }
        .service-card {
            background: #242424;
            border: 2px solid #333;
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }
        .service-card:hover {
            border-color: #555;
            transform: translateY(-2px);
        }
        .service-card.selected {
            background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%);
            border-color: #f7931a;
        }
        .service-icon {
            font-size: 32px;
            margin-bottom: 8px;
        }
        .service-name {
            color: #fff;
            font-weight: 600;
            font-size: 15px;
        }
        .amount-input-wrapper {
            position: relative;
        }
        .amount-input-wrapper input {
            width: 100%;
            padding: 16px 60px 16px 16px;
            background: #242424;
            border: 2px solid #333;
            border-radius: 12px;
            color: #fff;
            font-size: 20px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .amount-input-wrapper input:focus {
            outline: none;
            border-color: #f7931a;
            background: #2a2a2a;
        }
        .amount-input-wrapper input::placeholder {
            color: #555;
        }
        .currency-label {
            position: absolute;
            right: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: #999;
            font-size: 18px;
            font-weight: 600;
            pointer-events: none;
        }
        button { 
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #f7931a 0%, #ff6b35 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(247, 147, 26, 0.4);
        }
        button:disabled { 
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        #result { 
            margin-top: 32px;
            display: none;
        }
        #qrcode { 
            text-align: center;
            margin: 0 0 20px 0;
            background: white;
            padding: 16px;
            border-radius: 12px;
            display: inline-block;
            width: 100%;
        }
        #qrcode img { 
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
        }
        .invoice-box { 
            background: #242424;
            border: 1px solid #333;
            padding: 16px;
            border-radius: 12px;
        }
        .sats-amount {
            font-size: 24px;
            font-weight: 600;
            color: #f7931a;
            text-align: center;
            margin-bottom: 16px;
            padding: 12px;
            background: #1a1a1a;
            border-radius: 8px;
        }
        .invoice-text { 
            word-break: break-all;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 11px;
            color: #ccc;
            max-height: 100px;
            overflow-y: auto;
            margin-bottom: 12px;
            line-height: 1.5;
        }
        .copy-btn { 
            padding: 10px 18px;
            width: auto;
            font-size: 14px;
            background: #2a2a2a;
            border: 1px solid #444;
        }
        .copy-btn:hover { 
            background: #333;
            box-shadow: none;
        }
        .loading { 
            text-align: center;
            color: #f7931a;
            margin-top: 20px;
            display: none;
            font-size: 16px;
        }
        .error { 
            background: #ff3838;
            color: white;
            padding: 14px;
            border-radius: 10px;
            margin-top: 16px;
            display: none;
            font-size: 14px;
        }
        .merchant-info {
            background: #242424;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 12px 16px;
            margin-top: 16px;
            display: none;
            font-size: 13px;
            color: #ccc;
            line-height: 1.6;
        }
        .merchant-info a {
            color: #f7931a;
            text-decoration: none;
        }
        .merchant-info a:hover {
            text-decoration: underline;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            max-width: 480px;
            width: 100%;
        }
        .warning {
            padding: 10px;
            margin-bottom: 12px;
            font-size: 11px;
            color: #555;
            line-height: 1.4;
        }
        .warning a {
            color: #666;
            text-decoration: none;
        }
        .warning a:hover {
            color: #888;
            text-decoration: underline;
        }
        .powered-by {
            font-size: 11px;
            color: #444;
        }
        .powered-by a {
            color: #666;
            text-decoration: none;
            transition: color 0.2s;
        }
        .powered-by a:hover {
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ NS Lightning Payments</h1>
        <form id="paymentForm">
            <div class="form-group">
                <label>Select Recipient</label>
                <div class="service-grid" id="serviceGrid">
                    <div class="loading" style="grid-column: 1 / -1; text-align: center; color: #999;">Loading merchants...</div>
                </div>
                <div class="merchant-info" id="merchantInfo"></div>
            </div>
            <div class="form-group">
                <label>Amount</label>
                <div class="amount-input-wrapper">
                    <input type="number" id="amount" step="0.01" min="0.01" placeholder="0.00" required>
                    <span class="currency-label" id="currencyLabel">RM</span>
                </div>
            </div>
            <button type="submit" id="submitBtn">⚡ Pay Now</button>
        </form>
        <div class="loading" id="loading">⚡ Generating invoice...</div>
        <div class="error" id="error"></div>
        <div id="result">
            <div id="qrcode"></div>
            <div class="sats-amount" id="satsAmount"></div>
            <div class="invoice-box">
                <div class="invoice-text" id="invoice"></div>
                <button class="copy-btn" onclick="copyInvoice()">📋 Copy Invoice</button>
            </div>
        </div>
    </div>
    <div class="footer">
        <div class="warning">
            Use at your own risk. Developer not responsible for any loss.<br>
            You can <a href="https://github.com/shroominic/ns-bitcoin-payments" target="_blank">review code and self-host</a> on GitHub.
        </div>
        <div class="powered-by">
            Powered by <a href="https://ns.rozo.ai" target="_blank">Rozo</a> and <a href="https://swap.lendasat.com" target="_blank">Lendasat</a>
        </div>
    </div>
    <script>
        let selectedService = null;
        let merchants = [];
        
        const merchantIcons = {
            cafe: '☕', cafee: '☕', kindred: '☕',
            ride: '🚗', rideshare: '🚗',
            cacao: '🍫', dol: '🍝', nibbles: '🍪',
            spa: '💆', laundry: '👔', mart: '🛒',
            sam: '📚', bundles: '💻', zen: '💻',
            party: '🎉', coconut: '🥥', meisan: '🍜',
            kurtas: '👔'
        };
        
        function renderMerchants(showAll = false) {
            const serviceGrid = document.getElementById('serviceGrid');
            const displayCount = showAll ? merchants.length : 4;
            const displayMerchants = merchants.slice(0, displayCount);
            
            if (showAll) {
                serviceGrid.classList.add('expanded');
            } else {
                serviceGrid.classList.remove('expanded');
            }
            
            serviceGrid.innerHTML = displayMerchants.map(m => `
                <div class="service-card" data-service="${m.id}" data-currency="${m.currency}">
                    <div class="service-icon">${merchantIcons[m.id] || '🏪'}</div>
                    <div class="service-name">${m.name}</div>
                </div>
            `).join('');
            
            if (!showAll && merchants.length > 4) {
                serviceGrid.innerHTML += '<div class="show-all-link" onclick="showAllMerchants()">Show all</div>';
            }
            
            document.querySelectorAll('.service-card').forEach(card => {
                card.addEventListener('click', () => {
                    document.querySelectorAll('.service-card').forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    selectedService = card.dataset.service;
                    document.getElementById('currencyLabel').textContent = card.dataset.currency;
                    updateMerchantInfo(card.dataset.service);
                });
            });
            
            if (merchants.length > 0) {
                const firstCard = document.querySelector('.service-card');
                firstCard.classList.add('selected');
                selectedService = merchants[0].id;
                document.getElementById('currencyLabel').textContent = merchants[0].currency;
                updateMerchantInfo(merchants[0].id);
            }
        }
        
        function updateMerchantInfo(merchantId) {
            const merchantInfo = document.getElementById('merchantInfo');
            if (merchantId === 'ride') {
                merchantInfo.innerHTML = `
                    Book taxi over <a href="https://wa.me/60192551688" target="_blank">WhatsApp</a> or their 
                    <a href="https://sgmytaxi288service.com/" target="_blank">Website</a> and ask if they accept 
                    <a href="https://ns.rozo.ai/ns/ride" target="_blank">Rozo</a> as payment. 
                    Message @shawnmuggle on discord for payment issues.
                `;
                merchantInfo.style.display = 'block';
            } else {
                merchantInfo.style.display = 'none';
            }
        }
        
        function showAllMerchants() {
            renderMerchants(true);
        }
        
        async function loadMerchants() {
            const serviceGrid = document.getElementById('serviceGrid');
            try {
                const response = await fetch('/api/merchants');
                merchants = await response.json();
                renderMerchants(false);
            } catch (err) {
                serviceGrid.innerHTML = '<div style="grid-column: 1 / -1; color: #ff3838;">Failed to load merchants</div>';
            }
        }
        
        loadMerchants();
        
        const form = document.getElementById('paymentForm');
        const submitBtn = document.getElementById('submitBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        const error = document.getElementById('error');
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const amount = parseFloat(document.getElementById('amount').value);
            
            submitBtn.disabled = true;
            loading.style.display = 'block';
            result.style.display = 'none';
            error.style.display = 'none';
            
            try {
                const response = await fetch('/create-invoice', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ amount, service: selectedService })
                });
                
                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.detail || 'Failed to create invoice');
                }
                
                const data = await response.json();
                
                document.getElementById('qrcode').innerHTML = 
                    `<img src="data:image/png;base64,${data.qr_code}" alt="QR Code" style="max-width: 280px;" />`;
                document.getElementById('satsAmount').textContent = `₿${data.sats.toLocaleString()}`;
                document.getElementById('invoice').textContent = data.invoice;
                
                result.style.display = 'block';
            } catch (err) {
                error.textContent = err.message;
                error.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        });
        
        async function copyInvoice() {
            const invoice = document.getElementById('invoice').textContent;
            await navigator.clipboard.writeText(invoice);
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            setTimeout(() => btn.textContent = originalText, 2000);
        }
    </script>
</body>
</html>
"""


@app.post("/create-invoice")
async def create_invoice(req: PaymentRequest) -> dict[str, str | int]:
    try:
        receiving_address, usdc_amount = await create_rozo_payment(
            merchant_id=req.service, local_amount=req.amount
        )
        ln_invoice, _, sats_required = await create_ln_payment_for_rozo(
            receiving_address=receiving_address, usd_amount=usdc_amount
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(ln_invoice)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_base64 = base64.b64encode(buf.getvalue()).decode()

        return {"invoice": ln_invoice, "qr_code": qr_base64, "sats": sats_required}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
