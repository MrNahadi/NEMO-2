# Understanding your results

## Use and margin

Every check compares two numbers:

- **Demand**: what the padeye has to carry.
- **Capacity**: the most the design rules allow it to carry, after the safety factor.

**Use** is demand divided by capacity. 60% use means the padeye needs 60% of what
it is allowed, leaving 40% spare. Anything up to 100% passes.

The bar under each check shows its use. It turns red past 100%.

Select a check to see its calculation. Each line gives the quantity, the formula,
the formula with the numbers put in, and the result. Follow it down with a
calculator and you reach the same capacity NEMO used. The PDF report has the same
calculation sheets.

## Pass, Advice and Fail

| Badge | Meaning |
| --- | --- |
| **Pass** | The check is met. |
| **Advice** | Good practice is not met, but the design does not fail because of it. Read the explanation and decide. |
| **Fail** | A required check is not met. NEMO never offers a design with a failed required check. |

## The checks

| Check | What it guards against |
| --- | --- |
| Tearing across the sides of the hole | The plate tearing straight across beside the hole. |
| Splitting above the hole | The material above the hole splitting along the sling line. |
| Shearing out above the hole | The pin pushing a plug of material out of the top of the head. |
| Crushing under the shackle pin | The pin denting the hole surface. |
| Pulling and bending at the base | The padeye bending or pulling away where it meets the deck. |
| Shear at the base | The padeye sliding along its base. |
| Base weld strength | The fillet welds at the base breaking. |
| Cheek plate welds | The welds holding the cheek plates breaking. |
| Shackle is rated for the load | The sling force exceeding the shackle's working load limit. |
| Padeye fits inside the shackle | The padeye being too thick to fit the shackle jaw. |
| Hole is big enough for the pin | The pin not fitting through the hole. |
| Padeye fills the shackle jaw (advice) | A thin padeye letting the shackle tilt and bend its pin. |
| Pin fits the hole closely (advice) | A loose pin concentrating the load. |
| Weld size (advice) | Very small welds on thick plate cracking as they cool. |

The **source** under each check names the rule it comes from. "NEMO practice"
means a common workshop or rigging rule rather than a design-code clause.

## The stress check

NEMO builds a 3D model of the padeye, splits it into small pieces (a mesh), and
calculates the stress everywhere when the full sling force pulls on the hole.

- **Highest stress near the hole**: the largest stress the simulation finds.
  It sits where the pin presses on the hole.
- **Safety factor on yield**: yield strength divided by that stress. Above 1.0
  means no part of the padeye starts to bend permanently.
- **Mesh check**: NEMO runs the simulation at three mesh sizes. If the answer
  barely changes (under 5%), the mesh is fine enough.
- **Force balance**: the support forces must equal the applied load. A large
  error would mean the load was applied wrongly. NEMO shows the error so you can
  see it is tiny.

The design-code checks limit **average** stresses with a safety factor of 2 or 3.
The simulation shows the **peak** at the pin contact, which is always higher than
the average. That is why the simulation's safety factor is lower than the code
factor. What matters is that the peak stays below yield.

## Why three designs?

The lightest design uses its limits fully. A little extra steel buys margin for
things the checks do not cover, such as corrosion, fabrication tolerance or an
unexpected load. Choose the design that suits the job; if unsure, ask the
engineer reviewing it.

## If NEMO cannot find a design

NEMO tells you why. The usual fixes:

- Tick more plate thicknesses, especially thicker ones.
- Allow cheek plates.
- Use more lifting points or a steeper sling angle.
- Choose a stronger material.
