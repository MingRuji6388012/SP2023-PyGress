import collections


def absolute_proportions(proportions, count):
    """
    Split a given integer into n parts according to len(proportions) so they sum up to count and
    match the given proportions.

    Args:
        proportions (dict): Dict of proportions, with a identifier as key.

    Returns:
        dict: Dictionary with absolute proportions and same identifiers as key.

    Example::

        >>> absolute_proportions({'train': 0.5, 'test': 0.5}, 100)
        {'train': 50, 'test': 50}
    """

    # first create absolute values by flooring non-integer portions
    relative_sum = sum(proportions.values())
    absolute_proportions = {idx: int(count / relative_sum * prop_value) for idx, prop_value in
                            proportions.items()}

    # Now distribute the rest value randomly over the different parts
    absolute_sum = sum(absolute_proportions.values())
    rest_value = count - absolute_sum
    subset_keys = sorted(list(proportions.keys()))

    for i in range(rest_value):
        key = subset_keys[i % len(subset_keys)]
        absolute_proportions[key] += 1

    return absolute_proportions


def split_identifiers(identifiers=[], proportions={}):
    """
    Split the given identifiers by the given proportions.

    Args:
        identifiers (list): List of identifiers (str).
        proportions (dict): A dictionary containing the proportions with the identifier from the
        input as key.

    Returns:
        dict: Dictionary containing a list of identifiers per part with the same key as the
        proportions dict.

    Example::

        >>> split_identifiers(
        >>>     identifiers=['a', 'b', 'c', 'd'],
        >>>     proportions={'melvin' : 0.5, 'timmy' : 0.5}
        >>> )
        {'melvin' : ['a', 'c'], 'timmy' : ['b', 'd']}
    """

    abs_proportions = absolute_proportions(proportions, len(identifiers))

    parts = {}
    start_index = 0

    for idx, proportion in abs_proportions.items():
        parts[idx] = identifiers[start_index:start_index + proportion]
        start_index += proportion

    return parts


def get_identifiers_splitted_by_weights(identifiers={}, proportions={}):
    """
    Divide the given identifiers based on the given proportions. But instead of randomly split
    the identifiers it is based on category weights. Every identifier has a weight for any
    number of categories. The target is, to split the identifiers in a way, so the sum of
    category k within part x is proportional to the sum of category x over all parts
    according to the given proportions. This is done by greedily insert the identifiers step by
    step in a part which has free space (weight). If there are no fitting parts anymore, the one
    with the least weight exceed is used.

    Args:
        identifiers (dict): A dictionary containing the weights for each identifier (key). Per
                            item a dictionary of weights per category is given.
        proportions (dict): Dict of proportions, with a identifier as key.

    Returns:
        dict: Dictionary containing a list of identifiers per part with the same key as the proportions dict.

    Example::

        >>> identifiers = {
        >>>     'a': {'music': 2, 'speech': 1},
        >>>     'b': {'music': 5, 'speech': 2},
        >>>     'c': {'music': 2, 'speech': 4},
        >>>     'd': {'music': 1, 'speech': 4},
        >>>     'e': {'music': 3, 'speech': 4}
        >>> }
        >>> proportions = {
        >>>     "train" : 0.6,
        >>>     "dev" : 0.2,
        >>>     "test" : 0.2
        >>> }
        >>> get_identifiers_splitted_by_weights(identifiers, proportions)
        {
            'train': ['a', 'b', 'd'],
            'dev': ['c'],
            'test': ['e']
        }
    """

    # Get total weight per category
    sum_per_category = collections.defaultdict(int)

    for identifier, cat_weights in identifiers.items():
        for category, weight in cat_weights.items():
            sum_per_category[category] += weight

    target_weights_per_part = collections.defaultdict(dict)

    # Get target weight for each part and category
    for category, total_weight in sum_per_category.items():
        abs_proportions = absolute_proportions(proportions, total_weight)

        for idx, proportion in abs_proportions.items():
            target_weights_per_part[idx][category] = proportion

    # Distribute items greedily
    part_ids = sorted(list(proportions.keys()))
    current_weights_per_part = {idx: collections.defaultdict(int) for idx in part_ids}
    result = collections.defaultdict(list)

    for identifier in sorted(identifiers.keys()):
        cat_weights = identifiers[identifier]

        target_part = None
        current_part = 0
        weight_over_target = collections.defaultdict(int)

        # Search for fitting part
        while target_part is None and current_part < len(part_ids):
            free_space = True
            part_id = part_ids[current_part]
            part_weights = current_weights_per_part[part_id]

            for category, weight in cat_weights.items():
                target_weight = target_weights_per_part[part_id][category]
                current_weight = part_weights[category]
                weight_diff = current_weight + weight - target_weight
                weight_over_target[part_id] += weight_diff

                if weight_diff > 0:
                    free_space = False

            # If weight doesn't exceed target, place identifier in part
            if free_space:
                target_part = part_id

            current_part += 1

        # If not found fitting part, select the part with the least overweight
        if target_part is None:
            target_part = sorted(weight_over_target.items(), key=lambda x: x[1])[0][0]

        result[target_part].append(identifier)

        for category, weight in cat_weights.items():
            current_weights_per_part[target_part][category] += weight

    return result
