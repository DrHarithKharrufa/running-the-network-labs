#!/usr/bin/env python3
"""Checks for spectrum_plan.py --- two granularities, and the contiguity constraint.

The chapter described flexgrid as 12.5 GHz slices and said a CDC ROADM lets you
put any wavelength anywhere by software. The central checks are that the centre
granularity (6.25 GHz) and the slot granularity (12.5 GHz) are distinct, and
that a legal request into a fibre with ample free spectrum can still have
nowhere to go.

No ROADM, no WSS, no line system, no planning tool.

    python3 test_spectrum_plan.py
"""
import contextlib, io, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import spectrum_plan as sp  # noqa: E402

FAILS, COUNT = [], 0


def check(name, cond, detail=''):
    global COUNT
    COUNT += 1
    detail = str(detail) if detail not in ('', None) else ''
    suffix = ('  [' + detail + ']') if detail else ''
    (print('ok    ' + name + suffix) if cond
     else (FAILS.append(name + suffix), print('FAIL  ' + name + suffix)))


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = fn(*a, **k)
    return r, buf.getvalue()


# ---- TWO GRANULARITIES, AND THEY ARE DIFFERENT ---------------------------
check('the centre granularity is 6.25 GHz', sp.CENTRE_GRANULARITY_GHZ == 6.25)
check('the slot granularity is 12.5 GHz', sp.SLOT_GRANULARITY_GHZ == 12.5)
check('they are not the same number',
      sp.CENTRE_GRANULARITY_GHZ != sp.SLOT_GRANULARITY_GHZ)
check('the slot unit is twice the centre step',
      sp.SLOT_GRANULARITY_GHZ == 2 * sp.CENTRE_GRANULARITY_GHZ)

c0 = sp.channel(0, 4)
c1 = sp.channel(1, 4)
check('n moves the centre by 6.25 GHz, not 12.5',
      abs((c1['centre_ghz'] - c0['centre_ghz']) - 6.25) < 1e-9,
      c1['centre_ghz'] - c0['centre_ghz'])
check('m sets the width in 12.5 GHz units',
      sp.channel(0, 6)['width_ghz'] == 75.0)
check('a channel can be centred between the old 50 GHz positions',
      abs(c1['centre_ghz'] % 50.0) > 1e-9, c1['centre_ghz'])
check('the anchor is 193.1 THz', abs(c0['centre_ghz'] - 193100.0) < 1e-9)
check('n may be negative', sp.channel(-8, 8)['centre_ghz'] < 193100.0)
check('the occupied edges follow from centre and width',
      abs(c0['high_ghz'] - c0['low_ghz'] - c0['width_ghz']) < 1e-9)

# ---- slot widths round up, and the rounding is lost -----------------------
w = sp.slots_for(100.0)
check('100 GHz needs 8 slots', w['m'] == 8, w['m'])
check('...allocating exactly 100 GHz with nothing wasted',
      abs(w['wasted_ghz']) < 1e-9)
w2 = sp.slots_for(62.5)
check('62.5 GHz needs 5 slots', w2['m'] == 5)
w3 = sp.slots_for(63.0)
check('one gigahertz more needs a whole extra slot', w3['m'] == 6, w3['m'])
check('...and wastes almost all of it', w3['wasted_ghz'] > 11, w3['wasted_ghz'])
check('rounding never allocates less than needed',
      all(sp.slots_for(x)['allocated_ghz'] >= x
          for x in (1, 12.4, 12.5, 12.6, 37.5, 99.9, 100.1)))

# ---- THE CONTIGUITY CONSTRAINT -------------------------------------------
s = sp.Spectrum(1000.0)
check('a fresh band is one clean run', s.fragmentation() == 0.0)
check('...of the whole band', s.largest_run_ghz() == 1000.0)
check('placing reduces the free spectrum',
      s.place(4, 'a') == 0 and s.free_ghz() == 950.0, s.free_ghz())
s.place(4, 'b'); s.place(4, 'c')
check('first fit packs from the low edge', sorted(s.occupied)[:1] == [0])
s.release('b')
check('releasing frees the slots back', s.free_ghz() == 900.0, s.free_ghz())
check('...and leaves a hole', s.fragmentation() > 0, s.fragmentation())

# the headline: free spectrum that cannot be used
tiny = sp.Spectrum(200.0)          # 16 slots
for i, lbl in enumerate('abcdefgh'):
    tiny.place(1, lbl, at=i * 2)   # every other slot taken
