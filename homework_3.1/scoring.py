import hashlib
import random
import json


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    """
    Get user's score based on given user fields
    """
    key_parts = [
        first_name or "",
        last_name or "",
        str(phone) or "",
        birthday if birthday else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts).encode('utf-8')).hexdigest()

    # get value from cache
    score = store.cache_get(key) or 0
    if score:
        return float(score)

    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    # set value to cache
    store.cache_set(key, score, 60 * 60)

    return score


def get_interests(store, cid):
    """
    Get user interests
    """
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
