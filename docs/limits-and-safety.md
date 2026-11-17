# Limits and safety

NEMO is a design aid. It speeds up sizing and checking a padeye. It does not
replace an engineer, a lift plan, or the rules that apply to your vessel or site.

## Before anything is made or used

A competent engineer must review:

- the calculation report;
- the structure the padeye is welded to (deck, bulkhead, beam or frame);
- the lifting arrangement: slings, shackles, angles and the lift plan;
- the welding procedure and inspection.

## What NEMO checks

- The padeye plate around the hole and at its base, using ASME BTH-1.
- The fillet welds at the base and around any cheek plates.
- That the shackle is rated for the load and fits the padeye.
- A built-in stress simulation of the padeye on its own.

## What NEMO does not check

- **The supporting structure.** The deck or member under the padeye must carry the
  same forces. Check it separately.
- **Lamellar tearing.** A thick supporting plate pulled through its thickness can
  split. Use through-thickness (Z-grade) plate where required.
- **Fatigue** beyond the service class you choose.
- **Corrosion.** No corrosion allowance is added. Add one if the padeye stays on
  the vessel.
- **Shackle side loading.** Shackle ratings assume an in-line pull. Follow the
  shackle maker's reduction for side loads.
- **Weld quality.** The checks assume sound welds made to a qualified procedure.
- **Proof load testing** where your lifting standard requires it.

## Design rules

NEMO uses ASME BTH-1 by default. The vessel's classification society (for example
DNV, Bureau Veritas, Lloyd's Register or ABS), the flag state, or the lift
contract can require different rules and give a different answer. The report
names the rules used on its first page.

## Reference data

Material strengths are minimum specified values from the standards named in the
report. Shackle sizes come from the Crosby G-2130 catalogue. If you use different
material or shackles, check the values match.
