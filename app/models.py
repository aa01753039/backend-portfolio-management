from enum import Enum
from pydantic import BaseModel

class Objective(str, Enum):
    max_return = "max_return"
    min_risk = "min_risk"
    max_sharpe = "max_sharpe"
    max_return_with_risk = "max_return_with_risk"
    min_risk_with_return = "min_risk_with_return"


class AgeGroup(str, Enum):
    under_30 = "Menos de 30"
    _30_45 = "30-45"
    _46_60 = "46-60"
    over_60 = "Más de 60"

class InvestmentGoal(str, Enum):
    capital_preservation = "Preservación de capital"
    income_generation = "Generación de ingresos"
    growth = "Crecimiento"
    aggressive_growth = "Crecimiento agresivo"

class LossReaction(str, Enum):
    sell_all = "Vender todas las inversiones"
    sell_some = "Vender algunas inversiones"
    do_nothing = "No hacer nada"
    invest_more = "Invertir más"

class InvestmentHorizon(str, Enum):
    less_than_1_year = "Menos de 1 año"
    _1_3_years = "1-3 años"
    _3_5_years = "3-5 años"
    more_than_5_years = "Más de 5 años"

class QuestionnaireResponse(BaseModel):
    age_group: AgeGroup
    investment_goal: InvestmentGoal
    loss_reaction: LossReaction
    investment_horizon: InvestmentHorizon

