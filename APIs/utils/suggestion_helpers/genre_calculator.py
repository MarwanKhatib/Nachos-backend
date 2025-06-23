def genres_delta(list1_input, list2_input):
    """
    Calculate the similarity delta between two lists of genres.
    list1_input can be a list of genre IDs (integers) or a QuerySet/list of objects with .genre_id.
    list2_input can be a QuerySet/list of objects with .genre_id.
    """
    # Normalize list1_input to a list of genre IDs, preserving order
    list1_genre_ids = []
    if isinstance(list1_input, list) and all(isinstance(g, int) for g in list1_input):
        list1_genre_ids = list1_input
    else: # Assume it's a QuerySet or list of objects with .genre_id
        list1_genre_ids = [g.genre_id for g in list1_input] # type: ignore

    # Normalize list2_input to a set of genre IDs for efficient lookup
    list2_genre_id_set = {g.genre_id for g in list2_input} # type: ignore

    le = len(list1_genre_ids)
    if le == 0:
        return 0
    
    qu = le * (le + 1) / 2
    tot = 1000 / qu
    val = 0

    for i in range(le):
        current_genre_id = list1_genre_ids[i]
        if current_genre_id in list2_genre_id_set:
            # If a genre from list1 is found in list2, add points.
            # The contribution should be higher for genres earlier in the user's list.
            val += int(((le - i) * tot) + 0.5)
    return val
