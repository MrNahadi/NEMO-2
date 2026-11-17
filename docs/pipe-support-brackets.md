# Designing a pipe support bracket

A pipe support bracket holds a pipe run to a bulkhead. NEMO's bracket is a
**seat plate** the pipe rests on, held up by **two triangular knees** under its
edges, all welded to the bulkhead. A **U-bolt** round the pipe stops it lifting
or sliding off sideways.

NEMO sizes the plates, the welds and the U-bolt, and it also checks **the pipe
between the supports**. Most pipe-support failures at sea come from vibration,
so this second check matters as much as the bracket's strength.

## Step 1: Describe the pipe

| Question | What to enter |
| --- | --- |
| Pipe size | The nominal pipe size (NPS) and whether it is standard or extra-strong wall. |
| Pipe material | Carbon steel, stainless 316L or copper-nickel 90/10. |
| What is in the pipe? | The heaviest normal case, for example full of sea water. |
| Insulation | Type and thickness, if the pipe is lagged. |
| Distance to the next supports | The support spacing along the pipe, in metres. |
| Which way does the pipe run? | Fore and aft, or athwartships. It decides which ship motion pushes the pipe across the bracket. |
| Gap between the bulkhead and the pipe | Clear space for welding, painting and the U-bolt nuts. |
| Bracket material and plate thicknesses | The plate the seat and knees are cut from, and the thicknesses your workshop has. |

Under **More about the support** you can change the continuity factor (1.25 by
default; it allows for a continuous pipe putting more than one span's weight on
a support), the friction between pipe and bracket, and the U-bolt material.

## Step 2: Ship motion and vibration

- **Ship-motion accelerations**, in g. Vertical is on top of gravity. NEMO's
  starting values (1.0 g vertical, 0.8 g athwartships, 0.5 g fore and aft) are
  conservative for most places on a ship, but they are not taken from a class
  rule. **Replace them with the values from the vessel's class rules or design
  basis.** Accelerations are higher near the bow and stern and high up.
- **Propeller**: service speed (rpm) and number of blades.
- **Main engine**: speed (rpm), number of cylinders, and 2- or 4-stroke.
- **Frequency margin**: how far the pipe's natural frequency must stay from
  every excitation. 20% is common practice.
- **Largest bracket deflection** under the design load.
- **Design rules**: AISC 360-16 (allowable strength design). ASME BTH-1 is for
  lifting devices, so it is not used for pipe supports.

## What NEMO works out

1. **Forces on the bracket**: the weight per metre of pipe, contents and
   insulation, times the support spacing and the continuity factor, then the
   ship motions on top. The pipe sits on a sliding guide, so along the pipe
   only friction acts.
2. **Pipe span and vibration**: the natural frequency of the pipe between
   supports, compared with the propeller shaft rate, blade rate (and its second
   harmonic), engine speed and engine firing frequency. The run screen shows a
   chart of them with the keep-clear bands shaded. NEMO also gives the
   **longest support spacing** that keeps the pipe within its stress and sag
   limits with its frequency above every excitation.
3. **Design search**: for every pair of plates (seat, knees) it varies the
   knee depth and seat width for the least steel, then picks standard weld
   sizes and the smallest U-bolt that passes.
4. **3D model, cutting profiles and stress check**: as for the padeye. The
   stress result is read away from the bulkhead face, where the fixed edge is a
   modelling singularity, and compared with the hand calculation.

## The checks

| Check | What it means |
| --- | --- |
| Bending along the bracket arm | The seat and knees act as a short beam. NEMO checks 60 sections from the bulkhead to the pipe, because the tapering knees mean the worst one is not always at the bulkhead. |
| Shear in the arm | The vertical force travelling back to the bulkhead. |
| Welds to the bulkhead | All the welds at the bulkhead as one group, with bending and shear combined. |
| Knee-to-seat welds | The welds that make the knees and the seat work as one beam. |
| Seat plate between the knees | The seat spanning between the knees under the pipe or a U-bolt leg. |
| U-bolt legs | Tension and shear in each leg, combined. |
| Bracket deflection | How far the bracket drops under the pipe. |
| Pipe span clear of vibration | The pipe's natural frequency must be at least the margin away from every excitation. If this fails, change the support spacing. |
| Pipe bending between supports | The pipe itself bending between supports. |
| Pipe sag, support spacing, weld sizes, knee free edge | Advice: they do not fail the design on their own. |

If **Pipe span clear of vibration** fails, the bracket can still be strong
enough. Move the supports closer together, or further apart if the frequency
then falls into a gap between excitations, and run again.

## Limits

NEMO does not check the bulkhead the bracket is welded to, pipe anchors,
thermal expansion or water hammer, or weld fatigue. The vibration check
assumes rigid supports; a flexible bracket lowers the pipe's frequency.

## Checking the stress in Fusion

Section 8 of the calculation report lists the values for repeating NEMO's
stress check in Autodesk Fusion from `bracket.step`. See
[Using NEMO with Fusion](using-nemo-with-fusion.md#pipe-support-brackets-and-stabilizer-fins).
Fusion has no Grade A steel, so make the material by hand with the report's
values.
