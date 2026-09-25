"""Evaluate synthetic power/reach screening cases, not full PHY acceptance."""
from decimal import Decimal, InvalidOperation
from pathlib import Path
import json

def evaluate(case):
    def d(key):
        value=case[key]
        if isinstance(value,bool) or not isinstance(value,(int,float,str,Decimal)):
            raise ValueError(f'{key} must be a finite decimal number')
        try: result=Decimal(str(value))
        except InvalidOperation as exc: raise ValueError(f'{key} is not numeric') from exc
        if not result.is_finite(): raise ValueError(f'{key} must be finite')
        return result
    nonnegative = ('distance_km','rated_reach_km','loss_db_per_km',
                   'connector_pairs','loss_db_per_pair','splices',
                   'loss_db_per_splice','minimum_loss_db','required_margin_db')
    if any(d(k) < 0 for k in nonnegative):
        raise ValueError('Distances, losses, counts and allowance must be nonnegative')
    for k in ('connector_pairs','splices'):
        if d(k)!=d(k).to_integral_value():raise ValueError(f'{k} must be a whole count')
    if d('rated_reach_km')<=0:raise ValueError('Rated reach must be positive')
    if d('tx_min_dbm') > d('tx_max_dbm') or d('rx_sensitivity_dbm') > d('rx_max_dbm'):
        raise ValueError('Inconsistent power limits')
    loss = d('distance_km')*d('loss_db_per_km') + d('connector_pairs')*d('loss_db_per_pair') + d('splices')*d('loss_db_per_splice')
    if d('minimum_loss_db') > loss:
        raise ValueError('Minimum loss exceeds the assumed maximum loss')
    headroom = d('tx_min_dbm') - loss - d('rx_sensitivity_dbm')
    strongest = d('tx_max_dbm') - d('minimum_loss_db')
    reasons=[]
    if headroom < d('required_margin_db'): reasons.append('insufficient weak-signal allowance')
    if strongest > d('rx_max_dbm'): reasons.append('possible receiver overload')
    if d('distance_km') > d('rated_reach_km'): reasons.append('distance exceeds rated reach')
    return {'name':case['name'],'estimated_max_loss_db':str(loss),
            'headroom_before_allowance_db':str(headroom),
            'strongest_receive_dbm':str(strongest),
            'screen_pass':not reasons,'failure_reasons':reasons}

def main():
    data=json.loads(Path(__file__).with_name('optical-cases.json').read_text(encoding='utf8'))
    results=[]
    for case in data['cases']:
        result=evaluate(case)
        if result['screen_pass'] is not case['expected_screen_pass']:
            raise AssertionError(f'Unexpected result for {case["name"]}')
        results.append(result)
    print(json.dumps({'provenance':data['provenance'],
                      'limitation':'Passing this power/reach screen does not verify channel-loss limits, dispersion, reflectance, BER, hardware support or service acceptance.',
                      'cases':results},indent=2))

if __name__=='__main__':main()
