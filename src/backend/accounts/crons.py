import random
import string

from django.contrib.auth import get_user_model


def update_referer():
    users = get_user_model().objects.filter(referer_code='')
    for user in users:
        while True:
            letters = string.ascii_uppercase + string.digits
            name = user.first_name.replace(".", "").replace(" ", "")[0:4].upper()
            code = ''.join(random.choice(letters) for _ in range(8 - len(name)))
            refer_code = name + code
            if not get_user_model().objects.filter(referer_code=refer_code).exists():
                user.referer_code = refer_code
                user.save()
                break
    return len(users)
