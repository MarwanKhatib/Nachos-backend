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
    list2_genre_id_set = set()
    if isinstance(list2_input, list) and all(isinstance(g, int) for g in list2_input):
        list2_genre_id_set = set(list2_input)
    else: # Assume it's a QuerySet or list of objects with .genre_id
        list2_genre_id_set = {g.genre_id for g in list2_input} # type: ignore

    le = len(list1_genre_ids)
    if le == 0:
        return 0
    
    # Removed aggressive scaling to allow for more granular control in suggestion_manager
    # and rating_processor. This function now returns a raw weighted sum.
    val = 0
    # Assign higher weight to genres appearing earlier in list1 (user's preferred order)
    # For example, if list1 is [G1, G2, G3], G1 gets weight 3, G2 gets 2, G3 gets 1.
    # This makes the score more sensitive to the order of preferred genres.
    for i in range(le):
        current_genre_id = list1_genre_ids[i]
        if current_genre_id in list2_genre_id_set:
            # Weight is (length of list1 - current index)
            val += (le - i)
    return val
