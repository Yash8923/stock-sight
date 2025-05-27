from django.contrib import admin
from prediction.models import StockHistory,StockPrediction
from .models import ContactMessage

# Register your models here.
class StockHistoryAdmin(admin.ModelAdmin):
    list_display=['user','stock_symbol','date','open_price','high_price','low_price','close_price','volume']
    
class StockPredictionAdmin(admin.ModelAdmin):
    list_display=['user','stock_symbol','predicted_price','prediction_date']
    
admin.site.register(StockHistory,StockHistoryAdmin)
admin.site.register(StockPrediction,StockPredictionAdmin)



@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'timestamp')
    search_fields = ('name', 'email', 'message')
