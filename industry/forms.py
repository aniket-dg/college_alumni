from django import forms

from industry.models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        exclude =  ['user']

class CompanyProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['profile_image']

class CompanyCoverPhotoForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['cover_image']