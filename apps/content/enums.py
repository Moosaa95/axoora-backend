from django.db import models


class ArticleCategory(models.TextChoices):
    ENGINEERING = 'Engineering', 'Engineering'
    TECHNOLOGY = 'Technology', 'Technology'
    BUSINESS = 'Business', 'Business'
    GUIDES = 'Guides', 'Guides'
    NEWS = 'News', 'News & Updates'
    PRESS = 'Press', 'Press Releases'
    PRODUCT = 'Product', 'Product Announcements'



class FaqCategory(models.TextChoices):
    GENERAL = 'General', 'General'
    PERSONAL_CARDS = 'Personal & Cards', 'Personal & Cards'
    SAVE_EARN = 'Save and Earn', 'Save and Earn'
    PAYCIRCLE = 'Paycircle', 'Paycircle'
    BUSINESS_POS = 'Business & POS', 'Business & POS'
    SECURITY = 'Security', 'Security'


class ProductCategory(models.TextChoices):
    PERSONAL = 'personal', 'Personal Banking'
    BUSINESS = 'business', 'Business Account'
    POS = 'pos', 'Apex POS Terminal'
    CAPITAL = 'capital', 'Non-Interest Financing'


class ProductStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    BETA = 'beta', 'Beta Access'
    COMING_SOON = 'coming-soon', 'Coming Soon'
