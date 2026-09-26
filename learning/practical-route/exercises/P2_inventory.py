"""Learner starter: implement a missing-owner check, then add your own examples."""
def check_owner(row):
    # Return the nonempty owner, or raise ValueError. Do not print inside here.
    raise NotImplementedError('Implement P2 after completing lesson 1')

if __name__=='__main__':
    assert check_owner({'owner':'branch-team'})=='branch-team'
    for value in ('','   '):
        try:check_owner({'owner':value})
        except ValueError:pass
        else:raise AssertionError('empty owner was accepted')
    print('P2 examples passed; add a new example of your own')
