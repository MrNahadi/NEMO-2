// Plain-language help shown next to each question. Kept in one place so the user guide can reuse it.
export const HELP = {
  mass:
    "The total weight of what you are lifting, including any lifting frame or spreader beam. If you are not sure, round up.",
  points:
    "How many padeyes the slings attach to. Each padeye gets designed the same.",
  carrying:
    "With 4 lifting points and no spreader beam, the slings rarely share the load evenly. Riggers often assume only 2 carry it. Leave this at the number of lifting points if the load is shared evenly.",
  slingAngle:
    "The angle between each sling and the horizontal. 90° means straight up. Flatter slings pull harder on each padeye, so the padeye gets bigger. Below 45° is usually avoided.",
  material:
    "The plate steel or aluminium the padeye is cut from. S355 is the common structural steel; AH36 is the usual higher-strength ship steel.",
  plates:
    "Tick the plate thicknesses your workshop has or can buy. NEMO only designs with these, so the result can be cut straight away.",
  cheeks:
    "Cheek plates are rings welded either side of the hole to make it thicker without making the whole padeye thick. They save steel on heavier lifts but add welding.",
  category:
    "ASME BTH-1 sorts lifts into two groups. Category B is for uncertain loads or rough conditions, which is usual at sea or on deck, and uses a larger safety factor (3.0). Category A (2.0) is for predictable lifts in good conditions.",
  dynamic:
    "An extra multiplier for jerks and swinging during the lift. ASME BTH-1's safety factor already allows for normal lifting, so leave this at 1.0 unless your lift plan or standard asks for one (for example offshore lifts).",
  side:
    "Slings never line up perfectly with the padeye. This adds a sideways pull as a share of the sling force. 5% is a common allowance.",
  serviceClass:
    "How many times the padeye will be used at full load over its life. Choose 'Up to 20,000 lifts' for most one-off or occasional lifts.",
  fill:
    "A padeye much thinner than the shackle jaw lets the shackle tilt and bends its pin. With this on, NEMO keeps the padeye at least 60% as thick as the jaw.",
} as const;

export const HELP_BRACKET = {
  pipe: "The nominal pipe size and wall thickness. NEMO uses the outside diameter and wall from ASME B36.10M.",
  contents: "What normally fills the pipe. Pick the heaviest case, for example full of sea water during testing.",
  insulation: "Insulation adds weight and pushes the pipe further from the bulkhead.",
  span: "The distance between this support and the next ones along the pipe. Longer spacing means fewer supports but more load on each, and a pipe that vibrates more easily.",
  direction: "Which way the pipe runs on the ship. It decides whether the athwartships or the fore-and-aft acceleration pushes the pipe across the bracket.",
  gap: "Clear space between the bulkhead and the pipe (or its insulation), for welding, painting and fitting the U-bolt nuts.",
  material: "The plate the seat and knees are cut from. Grade A is the usual ship steel for brackets.",
  plates: "Tick the plate thicknesses your workshop has. NEMO only designs with these.",
  continuity: "A pipe running over many supports puts more than one span's weight on some of them. 1.25 covers the worst case of a two-span pipe.",
  friction: "When the ship pitches, the pipe tries to slide along the bracket. Friction passes part of that into the bracket. 0.3 is usual for steel on steel.",
  ubolt: "Galvanised 4.6 steel is the common choice. Use stainless A4-70 on stainless or copper-nickel pipe.",
  accel:
    "Ship motion adds to gravity. Vertical is on top of 1 g of gravity. Take these from the vessel's class rules or design basis: they are larger near the bow and stern and high up. NEMO's starting values are conservative for most places on a ship.",
  propeller: "The propeller shakes the ship once per revolution and once per blade passing. Enter the propeller's service speed and blade count.",
  engine: "The engine shakes the ship at its running speed and at its firing frequency.",
  margin: "How far the pipe's natural frequency must stay from every excitation. 20% is common shipyard practice.",
  deflection: "The most the bracket may bend under the pipe at the design load.",
} as const;

export const HELP_FIN = {
  speed: "The ship's service speed with the fins working. Fin forces grow with the square of the speed.",
  size: "Span is how far the fin sticks out from the hull; chord is its width front to back.",
  thickness: "Foil thickness as a share of the chord. Thicker foils have room for a bigger stock and are stiffer.",
  angle: "The largest angle the fin is turned to. The structure is designed for the lift at this angle and full speed.",
  stock: "Where the stock (the shaft the fin turns on) passes through the foil, measured from the leading edge. Near a third of the chord keeps the twisting moment small.",
  depth: "Depth of the fin below the waterline. Deeper water presses harder, which delays cavitation.",
  draught: "Scantling draught of the ship, used by the rules for the least skin thickness.",
  gap: "Distance from the fin root to the outer stock bearing in the hull. The stock bends most there.",
  material: "The plate for the skin, spars and ribs, and the forging for the stock.",
  spars: "Positions of the front and rear spars (internal walls running along the span), as a share of the chord.",
  deflection: "The most the fin tip may bend at the design load.",
} as const;
