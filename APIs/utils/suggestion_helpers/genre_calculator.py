def genres_delta(list1, list2):
    """
    Calculate the similarity delta between two lists of genres.
    """
    le = max(len(list1), len(list2))
    if le == 0:
        return 0
    qu = le * (le + 1) / 2
    tot = 1000 / qu
    val = 0
    set2 = {genre.genre_id for genre in list2}  # Convert list2 to a set
    for i in range(len(list1)):
        if list1[i] in set2:  # Check for membership in the set
            j = list(set2).index(list1[i])  # Get the index of the genre in list2
            val += int(((le - max(i, j)) * tot) + 0.5)
    return val
