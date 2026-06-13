from collections import Counter


def score_breakdown(dice_values):
    """
    Returns a list of groups that fully explain the score:
        {"values": [...], "combo": "straight"|"pair"|"triple"|"quad"|"quint"|"single", "contribution": int}
    Mirrors calculate_score exactly — sum of contributions == calculate_score(dice_values).
    """
    if not dice_values:
        return []

    counts = Counter(dice_values)
    groups = []
    straight_values = set()

    unique_sorted = sorted(set(dice_values))
    i = 0
    while i < len(unique_sorted):
        j = i
        while j + 1 < len(unique_sorted) and unique_sorted[j + 1] == unique_sorted[j] + 1:
            j += 1
        if j - i >= 2:
            run = unique_sorted[i:j + 1]
            groups.append({"values": list(run), "combo": "straight", "contribution": sum(run) * 10})
            straight_values.update(run)
        i = j + 1

    _NAMES = {2: "pair", 3: "triple", 4: "quad", 5: "quint"}
    for value in sorted(counts.keys()):
        if value in straight_values:
            continue
        count = counts[value]
        if count >= 2:
            groups.append({
                "values": [value] * count,
                "combo": _NAMES.get(count, f"{count}x"),
                "contribution": value * count * count,
            })
        else:
            groups.append({"values": [value], "combo": "single", "contribution": value})

    return groups


def calculate_score(dice_values):
    if not dice_values:
        return 0

    counts = Counter(dice_values)
    total = 0

    # Straight rule: find runs of >= 3 consecutive unique values, order doesn't matter
    unique_sorted = sorted(set(dice_values))
    straight_values = set()
    i = 0
    while i < len(unique_sorted):
        j = i
        while j + 1 < len(unique_sorted) and unique_sorted[j + 1] == unique_sorted[j] + 1:
            j += 1
        if j - i >= 2:  # run of length >= 3
            run = unique_sorted[i:j + 1]
            total += sum(run) * 10
            straight_values.update(run)
        i = j + 1

    # Same-value rule: pairs/triples/etc. (>= 2 dice with same value)
    # Singles not covered by a straight contribute their face value
    for value, count in counts.items():
        if count >= 2:
            total += (value * count) * count
        elif value not in straight_values:
            total += value

    return total
