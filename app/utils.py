import json
import os
from datetime import datetime, timedelta

import cvxpy as cp
import numpy as np
import yfinance as yf
from fastapi import HTTPException
from scipy.stats import norm

from app.models import InvestmentHorizon, Objective, QuestionnaireResponse

#read tickers from environment variable

TICKERS = json.loads(os.getenv('TICKERS'))

def calculate_risk_score(response: QuestionnaireResponse) -> int:
    risk_score = 0

    # Age group scoring
    age_group_scores = {"Menos de 30": 4, "30-45": 3, "46-60": 2, "Más de 60": 1}
    risk_score += age_group_scores[response.age_group.value]

    # Investment goal scoring
    investment_goal_scores = {
        "Preservación de capital": 1,
        "Generación de ingresos": 2,
       "Crecimiento": 3,
        "Crecimiento agresivo": 4,
    }
    risk_score += investment_goal_scores[response.investment_goal.value]

    # Loss reaction scoring
    loss_reaction_scores = {
        "Vender todas las inversiones": 1,
        "Vender algunas inversiones": 2,
       "No hacer nada": 3,
        "Invertir más": 4,
    }
    risk_score += loss_reaction_scores[response.loss_reaction.value]

    return risk_score


def determine_investment_term(horizon: InvestmentHorizon) -> int:
    horizon_terms = {
        "Menos de 1 año": 365,
        "1-3 años": 1095,  # 3 years
        "3-5 años": 1825,  # 5 years
        "Más de 5 años": 3650,  # 10 years
    }
    return horizon_terms[horizon.value]


def map_score_to_risk_level(risk_score: int) -> float:
    # Assuming the maximum possible score is 12 (4 questions * 4 max score per question)
    max_score = 12
    # Normalize the risk score to a value between 0 and 1
    risk_level = risk_score / max_score
    return round(risk_level, 2)


def optimize_portfolio_assets(
    expected_returns,
    covariance_matrix,
    objective,
    target_return=None,
    risk_limit=None,
):
    n_assets = len(expected_returns)
    weights = cp.Variable(n_assets)

    # Define risk and return expressions
    portfolio_return = expected_returns.values @ weights
    portfolio_risk = cp.quad_form(weights, covariance_matrix.values)

    # Constraints: Weights sum to 1, no short selling
    constraints = [cp.sum(weights) == 1, weights >= 0]

    if objective == Objective.max_return:
        objective_function = cp.Maximize(portfolio_return)

    elif objective == Objective.min_risk:
        objective_function = cp.Minimize(portfolio_risk)

    elif objective == Objective.max_sharpe:
        # Set a fixed risk level (e.g., portfolio risk <= 1)
        # You can adjust this risk level based on your data scale
        risk_target = 1.0  # Adjust this value as appropriate
        constraints.append(portfolio_risk <= risk_target)
        objective_function = cp.Maximize(portfolio_return)

    elif objective == Objective.max_return_with_risk:
        if risk_limit is None:
            raise ValueError(
                "risk_limit must be provided for max_return_with_risk objective."
            )
        constraints.append(portfolio_risk <= risk_limit)
        objective_function = cp.Maximize(portfolio_return)

    elif objective == Objective.min_risk_with_return:
        if target_return is None:
            raise ValueError(
                "target_return must be provided for min_risk_with_return objective."
            )
        constraints.append(portfolio_return >= target_return)
        objective_function = cp.Minimize(portfolio_risk)

    else:
        raise ValueError("Invalid optimization objective.")

    # Solve the optimization problem
    prob = cp.Problem(objective_function, constraints)
    prob.solve()

    # Check if the optimization was successful
    if prob.status not in ["optimal", "optimal_inaccurate"]:
        raise ValueError(f"Optimization failed. Status: {prob.status}")

    optimal_weights = weights.value
    return optimal_weights


def optimize_portfolio_with_risk_level(risk_level: float, investment_term: int):
    # Set the objective based on risk level
    if risk_level < 0.33:
        objective = Objective.min_risk
    elif risk_level < 0.66:
        objective = Objective.max_sharpe
    else:
        objective = Objective.max_return

    # Fetch historical data based on investment term
    end_date = datetime.now()
    start_date = end_date - timedelta(days=investment_term)
    data = yf.download(
        TICKERS,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
    )["Adj Close"]

    if data.empty:
        raise HTTPException(
            status_code=400, detail="No data fetched for the given investment term."
        )

    # Calculate daily returns, expected returns, and covariance matrix
    returns = data.pct_change().dropna()
    expected_returns = returns.mean()
    covariance_matrix = returns.cov()

    # Optimize the portfolio
    try:
        allocation = optimize_portfolio_assets(
            expected_returns, covariance_matrix, objective, risk_limit=risk_level
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    confidence_level = 0.95
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
        }
