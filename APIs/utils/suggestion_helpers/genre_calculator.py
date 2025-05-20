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
    for i in range(len(list1)):
        for j in range(len(list2)):
            if list1[i] == list2[j].genre_id:
                val += int(((le - max(i, j)) * tot) + 0.5)
    return val