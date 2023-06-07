from django.db import models
from django.conf import settings
# Create your models here.

from ..accounts.models import User


class Room(models.Model):
	name = models.CharField(max_length=30,null=False,blank=False)
	layer = models.CharField(max_length=300)
	admin = models.ForeignKey(User,on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	modified_at = models.DateTimeField(auto_now=True)
	active = models.BooleanField(default=True)


class ActiveUser(models.Model):
	room = models.ForeignKey(Room,on_delete=models.CASCADE)
	user = models.ManyToManyField(User)

	def get_count_of_active_user(self):
		return self.user.count()

	def get_queryset_of_active_user(self,exclude_user=None):
		print("running")
		if exclude_user:
			print("exclude_user")
			return [{'email':user.email,'id':user.id} for user in self.user.all() if user.id!=exclude_user.id ]
		return [ user for user in self.user.all().values('email','id') ]
    	# print("runnnn method called")
    	# if exclude_user:
		# 	print("exclude_user method called")
		# 	return [{'email':user.email,'id':user.id} for user in self.user.all() if user.id!=exclude_user.id ]
		# return [ user for user in self.user.all().values('email','id') ]




class TextMessage(models.Model):
	room = models.ForeignKey(Room,on_delete=models.CASCADE,null=True)
	text = models.CharField(max_length=30,null=True)
	sender = models.ForeignKey(User,on_delete=models.CASCADE, related_name="sender")
	receiver = models.ForeignKey(User,on_delete=models.CASCADE, related_name="receiver")
	datetime = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.text

	#class Meta:
		#unique_together = [['text','datetime'],]
		# constraints = [
        # 	models.UniqueConstraint(fields=['text','datetime'], name='unique appversion')
    	# ]





