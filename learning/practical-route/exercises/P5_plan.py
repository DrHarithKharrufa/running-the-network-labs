"""Learner starter: pure comparison; do not connect to a device."""
def make_plan(snapshot,desired):
    raise NotImplementedError('Implement P5 using the observed generation')

if __name__=='__main__':
    state={'asset_id':'r1','generation':4,'description':'old'}
    result=make_plan(state,'new')
    assert result['before']=='old' and result['after']=='new'
    assert result['expected_generation']==4 and result['change_required'] is True
    assert state['description']=='old'
    assert make_plan(state,'old')['change_required'] is False
    print('P5 examples passed; add invalid-input checks')
