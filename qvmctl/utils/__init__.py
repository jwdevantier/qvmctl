from typing import List


def flatten_list(lst: List):
    res = []

    def _flatten(res: List, lst: List):
        for elem in lst:
            if isinstance(elem, list):
                _flatten(res, elem)
            else:
                res.append(elem)

    _flatten(res, lst)
    return res
