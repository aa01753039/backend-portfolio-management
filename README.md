# Portafolio managment - backend

Below is an example **README.md** you can adapt for your FastAPI backend application. Feel free to customize it to match your project's specific details and requirements.

---

# FastAPI Backend Application

A **FastAPI** backend application that provides portfolio optimization, risk profiling, and more. This repository contains the source code for the API, including routes for questionnaire-based risk assessments, portfolio optimization, and retrieving historical data.

---

## Table of Contents

1. [Features](#features)  
2. [Project Structure](#project-structure)  
3. [Getting Started](#getting-started)  
4. [Configuration](#configuration)  
5. [Running the App](#running-the-app)  
6. [API Endpoints](#api-endpoints)  
7. [License](#license)

---

## Features

- **Questionnaire-Based Risk Profiling**: Infer a user's risk tolerance and investment horizon via a series of questions.
- **Portfolio Optimization**: Generate an optimal portfolio allocation based on Markowitz's Modern Portfolio Theory (MPT).
- **Value at Risk (VaR)**: Calculate daily, weekly, and yearly VaR using parametric methods.
- **Historical Data Retrieval**: Fetch historical price data from Yahoo Finance (using `yfinance`) and compute changes over time.
- **Flexible Configuration**: Easily adjust risk tolerance, investment term, and objective (e.g., max return, min risk, max Sharpe ratio).

---

## Project Structure

```
.
├── app
│   ├── api
│   │   ├── routes
│   │   │   ├── portfolio.py       # Main portfolio optimization routes
│   │   │   ├── questionnaire.py   # Questionnaire-based risk assessment routes
│   │   └── main.py                # FastAPI application setup
│   ├── core
│   │   └── config.py              # Configuration settings (e.g., environment variables)
│   ├── models
│   │   └── questionnaire.py       # Pydantic models for questionnaire responses
│   └── utils
│       └── helpers.py             # Helper functions (e.g., risk scoring, transformations)
├── requirements.txt               # Python dependencies
├── README.md                      # Project README (you are here)
└── main.py                        # Another entry point if needed (optional)
```

---

## Getting Started

### Prerequisites

- **Python 3.9+** (recommended)
- **Virtual Environment** (optional but recommended)

Clone the repository:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

Create and activate a virtual environment (optional, but recommended):

```bash
# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Configuration

You can store configuration settings (e.g., environment, API keys) in:
- **`.env` file**, or 
- **app/core/config.py** (if you have a custom config class).

Make sure to update any environment variables (e.g., `SENTRY_DSN`, `API_V1_STR`, `BACKEND_CORS_ORIGINS`) to match your setup.

---

## Running the App

Use **uvicorn** to run your FastAPI application in development mode:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

- **`--reload`** automatically restarts the server when code changes.
- **`--host 0.0.0.0`** makes the server accessible externally (e.g., inside Docker containers).
- **`--port 8000`** specifies the port to listen on.

Once the server is running, visit [http://localhost:8000/docs](http://localhost:8000/docs) to view the automatically generated Swagger UI.

---

## API Endpoints

Here are some key endpoints in the application. For a full list, refer to **`/docs`** or **`/redoc`**:

1. **Portfolio Optimization**
   - **GET** `/optimize`  
     **Description**: Optimizes the portfolio based on the specified objective and returns allocations, expected risk/return, and VaR values.  
     **Query Parameters**:  
       - `investment_term` (int): Investment term in days  
       - `objective` (str): Optimization objective (e.g., `max_return`, `min_risk`, `max_sharpe`)  
       - `risk_tolerance` (float, optional): Risk level between 0 and 1  
       - `confidence_level` (float, optional): Confidence level for VaR (default is `0.95`)

2. **Questionnaire-Based Risk Assessment**
   - **POST** `/questionnaire`  
     **Description**: Accepts user responses, infers risk tolerance and investment horizon, then optimizes the portfolio accordingly.  
     **Request Body** (JSON):  
       - `age_group`, `investment_goal`, `loss_reaction`, `investment_horizon`

3. **Historical Data**
   - Returned as part of the **`/optimize`** response or upon specific endpoints.  
   **Description**: Fetches historical price data for default or user-defined tickers, computes absolute and percentage changes.

---

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

