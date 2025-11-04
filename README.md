# NS Bitcoin Payments

Lightning Network payment service for Network School cafe and rideshare payments.

## Quick Start

### Web App (Recommended)

Run the FastAPI web interface:

```bash
./run_app.sh
```

Or manually:

```bash
uv run uvicorn app:app --reload
```

Then open your browser to: **http://localhost:8000**

### CLI Usage

```bash
uv run python main.py
```

## Features

- 🌐 Simple web interface for generating Lightning invoices
- ⚡ Instant QR code generation
- 📋 One-click invoice copying
- 🏪 Support for NS Cafe (MYR) and Rideshare (RM) payments
- 🔄 Automatic currency conversion to USD

