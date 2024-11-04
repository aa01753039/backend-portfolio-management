# app/api/routes/portfolio.py
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import yfinance as yf
from fastapi import APIRouter, HTTPException, Query
from scipy.stats import norm  # At the top of your file

from app.models import Objective, QuestionnaireResponse
from app.utils import (
    calculate_risk_score,
    determine_investment_term,
    map_score_to_risk_level,
    optimize_portfolio_assets,
    optimize_portfolio_with_risk_level,
)

router = APIRouter()
logging.basicConfig(level=logging.INFO)

# # Set cache location to a directory with appropriate permissions
# yf.set_tz_cache_location("/app/.cache/py-yfinance")

#READ TICKERS FROM ENVIRONMENT VARIABLE

TICKERS = json.loads(os.getenv('TICKERS'))


@router.post("/questionnaire")
def process_questionnaire(response: QuestionnaireResponse):
    """
    Process the questionnaire responses and infer risk level and investment term.
    """
    # Map responses to scores
    risk_score = calculate_risk_score(response)
    investment_term = determine_investment_term(response.investment_horizon)

    # Map total risk score to risk level
    risk_level = map_score_to_risk_level(risk_score)

    # Call the portfolio optimization function
   
    optimization_result = optimize_portfolio_with_risk_level(
        risk_level, investment_term
    )


    return {
        "risk_level": risk_level,
        "investment_term": investment_term,
        "portfolio": optimization_result,
    }

