# 🏦 Banking App — Full Stack (Express + Streamlit)

A full-stack banking application with a Node.js/Express/MongoDB backend and a Streamlit Python frontend.

---

## 📁 Project Structure

```
banking_app/
├── backend/               # Node.js + Express + MongoDB
│   ├── server.js
│   ├── package.json
│   ├── .env.example       ← copy to .env and fill in values
│   └── src/
│       ├── app.js
│       ├── config/db.js
│       ├── Models/
│       │   ├── user.model.js
│       │   ├── account.model.js
│       │   ├── ledger.model.js
│       │   └── transactions.models.js
│       ├── controllers/
│       │   ├── auth.controllers.js
│       │   ├── account.controller.js
│       │   └── transaction.controller.js
│       ├── middleware/auth.middleware.js
│       ├── routes/
│       │   ├── auth.routes.js
│       │   ├── account.routes.js
│       │   └── transaction.routes.js
│       └── services/email.service.js
└── frontend/              # Python + Streamlit
    ├── app.py
    └── requirements.txt
```

---

## 🚀 Setup & Run

### 1. Backend

```bash
cd banking_app/backend
cp .env.example .env          # Fill in your MongoDB URI, JWT secret, email creds
npm install
npm run dev                    # Starts on http://localhost:3000
```

### 2. Frontend

```bash
cd banking_app/frontend
pip install -r requirements.txt
streamlit run app.py           # Opens on http://localhost:8501
```

---

## 🔧 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Register a new user |
| POST | `/api/auth/login` | No | Login, get JWT |
| POST | `/api/accounts` | Yes | Open a new bank account |
| GET | `/api/accounts` | Yes | List your accounts + balances |
| GET | `/api/accounts/balance/:accountId` | Yes | Get single account balance |
| GET | `/api/accounts/transactions/:accountId` | Yes | Get account transaction history |
| POST | `/api/transactions` | Yes | Transfer money to another account |
| POST | `/api/transactions/system/initial-funds` | System | Deposit initial funds (system user only) |

---

## 🐛 Bugs Fixed from Original Code

| # | File | Bug | Fix Applied |
|---|------|-----|-------------|
| 1 | `account.model.js` | `const { $where } = require("./user.model")` — invalid destructure import | Removed |
| 2 | `account.model.js` | Unique index on `{user, status}` prevented users from having more than one account | Removed faulty index |
| 3 | `email.service.js` | Exported `sendtransactionEmail` but controller called `sendTransactionEmail` → crash | Renamed to `sendTransactionEmail` |
| 4 | `transaction.controller.js` | `createTransaction` returned 501 (not implemented) | Fully implemented with idempotency, balance check, MongoDB session |
| 5 | `account.controller.js` | No try/catch → unhandled promise rejections crash server | All functions wrapped in try/catch |
| 6 | `user.model.js` | Model registered as `'user'` but `account.model.js` refs `'User'` | Consistent `'User'` capitalization |
| 7 | `auth.controllers.js` | Email sent before response — failure caused unhandled rejection | Made fire-and-forget with `.catch()` |

---

## ✨ Features

- **JWT Authentication** — secure login/register
- **Double-entry Ledger** — all transactions recorded as debit + credit entries
- **Idempotent Transfers** — safe to retry without double-charging
- **MongoDB Transactions** — atomic session-based transfers
- **Email Notifications** — registration + transaction emails via Nodemailer
- **Streamlit Frontend** — dashboard, send money, transaction history with filters
