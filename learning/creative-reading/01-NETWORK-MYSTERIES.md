# Network mysteries

Twelve finished reader-facing cases. All incidents, measurements and dialogue below are fictional teaching scenarios. The evidence is supplied so the reader can reason without running a lab. Each question is designed for about two minutes of thought, not a measured completion-time claim. Keep the reveal out of view until the reader has made a prediction. Placement and answer keys are in the accompanying files.

## M01 The neighbour nobody could find

**Chapter 5.**

In an isolated Aldergate training exercise using documentation addresses, a workstation has moved into a new subnet. It reaches its default gateway but cannot reach the application at `192.0.2.130`. The application team has already sent an admirably complete screenshot of a green server icon. These are lab addresses, not a change to Aldergate's canonical address plan.

The workstation has address `192.0.2.70` and gateway `192.0.2.66`. The approved plan says `/26`; the workstation says `/24`. Its route lookup treats `192.0.2.130` as directly connected. A capture shows it repeatedly asking for that destination's MAC address. The gateway's neighbour entry is healthy. Proxy ARP is disabled in this scenario.

**Make a prediction:** Is the workstation trying the wrong next hop, or failing to find the right one? With the approved mask, which device's MAC address should it seek? Name one service check you would repeat after correcting the host configuration.

## M02 The name that arrived early

**Chapter 7.**

An engineer tested a new hostname before the record existed. Three minutes later the authoritative server returns the intended address, but the engineer's normal resolver still says that the name does not exist.

The earlier negative answer had a 600-second cache lifetime. Only 180 seconds have elapsed since it was cached; the resolver's negative cache shows 420 seconds remaining. A direct query to the authoritative server returns the new record. An isolated test through a resolver without that cached answer succeeds. These are DNS observations; no application connection has yet been tested.

“The record is there,” says the engineer.

“The resolver remembers when it wasn't,” replies a colleague.

**Make a prediction:** Can both answers be consistent with correct operation? Would shortening the record's current positive TTL shorten this already-cached negative answer? What else must work before you declare the application available?

## M03 The bundle with a favourite chair

**Chapter 12.**

Four 10 Gb/s links form a healthy LAG. One long-lived transfer reaches roughly 9 Gb/s. Its selected member is busy; the other three are quiet. All members are active, counters show no errors, and captures identify one unchanged five-tuple for the transfer. This implementation uses a stable per-flow hash and does not spray that flow across members.

The purchase order describes “40 Gb/s aggregate capacity.” A manager circles the number 40, then the number 9, as though one of them must apologise.

**Make a prediction:** Do the two numbers contradict each other? What would you learn from several independent flows? Why would four flows still not guarantee perfectly even use of all four members?

## M04 The neighbours who stayed polite

**Chapter 18.**

Two OSPF routers on one broadcast segment remain in 2-Way with each other. Their operator is waiting for Full and has begun collecting increasingly ambitious reset commands.

The segment also contains a DR and a BDR. The two routers under investigation are both DROthers. Each is Full with the DR and BDR. Their link-state databases agree for the area, and a defined test prefix is installed and forwards correctly. The intended design is ordinary broadcast OSPF adjacency behaviour, with no special full-mesh feature.

**Make a prediction:** Is their mutual 2-Way state itself a fault? What result would make you investigate further? Write the one sentence that should stop the unnecessary reset.

## M05 The route with nowhere to stand

**Chapter 20.**

Kestrel's BGP session is Established. An update for the laboratory prefix `203.0.113.0/24` is visible in the received-route evidence. Yet no forwarding entry for that prefix appears.

The received path names `10.255.0.9` as its next hop. In the receiving router's relevant routing context, no usable route resolves that next hop. The import policy accepts the prefix. A route to the BGP peer's session address exists, but that address is different from the advertised forwarding next hop. No alternative path exists in this case.

“The messenger got here,” says the on-call engineer. “The directions didn't.”

**Make a prediction:** Why can the session remain healthy while this path is unusable? Which lookup would you inspect next? Is changing next-hop policy automatically the right repair?

## M06 The multicast wrong door

**Chapter 23.**

