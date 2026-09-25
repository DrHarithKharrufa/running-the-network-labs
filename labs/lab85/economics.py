"""Chapter 85: invented GBP scenarios, not quotes or accounting advice.
Local arithmetic only. Costs are positive; receipts negative in PV-of-costs.
Annual cash flows occur at year end; index zero is the decision date.
"""
from decimal import Decimal, InvalidOperation, localcontext
import json

def number(value, name='value', minimum=None):
    if isinstance(value, bool): raise ValueError(name)
    try: result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError): raise ValueError(name) from None
    if not result.is_finite() or abs(result)>Decimal('1e18'): raise ValueError(name)
    if minimum is not None and result < Decimal(str(minimum)): raise ValueError(name)
    return result

def present_cost(cashflows, rate):
    values=list(cashflows)
    if not 1 <= len(values) <= 101: raise ValueError('1 to 101 dated cash flows required')
    r=number(rate,'rate',0)
    if r>1: raise ValueError('worksheet supports rates from 0 to 100 percent')
    with localcontext() as ctx:
        ctx.prec=40
        return sum((number(c,'cash flow')/(1+r)**t for t,c in enumerate(values)),Decimal(0))

def own_costs(support_growth=0, extra_capacity=False):
    g=number(support_growth,'support growth',0)
    if g>1 or type(extra_capacity) is not bool: raise ValueError('scenario')
    annual_power=Decimal('1')*8760*Decimal('1.4')*Decimal('0.30')
    flows=[Decimal(140000)]
    for year in range(1,8):
        cost=Decimal(15000)*(1+g)**(year-1)+annual_power+3000+8000
        # Explicit invented growth option: added module at end of year 3,
        # paid support in years 4-7; no change to power/space/operations assumed.
        if extra_capacity and year==3: cost+=100000
        if extra_capacity and year>=4: cost+=15000
        if year==7: cost+=10000-5000
        flows.append(cost)
    return flows

def service_costs(): return [Decimal(10000)]+[Decimal(52000)]*7

def unit_cost(pool, units):
    c=number(pool,'pool',0);u=number(units,'units',0)
    if u==0: raise ValueError('zero denominator')
    return c/u

def support_only(purchase, annual_fraction, years=7):
    if type(years) is not int or not 1<=years<=100: raise ValueError('years')
    p=number(purchase,'purchase',0);f=number(annual_fraction,'support fraction',0)
    if f>1: raise ValueError('fraction')
    return [p]+[p*f]*years

def expected_event_loss(frequency, loss):
    return number(frequency,'events per year',0)*number(loss,'loss per event',0)

def display(value): return str(value.quantize(Decimal('0.01')))

def worksheet():
    own=own_costs();service=service_costs();a=support_only(80000,'.20');b=support_only(110000,'.12')
    event=Decimal(100)*40+3000+2000+1000
    return {
      'scope':'Invented nominal pre-tax GBP, time-zero and end-year cash flows. Local arithmetic; no quote, tax, ledger, outage or vendor execution.',
      'own_cashflows':[str(v) for v in own], 'service_cashflows':[str(v) for v in service],
      'costs_by_rate':{str(r):{'own':display(present_cost(own,r)),'service':display(present_cost(service,r))} for r in [0,'.04','.08','.12']},
      'own_support_3pct_pv_8pct':display(present_cost(own_costs('.03'),'.08')),
      'own_growth_module_pv_8pct':display(present_cost(own_costs(extra_capacity=True),'.08')),
      'checkpoint':{'A_undiscounted':display(sum(a)),'B_undiscounted':display(sum(b)),
        'B_minus_A_undiscounted':display(sum(b)-sum(a)),
        'B_minus_A_pv_8pct':display(present_cost(b,'.08')-present_cost(a,'.08')),
        'annual_other_cash_saving_B_needs_at_8pct':display((present_cost(b,'.08')-present_cost(a,'.08'))/present_cost([0]+[1]*7,'.08'))},
      'units':{'GBP_per_subscriber_month':display(unit_cost(1200000,10000*12)),
        'GBP_per_provisioned_Gbps_month':display(unit_cost(1200000,100*12)),
        'GBP_per_delivered_GB':display(unit_cost(1200000,3000000))},
      'outage':{'event_cost':display(event),'expected_annual_before':display(expected_event_loss('.6',event)),
        'expected_annual_after':display(expected_event_loss('.2',event)),
        'avoided_expected_loss':display(expected_event_loss('.4',event)),
        'programme_cost':display(Decimal(6000)),'net_expected_benefit':display(expected_event_loss('.4',event)-6000)},
      'accounting_bridge':{'purchase_cash':-70000,'annual_support_cash':-5000,'year1_cash':-75000,
        'annual_straight_line_depreciation':10000,'year1_closing_asset':60000,
        'year1_operating_profit_effect':-15000,'year1_EBITDA_effect':-5000,
        'year1_operating_profit_plus_depreciation_minus_capex':-15000+10000-70000}}

if __name__=='__main__': print(json.dumps(worksheet(),indent=2))
