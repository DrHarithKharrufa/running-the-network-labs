# Transport route: Chapters 43–49

Seven paper sessions connect the physical plant to an accepted service. Every observation and price here is constructed. Use the chapter answers after making your own prediction; use the lab READMEs to decide which parts can actually be executed in your environment.

## 1. The route is longer than the straight line — Chapter 43

An OTDR reports 20,000 m after excluding the launch lead. The documented route before the event contains four closures with 25 m of fibre slack each and a uniform 1% fibre-length excess over cable length. Estimate the route position, then state what survey evidence is still missing. Two directional event-loss estimates are −0.10 dB and +0.50 dB.

Model reasoning: `(20000−100)/1.01 = 19702.97 m`. This does not identify a dig point without accurate records and reference planes. The symmetric-bias average is 0.20 dB; one apparent gain is not optical amplification. Pulse width and instrument recovery limit event resolution. Change the closure count to six: the estimate falls by 49.50 m. Submit a route sketch with uncertainties, a bidirectional measurement plan and a permissions/recovery plan before any intrusive test.

## 2. A link needs both ends of its power window — Chapter 44

Assume minimum launch −3 dBm, maximum launch +1 dBm, receiver sensitivity −14 dBm and maximum receiver input −1 dBm for one specified mode. The path-loss range is 4–8 dB; the design reserves 2 dB on the low-power side.

Worst weak receive power is −11 dBm, giving 3 dB raw sensitivity margin and 1 dB after reserve. Worst strong receive power is −3 dBm, 2 dB below the maximum input. Now reduce minimum path loss to 1 dB: strong receive becomes 0 dBm, beyond the stated maximum. Attenuation may help that case but consumes the weak-signal margin. Submit both inequalities, the reference planes and a test plan. Do not subtract FEC coding gain from physical loss or assume a valid power budget proves OSNR, dispersion and modem compatibility.

## 3. The empty-looking spectrum — Chapter 45

A signal needs 63 GHz and the slot-width granularity is 12.5 GHz. One allocated slot therefore has width index `m=ceil(63/12.5)=6`, or 75 GHz. The 6.25 GHz centre-frequency granularity is a different quantity. At 193.1 THz, the allocated edges are 193.0625 and 193.1375 THz.

Place two such slots without overlap and check the band's edges as well as their centres. Move one centre by a single 6.25 GHz step and recompute. Free aggregate bandwidth does not guarantee a contiguous slot or a viable route through all filters. Submit the slot plan, guard/filter assumptions and path-wide allocation. The teaching arithmetic does not qualify a modem or a ROADM passband.

## 4. Compatible declarations are not a working wavelength — Chapter 46

An invented line system permits 191.3–196.1 THz. A 137.5 GHz allocated slot centred at 191.3 THz is outside its band even though the centre equals the lower limit: its lower edge is 191.23125 THz. Moving the centre to 191.36875 THz puts that edge exactly on the stated boundary, before any additional engineering guard.

Ask separately whether the slot, PSD, channel loading, management integration and path OSNR are acceptable, and whether the end modems implement a qualified common mode. “Not evaluated” is not “passed”. Submit a contract with known, failed and unknown clauses, then a recovery timeline showing who owns transport and IP restoration. Inject an unknown OSNR and a shared power feed; neither should disappear behind the word open.

## 5. Agreeing clocks can agree on the wrong time — Chapter 47

Construct timestamps with a true clock offset of 100 ns, forward delay 1,400 ns and reverse delay 900 ns. The ideal two-way offset estimate is `100+(1400−900)/2 = 350 ns`, biased by 250 ns. Repeating unchanged measurements does not average away that bias.

Submit a reference-plane diagram, source/clock/path error allocation and independent measurement plan. Change only the forward delay to 1,000 ns: the estimate becomes 150 ns. Explain the difference between time, phase and frequency, and between a detected source loss and a plausible false source. Use answer 47.7 for the separate holdover calculation; do not substitute an oscillator temperature specification for measured residual frequency error.

## 6. The split decides what must cross the transport — Chapter 48

For an illustrative uncompressed sample transport, take 30.72 million samples/s, 16-bit I and 16-bit Q, four antenna streams and a stated 25% framing factor. The arithmetic is `30.72e6×32×4×1.25 = 4.9152 Gbit/s`. It is not a universal CPRI/eCPRI or functional-split rate.

Submit the chosen split and exact payload/framing assumptions, plus latency, delay-variation, synchronisation and failure budgets. Double antenna streams: the model rate doubles to 9.8304 Gbit/s before any omitted overhead or reserve. A nominal 10 Gbit/s port alone therefore does not prove acceptable delivery. Change compression or sample rate only when the interface specification and quality requirements support it.

## 7. Two radios, one dependency — Chapter 49

Two independent hypothetical links each have availability 0.99. The ideal parallel result is `1−0.01² = 0.9999`. Add a shared power dependency with availability 0.999, independent of the link-specific failures: the result is `0.999×0.9999 = 0.9989001`. The input independence and probabilities are assumptions, not measurements.

Draw the actual common dependencies: mast, spectrum/interference environment, power, timing, backhaul and maintenance. Then consider adaptive modulation: a surviving link can remain up while carrying less than the protected load. Submit a service-rate acceptance test across the stipulated degradation and recovery conditions. Read current local spectrum conditions for a real installation; this paper session provides no frequency authorisation or RF qualification.

## Review

For each session, retain the initial answer, the changed input, corrected reasoning and remaining uncertainty. Score mechanism/units, evidence/limits, service/recovery and communication/ownership using Appendix G. A paper result may justify the next test; it must not be relabelled as that test's result.