check('half the band is free', tiny.free_ghz() == 100.0, tiny.free_ghz())
check('...in single-slot pieces', tiny.largest_run_ghz() == 12.5,
      tiny.largest_run_ghz())
check('a 4-slot channel cannot be placed despite the free spectrum',
      tiny.place(4, 'wide') is None)
check('...and a 1-slot channel can', tiny.place(1, 'narrow') is not None)
check('fragmentation reports how bad it is', tiny.fragmentation() > 0.8,
      tiny.fragmentation())

# ---- the worked scenario ---------------------------------------------------
b = sp.build()
ev = b['events']
ask = next(e for e in ev if 'asks for' in e['event'])
after = next(e for e in ev if 'defragmenting' in e['event'])
check('the request is refused', 'NO ROOM' in (ask['result'] or ''), ask['result'])
check('...with plenty of spectrum free', ask['free_ghz'] > 1000,
      ask['free_ghz'])
check('...but the largest run is smaller than the request',
      ask['largest_run_ghz'] < b['want']['needed_ghz'],
      (ask['largest_run_ghz'], b['want']['needed_ghz']))
check('fragmentation is severe at that moment', ask['fragmentation'] > 0.5,
      ask['fragmentation'])
check('defragmenting makes it fit', 'placed at slot' in (after['result'] or ''),
      after['result'])
check('the scenario fills the band before it fragments it',
      min(e['free_ghz'] for e in ev) < 100,
      min(e['free_ghz'] for e in ev))

check('repacked snapshot subtracts the newly placed width',
      after['free_ghz'] == 1550.0, after['free_ghz'])
check('repacked snapshot reports a single remaining run',
      after['largest_run_ghz'] == 1550.0 and after['fragmentation'] == 0.0, after)

# ---- rejection -------------------------------------------------------------
for args, word in (((0.5, 4), 'integer number of 6.25'),
                   ((0, 0), 'positive integer'),
                   ((0, -1), 'positive integer')):
    try:
        sp.channel(*args)
        check('rejects channel%r' % (args,), False, 'no exception')
    except sp.GridError as e:
        check('rejects channel%r' % (args,), word in str(e), str(e)[:50])
for v in (0, -1):
    try:
        sp.slots_for(v)
        check('rejects a width of %r' % v, False, 'no exception')
    except sp.GridError as e:
        check('rejects a width of %r' % v, 'positive' in str(e))
try:
    sp.Spectrum(0)
    check('rejects an empty band', False, 'no exception')
except sp.GridError as e:
    check('rejects an empty band', 'positive' in str(e))
try:
    sp.Spectrum(100.0).place(0, 'x')
    check('rejects a zero-slot placement', False, 'no exception')
except sp.GridError as e:
    check('rejects a zero-slot placement', 'positive integer' in str(e))
try:
    sp.Spectrum(100.0).place(4, 'x', at=6)
    check('rejects a placement off the end', False, 'no exception')
except sp.GridError as e:
    check('rejects a placement off the end', 'outside the band' in str(e))
check('a blocked explicit placement returns None rather than raising',
      (lambda s: (s.place(2, 'a', at=0), s.place(2, 'b', at=1))[1])
      (sp.Spectrum(100.0)) is None)

# ---- the report says what it is and is not -------------------------------
_r, out = quiet(sp.report, sp.analyse())
low = ' '.join(out.lower().split())
check('the report names both granularities',
      'two granularities' in low and '6.25' in low and '12.5' in low)
check('the report says quoting only 12.5 leaves something out',
      'leaves out the step' in low)
check('the report says CDC does not create contiguous spectrum',
      'does not create contiguous' in low)
check('the report names the other links of the path',
      'other links of the path' in low)
check('the report separates static repacking from live migration',
      'no live service was moved' in low and 'qualified migration' in low)
check('the report disclaims equipment', 'no roadm, no wss' in low)
rc, _o = quiet(sp.main, [])
check('the script exits 0', rc == 0, rc)
rc2, _o = quiet(sp.main, ['--json'])
check('--json exits 0', rc2 == 0, rc2)

print('\n%d/%d checks passed' % (COUNT - len(FAILS), COUNT))
if FAILS:
    print('FAILURES:')
    for f in FAILS:
        print('  - ' + f)
sys.exit(1 if FAILS else 0)
