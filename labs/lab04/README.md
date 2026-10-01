# Lab 4 — Interface evidence and an optical worksheet

The two SR Linux 24.10.1 nodes in `physical.clab.yml` let you inspect interface
state. They do not measure physical fibre loss, hardware FEC or optical power.
The optical cases are labelled synthetic teaching data.

## Interface experiment

On an isolated Linux Containerlab host, deploy and inspect the topology:

```bash
sudo containerlab deploy -t physical.clab.yml
sudo containerlab inspect -t physical.clab.yml
docker exec -it clab-lab04-lon-p-01 sr_cli
```

Record software version, interface configuration and observed state on both
nodes. Keep separate console sessions open:

```text
show version
show interface ethernet-1/1 detail
info from state interface ethernet-1/1 statistics
```

On the far node, disable the lab data interface through a committed change:

```text
enter candidate
set / interface ethernet-1/1 admin-state disable
commit now
```

Observe what both nodes report and record elapsed time. Virtual link state need
not behave like a particular optical PHY. Restore the interface and verify:

```text
enter candidate
set / interface ethernet-1/1 admin-state enable
commit now
```

Record counter deltas over a known interval and traffic load. No real optical
baseline can be derived from these virtual interfaces.

## Power and reach worksheet

Read `optical-cases.json`, predict each result, then run:

```bash
python3 check_budget.py
```

The five cases distinguish sufficient calculated allowance, inadequate margin,
out-of-reach operation, overload, and insufficient long-span power budget. The
script checks the expected decisions. It does not simulate Ethernet or prove
that a real link is qualified. Its minimum-loss assumptions are intentionally
conservative screening values, not measurements of the pictured plant.

For the chapter's 11.8 km diagnostic example:

- Estimated loss: `11.8 × 0.35 + 2 × 0.5 + 2 × 0.1 = 5.33 dB`.
- At synthetic measured Tx −2.0 dBm, predicted Rx is −7.33 dBm.
- Synthetic Rx −9.4 dBm implies 7.40 dB loss: 2.07 dB above the model.
- The span exceeds nominal 10 km LR reach. The current power reading does not
  approve it, and no ageing claim follows without comparable historical data.

Exercise answers used to check arithmetic:

- 8 km LR case: 4.2 dB estimated loss and 2.0 dB headroom above sensitivity.
- Eight splices and 0.75 dB per connector pair: 5.1 dB loss, 1.1 dB headroom.
- 40 km exercise: 13.4 dB estimated loss plus 3 dB allowance = 16.4 dB needed;
  the illustrative ER screening budget is only 11.1 dB.
- Breakout: `(32 − 8) × 4 = 96` downlinks; `96 × 25 / (8 × 100) = 3:1`.
- AP power: `36 × 45 = 1620 W` at the PD, before channel/conversion losses.

For a real authorised hardware test, add exact part numbers and specifications,
both directions, lane/wavelength, temperature, calibration/uncertainty,
reflectance/dispersion constraints, counter intervals and traffic acceptance.

## Validation and cleanup

The arithmetic cases can run on ordinary Python. Device and optical tests are
not claimed as executed during editing. Enter actual results in your lab record.
After preserving the transcript, destroy only this named topology:

```bash
sudo containerlab destroy -t physical.clab.yml
```

## Offline acceptance tests

Run `python3 -m unittest -v test_budget.py`. Twelve tests cover the five retained
synthetic cases, exact thresholds, independent overload checks and worked
arithmetic. Missing, non-finite, Boolean and inconsistent inputs fail instead
of silently becoming a passing screen. Connector and splice counts must be
whole numbers. These are arithmetic tests, not optical or NOS execution.

The chapter power table now names the exact Cisco SR/LR/ER parts and the
1 July 2026 datasheet. Its SFP-10G-SR maximum launch is -1.2 dBm. The retained
LR/ER fixtures are unchanged; no SR fixture is silently substituted. Observe
the cited ER minimum-attenuation and engineered-link conditions separately.
