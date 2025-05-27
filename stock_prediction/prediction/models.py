from django.db import models
from django.contrib.auth.models import User

class StockPrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Links to the user
    stock_symbol = models.CharField(max_length=10)# Stock ka naam
    predicted_price = models.FloatField() # Predicted price
    prediction_date = models.DateTimeField(auto_now_add=True)  # Prediction ka time
    confidence_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.stock_symbol} - {self.predicted_price} by {self.user.username}"

class StockHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Optional: Track user requests
    stock_symbol = models.CharField(max_length=10)
    date = models.DateField()
    open_price = models.FloatField()
    high_price = models.FloatField()
    low_price = models.FloatField()
    close_price = models.FloatField()
    volume = models.BigIntegerField()

    def __str__(self):
        return f"{self.stock_symbol} - {self.date}"
    


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

