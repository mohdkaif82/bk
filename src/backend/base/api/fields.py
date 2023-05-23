from rest_framework.fields import FileField


# django rest framework prevent to read file field from database
# as we upload file it create two copies one to save in database
# another return directly to save performance hit
# as it return file does not have url attribute because it is not coming from db
# so it gives error 'In Memory file upload no attribute url'

# as we dig deep into django rest frameworks file field we get that there
# is use_url attribute , if we set it to false, it prevent accessing
# url attribute

# one solution for this problem is change in rest frameworks library - fields.py
# but that need to be done on every machine so it is not a correct way
# problem was fixed in this commit -
# https://github.com/encode/django-rest-framework/pull/2759#event-263275237
# but if we update version of rest framework it will give problem with other
# methods

# another solution is we have created our own CustomFileField by inheriting
# base FileField and setting use_url as False


class CustomFileField(FileField):
    use_url = False