@router.post("/calculator")
def optimize_given_portfolio(
    investment_term: int = Query(..., gt=0, description="Investment term in days"),
    target_return: float = Query(
        None, description="Desired target return (as decimal)"
    ),
    risk_limit: float = Query(
        None, description="Maximum acceptable portfolio risk (variance)"
    ),
    confidence_level: float = Query(
        0.95,
        ge=0.90,
        le=0.99,
        description="Confidence level for VaR (e.g., 0.95 for 95%)",
    ),
    
) -> Any:
    """
    Optimize portfolio based on the specified objective.

    Returns:
    - allocation (dict): Asset allocation percentages.
    - expected_daily_return (float): Expected daily return in percentage.
    - expected_daily_risk (float): Expected daily risk (volatility) in percentage.
    - expected_annual_return (float): Expected annual return in percentage.
    - expected_annual_risk (float): Expected annual risk in percentage.
    - value_at_risk (dict): Value at Risk for daily, weekly, and yearly periods at the specified confidence level.
      - daily_var (float): Daily VaR in percentage.
      - weekly_var (float): Weekly VaR in percentage.
      - yearly_var (float): Yearly VaR in percentage.
    - historical_data (dict): Historical data and change information for each ticker.
    - confidence_level (float): The confidence level used for VaR calculation.
    """
 

    # Determine the start date based on investment term
    end_date = datetime.now()
    start_date = end_date - timedelta(days=investment_term)

    # Fetch historical price data
    data = yf.download(
        TICKERS,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
    )["Adj Close"]

    # Check if data was fetched successfully
    if data.empty:
        raise HTTPException(
            status_code=400, detail="No data fetched for the given investment term."
        )

    # Calculate daily returns
    returns = data.pct_change().dropna()

    # Calculate expected returns and covariance matrix
    expected_returns = returns.mean()
    covariance_matrix = returns.cov()

    if target_return is None and risk_limit is None:
        raise HTTPException(
            status_code=400,
            detail="Either target return or risk limit must be provided.",
        )
    
    if target_return is not None and risk_limit is not None:
        raise HTTPException(
            status_code=400,
            detail="Only one of target return or risk limit can be provided.",
        )
    
    if target_return is not None:
        objective = "min_risk_with_return"
    else:
        objective = "max_return_with_risk"


    # Perform portfolio optimization
    try:
        allocation,result = optimize_portfolio_assets(
            expected_returns,
            covariance_matrix,
            objective,
            target_return,
            risk_limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Prepare the result
    allocation_percentages = {
        ticker: round(weight * 100, 2) for ticker, weight in zip(TICKERS, allocation)
    }

    # Annualize expected portfolio return and risk
    trading_days_per_year = 252  # Approximate number of trading days in a year
    expected_portfolio_return = (
        float(expected_returns.values @ allocation) * trading_days_per_year
    )
    expected_portfolio_risk = float(
        np.sqrt(allocation.T @ covariance_matrix.values @ allocation)
    ) * np.sqrt(trading_days_per_year)

    # Daily expected return and risk
    daily_expected_return = float(expected_returns.values @ allocation)
    daily_expected_risk = float(
        np.sqrt(allocation.T @ covariance_matrix.values @ allocation)
    )

    # VaR Calculations
    # z_score = norm.ppf(confidence_level)

    # # Daily VaR
    # daily_var = -(daily_expected_return - z_score * daily_expected_risk)

    # # Weekly and Yearly VaR
    # trading_days_per_week = 5
    # weekly_var = daily_var * np.sqrt(trading_days_per_week)
    # yearly_var = daily_var * np.sqrt(trading_days_per_year)

    z_score = norm.ppf(confidence_level)

    # Daily VaR (Historical)
    historical_var = np.percentile(returns @ allocation, (1 - confidence_level) * 100)
    
    # If historical returns produce unrealistic VaR values, revert to normal VaR
    daily_var = min(-(daily_expected_return - z_score * daily_expected_risk), -historical_var)

    # Weekly VaR with proper scaling
    trading_days_per_week = 5
    weekly_var = daily_var * np.sqrt(trading_days_per_week)

    # Adjust yearly VaR scaling based on non-iid assumption
    yearly_var = daily_var * np.sqrt(min(trading_days_per_year, investment_term))


    # Historical data and change calculations
    historical_data = {}
    for ticker in TICKERS:
        ticker_data = data[ticker].dropna()
        if not ticker_data.empty:
            first_price = ticker_data.iloc[0]
            last_price = ticker_data.iloc[-1]
            absolute_change = last_price - first_price
            percentage_change = (absolute_change / first_price) * 100

            # Prepare the historical data as a list of dictionaries
            ticker_historical_data = [
                {"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)}
                for date, price in ticker_data.items()
            ]

            historical_data[ticker] = {
                "historical_data": ticker_historical_data,
                "first_price": round(first_price, 2),
                "last_price": round(last_price, 2),
                "absolute_change": round(absolute_change, 2),
                "percentage_change": round(percentage_change, 2),
            }
        else:
            historical_data[ticker] = {
                "error": "No data available for this ticker in the given period."
            }

    correlation_matrix = returns.corr()

    if risk_limit is None:
        risk_limit = result

    return {
        "risk_level": risk_limit,
        "investment_term": investment_term // 365,
        "portfolio": {
        "objective": objective,
        "investment_term_days": investment_term,
        "allocation": allocation_percentages,
        "expected_daily_return": round(daily_expected_return * 100, 2),
        "expected_daily_risk": round(daily_expected_risk * 100, 2),
        "expected_annual_return": round(expected_portfolio_return * 100, 2),
        "expected_annual_risk": round(expected_portfolio_risk * 100, 2),
        "confidence_level": confidence_level,
        "value_at_risk": {
            "daily_var": round(daily_var * 100, 2),
            "weekly_var": round(weekly_var * 100, 2),
            "yearly_var": round(yearly_var * 100, 2),
        },
        "historical_data": historical_data,
        "correlation_matrix": correlation_matrix.to_dict(),
        }
    }


@router.get("/optimize")
def optimize_portfolio(
    investment_term: int = Query(..., gt=0, description="Investment term in days"),
    objective: Objective = Query(..., description="Optimization objective"),
    target_return: float = Query(
        None, description="Desired target return (as decimal)"
    ),
    risk_limit: float = Query(
        None, description="Maximum acceptable portfolio risk (variance)"
    ),
    confidence_level: float = Query(
        0.95,
        ge=0.90,
        le=0.99,
        description="Confidence level for VaR (e.g., 0.95 for 95%)",
    ),
) -> Any:
    """
    Optimize portfolio based on the specified objective.

    Returns:
    - allocation (dict): Asset allocation percentages.
    - expected_daily_return (float): Expected daily return in percentage.
    - expected_daily_risk (float): Expected daily risk (volatility) in percentage.
    - expected_annual_return (float): Expected annual return in percentage.
    - expected_annual_risk (float): Expected annual risk in percentage.
    - value_at_risk (dict): Value at Risk for daily, weekly, and yearly periods at the specified confidence level.
      - daily_var (float): Daily VaR in percentage.
      - weekly_var (float): Weekly VaR in percentage.
      - yearly_var (float): Yearly VaR in percentage.
    - historical_data (dict): Historical data and change information for each ticker.
    - confidence_level (float): The confidence level used for VaR calculation.
    """
 

    # Determine the start date based on investment term
    end_date = datetime.now()
    start_date = end_date - timedelta(days=investment_term)

    # Fetch historical price data
    data = yf.download(
        TICKERS,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
    )["Adj Close"]

    # Check if data was fetched successfully
    if data.empty:
        raise HTTPException(
            status_code=400, detail="No data fetched for the given investment term."
        )

    # Calculate daily returns
    returns = data.pct_change().dropna()

    # Calculate expected returns and covariance matrix
    expected_returns = returns.mean()
    covariance_matrix = returns.cov()

    # Perform portfolio optimization
    try:
        allocation = optimize_portfolio_assets(
            expected_returns,
            covariance_matrix,
            objective,
            target_return,
            risk_limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Prepare the result
    allocation_percentages = {
        ticker: round(weight * 100, 2) for ticker, weight in zip(TICKERS, allocation)
    }

    # Annualize expected portfolio return and risk
    trading_days_per_year = 252  # Approximate number of trading days in a year
    expected_portfolio_return = (
        float(expected_returns.values @ allocation) * trading_days_per_year
    )
    expected_portfolio_risk = float(
        np.sqrt(allocation.T @ covariance_matrix.values @ allocation)
    ) * np.sqrt(trading_days_per_year)

    # Daily expected return and risk
    daily_expected_return = float(expected_returns.values @ allocation)
    daily_expected_risk = float(
        np.sqrt(allocation.T @ covariance_matrix.values @ allocation)
    )

    # VaR Calculations
    # z_score = norm.ppf(confidence_level)

    # # Daily VaR
    # daily_var = -(daily_expected_return - z_score * daily_expected_risk)

    # # Weekly and Yearly VaR
    # trading_days_per_week = 5
    # weekly_var = daily_var * np.sqrt(trading_days_per_week)
    # yearly_var = daily_var * np.sqrt(trading_days_per_year)

    z_score = norm.ppf(confidence_level)

    # Daily VaR (Historical)
    historical_var = np.percentile(returns @ allocation, (1 - confidence_level) * 100)
    
    # If historical returns produce unrealistic VaR values, revert to normal VaR
    daily_var = min(-(daily_expected_return - z_score * daily_expected_risk), -historical_var)

    # Weekly VaR with proper scaling
    trading_days_per_week = 5
    weekly_var = daily_var * np.sqrt(trading_days_per_week)

    # Adjust yearly VaR scaling based on non-iid assumption
    yearly_var = daily_var * np.sqrt(min(trading_days_per_year, investment_term))


    # Historical data and change calculations
    historical_data = {}
    for ticker in TICKERS:
        ticker_data = data[ticker].dropna()
        if not ticker_data.empty:
            first_price = ticker_data.iloc[0]
            last_price = ticker_data.iloc[-1]
            absolute_change = last_price - first_price
            percentage_change = (absolute_change / first_price) * 100

            # Prepare the historical data as a list of dictionaries
            ticker_historical_data = [
                {"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)}
                for date, price in ticker_data.items()
            ]

            historical_data[ticker] = {
                "historical_data": ticker_historical_data,
                "first_price": round(first_price, 2),
                "last_price": round(last_price, 2),
                "absolute_change": round(absolute_change, 2),
                "percentage_change": round(percentage_change, 2),
            }
        else:
            historical_data[ticker] = {
                "error": "No data available for this ticker in the given period."
            }

    correlation_matrix = returns.corr()
    return {
        "objective": objective,
        "investment_term_days": investment_term,
        "allocation": allocation_percentages,
        "expected_daily_return": round(daily_expected_return * 100, 2),
        "expected_daily_risk": round(daily_expected_risk * 100, 2),
        "expected_annual_return": round(expected_portfolio_return * 100, 2),
        "expected_annual_risk": round(expected_portfolio_risk * 100, 2),
        "confidence_level": confidence_level,
        "value_at_risk": {
            "daily_var": round(daily_var * 100, 2),
            "weekly_var": round(weekly_var * 100, 2),
            "yearly_var": round(yearly_var * 100, 2),
        },
        "historical_data": historical_data,
        "correlation_matrix": correlation_matrix.to_dict(),
    }
