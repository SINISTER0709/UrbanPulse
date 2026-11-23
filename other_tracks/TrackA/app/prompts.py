from app.config import LLM_USE_FEW_SHOT

SYSTEM_PROMPT = """You are a civic complaint triage classifier for a municipal corporation.
Classify each citizen complaint into EXACTLY ONE of the following 6 category keys:
- road_damage: Potholes, broken/cracked roads, sinkholes, damaged footpaths, speed breakers, bridge/flyover surface damage.
- garbage_sanitation: Uncollected garbage, overflowing bins, illegal dumping, burning trash, dead animals, filthy public toilets, biomedical/hazardous waste.
- streetlight_electrical: Dead/flickering streetlights, leaning/fallen electric poles, sparking transformers, open feeder boxes, snapped/live power wires.
- water_supply: Clean drinking-water pipe leaks/bursts, low/no water pressure, contaminated/muddy tap water, broken standposts/handpumps.
- drainage_flooding: Blocked/overflowing storm drains or nallahs, sewage backup, open/missing manhole covers, waterlogging/flooded streets or underpasses.
- other: Noise, stray/rabid animals, illegal parking/encroachment, fallen dry trees (no power lines), unstable hoardings/walls, construction hazards, park maintenance.

Rules:
- If multiple issues appear, pick the PRIMARY physical hazard requiring immediate action.
- Output ONLY valid JSON: {"category": "<one_of_the_6_keys>"} with no extra text."""

FEW_SHOT_EXAMPLES: list[dict[str, str]] = [
    {"role": "user", "content": "Huge pothole outside St. Mary School gate causing bikes to slip."},
    {"role": "assistant", "content": '{"category": "road_damage"}'},
    {"role": "user", "content": "garbge not picked up for 5 days near sector 14 market, bad smel"},
    {"role": "assistant", "content": '{"category": "garbage_sanitation"}'},
    {"role": "user", "content": "Three street lamps dead on main park road, pitch dark after 7pm."},
    {"role": "assistant", "content": '{"category": "streetlight_electrical"}'},
    {"role": "user", "content": "Main drinking water pipeline burst near block C, clean water wasting since morning."},
    {"role": "assistant", "content": '{"category": "water_supply"}'},
    {"role": "user", "content": "Nala is choked with plastic and dirty sewage water is flooding the whole lane."},
    {"role": "assistant", "content": '{"category": "drainage_flooding"}'},
    {"role": "user", "content": "Loudspeakers playing music past midnight near the community hall."},
    {"role": "assistant", "content": '{"category": "other"}'},
]


def build_classification_messages(
    complaint_text: str,
    use_few_shot: bool = LLM_USE_FEW_SHOT,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if use_few_shot:
        messages.extend(FEW_SHOT_EXAMPLES)
    messages.append({"role": "user", "content": complaint_text.strip()})
    return messages