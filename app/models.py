from enum import Enum
from pydantic import BaseModel

class Objective(str, Enum):
    max_return = "max_return"
    min_risk = "min_risk"
    max_sharpe = "max_sharpe"
    max_return_with_risk = "max_return_with_risk"
    min_risk_with_return = "min_risk_with_return"


class AgeGroup(str, Enum):
    under_30 = "Under 30"
    _30_45 = "30-45"
    _46_60 = "46-60"
    over_60 = "Over 60"

class InvestmentGoal(str, Enum):
    capital_preservation = "Capital preservation"
    income_generation = "Income generation"
    growth = "Growth"
    aggressive_growth = "Aggressive growth"

class LossReaction(str, Enum):
    sell_all = "Sell all investments"
    sell_some = "Sell some investments"
    do_nothing = "Do nothing"
    invest_more = "Invest more"

class InvestmentHorizon(str, Enum):
    less_than_1_year = "Less than 1 year"
    _1_3_years = "1-3 years"
    _3_5_years = "3-5 years"
    more_than_5_years = "More than 5 years"

class QuestionnaireResponse(BaseModel):
    age_group: AgeGroup
    investment_goal: InvestmentGoal
    loss_reaction: LossReaction
    investment_horizon: InvestmentHorizon

