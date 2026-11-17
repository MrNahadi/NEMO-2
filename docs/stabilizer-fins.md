# Designing a stabilizer fin

A roll-stabilizer fin is a short wing that sticks out from the hull and turns
on a **stock** (a solid shaft) to push the ship upright. NEMO keeps the outer
shape of the fin as you give it and designs the structure inside: the **skin**
plating, two **spars** (walls running along the span), the **ribs** across it,
and the **stock**.

## Step 1: Describe the fin

| Question | What to enter |
| --- | --- |
| Ship speed | Service speed with the fins working, in knots. |
| Fin size | Span (how far it sticks out) and chord (front to back), in metres. |
| Foil thickness | Thickness as a share of the chord, NACA 00 series. 20% is common for fins. |
| Largest fin angle | The most the fin is turned. The structure is designed for full speed at this angle. |
| Stock position | Where the stock passes through the foil, from the leading edge. About a third of the chord keeps the twist small. |
| Depth and draught | Depth of the fin below the waterline (for cavitation) and the ship's scantling draught (for the plating rule). |
| Fin root to the outer stock bearing | The stock bends most where it leaves the hull bearing. |
| Materials and plates | Plate for the skin, spars and ribs, the stock forging, and the plate thicknesses you have. |

## Step 2: Check the assumptions

The spar positions (15% and 65% of the chord by default), the largest tip
deflection, and the design rules. NEMO uses **IACS UR S10** (rudders, Rev.8
2025): a stabilizer fin turns on a stock like a spade rudder.

Under **Advanced settings: going astern and the stock bearings**:

- **Check the stock going astern** (on by default, no input needed). UR S10
  checks rudders astern as well as ahead. The force is smaller, but the centre
  of pressure moves aft to 66% of the chord, so the stock can twist more,
  especially when it sits well forward. Enter the ship's astern speed, or leave
  0 to use the rule's minimum of half the ahead speed.
- **Size the stock bearings** (off by default). Turn on when you know the
  distance between the outer and inner stock bearings and the bearing material.
  NEMO works out the force on each bearing, the bearing length needed to keep
  the pressure within the UR S10 limit, and checks it is no more than 1.2 times
  the bearing diameter. If it would be longer, NEMO makes the stock bigger.

## What NEMO works out

1. **Forces on the fin**, two ways:
   - from published low-aspect-ratio foil data (Whicker and Fehlner, 1958),
     using the hull as a mirror so the effective aspect ratio is twice the
     span over the chord; and
   - from the rudder force formula in IACS UR S10.

   The larger is used. The twisting moment on the stock comes from the force
   acting at a third of the chord.
2. **Pressure on the foil**: NEMO's panel method works out the pressure all
   round the foil section. The suction peak near the nose is compared with the
   cavitation number at the fin's depth. The run screen draws the pressure
   curve and the line where cavitation starts.
3. **Design search**: for every pair of plates (skin, webs) it tries every
   rib spacing from 150 to 1000 mm and sizes the stock to the rules, then keeps
   the lightest fin that passes.
4. **3D model, rib profiles and stress check**. The fin body is a thin box, so
   the stress check is run on the stock and compared with beam theory.

## The checks

| Check | What it means |
| --- | --- |
| Stock twisting / bending and twisting | UR S10.4 limits on the stock, ahead and (by default) astern. Usually the governing check. |
| Outer and inner stock bearing length | Advanced: the least bearing length for the UR S10 surface pressure, against 1.2 times the bearing diameter. |
| Stock fits inside the foil | The stock must fit inside the foil at its position. |
| Fin body bending, spar web shear, skin combined stress | UR S10.5.1 limits on the fin acting as a box beam. |
| Skin plate thickness, web thickness | UR S10.5.2 minimum thicknesses. |
| Skin panel buckling | A skin panel between ribs and spars must not buckle under the bending. |
| Fin tip deflection | How far the tip bends at the design load. |
| Cavitation | Advice: if it fails, the fin will cavitate at full angle and speed. Use a smaller largest angle at top speed. |

## Limits

NEMO does not design the hull structure round the fin, the bearings, the
stock housing or the stock-to-fin connection. The loads are quasi-static:
dynamic fin motion, slamming and fatigue are not covered.

## Checking the stress in Fusion

NEMO's stress check models the stock alone. Section 8 of the calculation
report lists the values for repeating it in Autodesk Fusion from
`fin-stock.step` (**Download files > Stock alone, for a Fusion check**). See
[Using NEMO with Fusion](using-nemo-with-fusion.md#pipe-support-brackets-and-stabilizer-fins).
Fusion has no 42CrMo4, so make the material by hand with the report's values.
