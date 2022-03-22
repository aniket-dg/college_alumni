from django import forms

from users.models import CollegeName


class CollegeForm(forms.ModelForm):
    class Meta:
        model = CollegeName
        fields = ['about_us', 'profile_image', 'phone_number', 'website']


class CollegeBasicInfoForm(forms.ModelForm):
    class Meta:
        model = CollegeName
        fields = ['name', 'about_us', 'phone_number', 'website']