A receiver has joined the intended multicast group. The source is sending. Packets reach a router on interface A, but the receiver sees none.

For this case, the router's active multicast RPF lookup for the source selects interface B. The relevant multicast state shows the expected receiver-facing outgoing interface. A capture confirms the source and group on interface A; the corresponding RPF-failure counter rises during that capture interval. No other drop mechanism is supplied as part of this exercise.

The packet has found the building. It has used the entrance the building did not expect.

**Make a prediction:** Which consistency check is failing? Why does a successful receiver join not settle that check? What should you compare before touching the receiver?

## M07 The last subscriber at the port counter

**Chapter 31.**

In an isolated CGN allocation exercise, one public IPv4 address has ports 1024 through 65535 available. Each subscriber receives a fixed block of 64 ports. There are no extra exclusions, overlapping assignments or block-sharing mechanisms in this model.

The first 1,008 subscribers receive blocks. Subscriber 1,009 cannot receive one. Established flows belonging to earlier allocations continue to work. The public address has not disappeared, and there is no session-processing failure in the supplied evidence.

“But we still have an address,” someone says.

The allocator would also appreciate somewhere to put the ports.

**Make a prediction:** Reproduce the block count. What exactly is exhausted? Why is watching one existing flow a poor acceptance test for admitting the next subscriber?

## M08 The route that stopped at the chip

**Chapter 37.**

Anvil's SONiC pilot learns a test route. The control-plane route is present and its next hop is resolved. The relevant intended hardware request is visible, but the corresponding hardware entry is absent. The captured SAI programming result reports resource exhaustion for that operation. A packet test for the new route fails; an older route still forwards.

The engineer has three receipts: learned, requested, and attempted. None says delivered.

**Make a prediction:** Where has the supplied evidence placed the failure? Why would another control-plane route display not settle it? Name two things to establish before deciding whether to release resources or change hardware.

## M09 The margin that left before the ribbon cutting

**Chapter 43.**

For a stated optical-budget model, minimum launch power is −5 dBm, required receiver sensitivity is −15 dBm, and the qualified worst-case path loss is 8 dB. The design requires a further 3 dB allowance. Assume the other acceptance conditions, including overload, are separately satisfied; this question concerns only the power budget.

Today's measured launch power is −2 dBm. Someone wants to use that cheerful reading in place of the specified minimum.

**Make a prediction:** How much spare power budget remains using the specified minimum? Does it meet the allowance? What would you tell the person holding the commissioning ribbon?

## M10 The nameserver with the wrong family papers

**Chapter 57.**

A domain has moved to a new DNS operator. Direct authoritative queries return its records. Validating resolvers, however, return failure. In the supplied diagnostic record, the parent still publishes a DS for the old signing key; the new child zone is signed only with a different key. The current parent and child data have been checked after the relevant caches expired. The resolver classifies the answer as bogus.

The new nameserver answers confidently. Its chain of introduction does not match.

**Make a prediction:** Does changing delegation alone complete this signed-zone migration? Which records and signatures need coordinated attention? Why is “turn validation off” a poor way to prove recovery?

## M11 The five packets that escaped the notebook

**Chapter 62.**

For this toy calculation only, a sensor samples each packet independently with probability 1/1000. A short exchange contains five packets. The collector has no sample from it. Assume no additional collection loss; real device sampling schemes need their own model.

An analyst writes, “The exchange did not happen.” Their colleague asks for a smaller pencil.

**Make a prediction:** What is the probability that the sensor samples none of those five packets? Is an empty result surprising? What additional observation would be more useful for establishing whether this particular exchange occurred?

## M12 Four quick repairs and one awkward month

**Chapter 83.**

A fictional service agreement measures availability over a 30-day month, using 43,200 minutes as the denominator. Its target is 99.95%. Four qualifying outages affect the entire measured service for seven minutes each. They do not overlap, and this exercise supplies no exclusions.

The operations report leads with “mean restoration time: seven minutes.” The account manager leads with a raised eyebrow.

**Make a prediction:** What downtime does the target allow? What availability did this month achieve? Can a reassuring mean restoration time establish that the monthly availability target was met?
