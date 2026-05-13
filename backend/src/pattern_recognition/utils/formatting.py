def unpackage_breakdown_list(breakdown: list) -> list:
    """
    Unpackage the breakdown list to a more readable format.
    """
    unpackaged_breakdown = []
    for item in breakdown:
        if item[0] == "dui":
            unpackaged_breakdown.extend([item[1], item[2]])
        else:
            unpackaged_breakdown.extend([item[1], item[2], item[3]])
    return unpackaged_breakdown
