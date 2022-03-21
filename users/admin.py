from django.contrib import admin
from users.models import User, Connection, UserBasic, BranchName, CollegeName, UserEducation, UserInterest

# Register your models here.
admin.site.register(User)
admin.site.register(Connection)
admin.site.register(UserBasic)
admin.site.register(BranchName)
admin.site.register(CollegeName)
admin.site.register(UserEducation)
admin.site.register(UserInterest)
