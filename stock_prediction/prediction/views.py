from django.shortcuts import render,redirect
from django.http import HttpResponse
from datetime import datetime, timedelta
from .utils import fetch_stock_data_for_symbol
import requests,joblib
from django.contrib.auth import authenticate, login as auth_login,logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.models import User
from .forms import LoginForm, SignupForm
from keras.saving import load_model
import yfinance as yf  # Yahoo Finance API se data fetch karne ke liye
import numpy as np
import pandas as pd
import tensorflow as tf
import os
from .models import StockHistory, StockPrediction
from prediction.utils import fetch_stock_data_for_symbol
from sklearn.preprocessing import MinMaxScaler 
from .forms import ContactForm
from prediction.models import ContactMessage

'''# Model ko load karne ke liye
MODEL_PATH = os.path.join(os.path.dirname(__file__), "stock_model.h5")
model = load_model(MODEL_PATH)'''

# Construct model path dynamically
MODEL_PATH = os.path.join(settings.BASE_DIR, "prediction", "models", "stock_prediction_model.h5")
SCALER_PATH = os.path.join(settings.BASE_DIR, "prediction", "models", "scaler.pkl")

# Load the model once at startup
model = load_model(MODEL_PATH, compile=False)
scaler = joblib.load(SCALER_PATH)


# Create your views here.

def home_view(request):
    return render(request, 'prediction/home.html')

def about_view(request):
    return render(request, "prediction/about.html")

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')
        else:
            messages.error(request, "There was an error. Please check your input.")
    else:
        form = ContactForm()

    return render(request, 'prediction/contact.html', {'form': form})

# User Signup

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            # Check if the username or email is already taken
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose a different one.")
                print("❌ User already exists:", username)
            elif User.objects.filter(email=email).exists():
                messages.error(request, "Email is already in use. Try another one.")
                print("❌ Email already exists:", email)
            else:
                # Create and save user
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password1'])  # ✅ Encrypt password
                user.save()

                auth_login(request, user)  # ✅ Log in user after signup
                messages.success(request, "Account created successfully! You are now logged in.")
                print("✅ User created successfully:", username)

                return redirect('home')  # Redirect to home page after signup
        else:
            # Show errors if form validation fails (password mismatch, etc.)
            messages.error(request, "Please correct the errors below.")
            print("❌ Form errors:", form.errors)

    else:
        form = SignupForm()

    return render(request, 'prediction/signup.html', {'form': form})



# User Login
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)

            next_url = request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')  # fallback
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = LoginForm()

    return render(request, 'prediction/login.html', {
        'form': form,
        'next': request.GET.get('next', '')
    })

# User Logout
def logout_view(request):
    auth_logout(request)
    return redirect('home')  # Redirect to login page after logout

# Dashboard to View Past Predictions
from .models import StockPrediction, ContactMessage
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    is_admin = request.user.is_superuser
    user_stocks = StockPrediction.objects.filter(user=request.user).order_by('-prediction_date')
    latest_prediction = user_stocks.first()

    context = {
        'user': request.user,
        'user_stocks': user_stocks,
        'total_predictions': user_stocks.count(),
        'last_stock': latest_prediction.stock_symbol if latest_prediction else "N/A",
        'last_confidence': f"{latest_prediction.confidence_score:.2f}%" if latest_prediction and latest_prediction.confidence_score else "N/A",
        'is_admin': is_admin,
    }

    if is_admin:
        context['all_feedback'] = ContactMessage.objects.all().order_by('-timestamp')

    return render(request, 'prediction/dashboard.html', context)



range_mapping = {
    "30d": 30,
    "60d": 60,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "3y": 1095,
    "5y": 1825,
    "7y": 2555,
}

@login_required
def predict_view(request):
    prediction = None
    stock_data = None
    stock_symbol = ""
    confidence_score = None
    selected_range = "60d"  # Default

    if request.method == "POST":
        stock_symbol = request.POST.get("stock_symbol", "").upper().strip()
        selected_range = request.POST.get("date_range", "60d")

        end_date = datetime.today()
        days = range_mapping.get(selected_range, 60)
        start_date = end_date - timedelta(days=days)

        queryset = StockHistory.objects.filter(
            stock_symbol=stock_symbol,
            date__range=(start_date, end_date)
        ).order_by("date")

        if not queryset.exists():
            df = fetch_stock_data_for_symbol(stock_symbol)
            if df is not None:
                df = df.sort_index()
                df.reset_index(inplace=True)
                df.rename(columns={"index": "date"}, inplace=True)
                for _, row in df.iterrows():
                    StockHistory.objects.get_or_create(
                        stock_symbol=stock_symbol,
                        date=row["date"].date(),
                        defaults={
                            "open_price": row["Open"],
                            "high_price": row["High"],
                            "low_price": row["Low"],
                            "close_price": row["Close"],
                            "volume": int(row["Volume"]),
                        }
                    )
                queryset = StockHistory.objects.filter(
                    stock_symbol=stock_symbol,
                    date__range=(start_date, end_date)
                ).order_by("date")

        if queryset.exists():
            df = pd.DataFrame.from_records(queryset.values("date", "close_price"))
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)

            prices = df["close_price"].values

            if len(prices) < 50:
                prediction = (
                    f"Only {len(prices)} trading days of data available in the selected range "
                    f"('{selected_range}'). At least 50 days are required to make a prediction."
                )
                confidence_score = None
            else:
                scaler = MinMaxScaler()
                scaled_prices = scaler.fit_transform(prices.reshape(-1, 1))
                input_data = scaled_prices[-50:].reshape(1, 50, 1)

                predicted_array = model.predict(input_data)
                predicted_price = scaler.inverse_transform(predicted_array)[0][0]

                std_dev = np.std(prices[-50:])
                confidence = max(0, min(100, 100 - (std_dev / predicted_price * 100))) if predicted_price > 0 else 0
                confidence_score = f"Confidence Score: {confidence:.2f}%"
                prediction = f"Predicted Price for {stock_symbol}: {predicted_price:.2f} INR"

                StockPrediction.objects.create(
                    user=request.user,
                    stock_symbol=stock_symbol,
                    predicted_price=predicted_price,
                    confidence_score=confidence,
                )

            stock_data = {
                "dates": df.index.strftime("%Y-%m-%d").tolist(),
                "prices": prices.tolist(),
            }

        else:
            prediction = "Invalid Stock Symbol or No Data Available"

    return render(request, "prediction/predict.html", {
        "prediction": prediction,
        "confidence": confidence_score,
        "stock_data": stock_data,
        "stock_symbol": stock_symbol,
        "selected_range": selected_range,
    })


@login_required
def get_stock_data(request, stock_symbol):
    print(f"Fetching data for: {stock_symbol}")  # Debugging print

    stock_entry = StockPrediction.objects.filter(
        stock_symbol=stock_symbol,
        user=request.user  # ✅ Fetch only the logged-in user's predictions
    ).order_by('-prediction_date').first()

    if stock_entry:
        response_data = {
            'stock': stock_symbol,
            'date': stock_entry.prediction_date.strftime('%Y-%m-%d %H:%M:%S'),
            'predicted_price': stock_entry.predicted_price
        }
    else:
        response_data = {'error': f'No prediction found for {stock_symbol}'}

    print(response_data)  # Debugging print
    return JsonResponse(response_data)

 

def stock_history_view(request, stock_symbol):
    stock_data = StockHistory.objects.filter(stock_symbol=stock_symbol).order_by("date")
    predicted_data = StockPrediction.objects.filter(stock_symbol=stock_symbol).order_by("prediction_date")

    if not stock_data.exists():
        return render(request, "prediction/no_data.html", {"stock_symbol": stock_symbol})

    return render(request, "prediction/stock_history.html", {
        "stock_data": stock_data,
        "predicted_data": predicted_data
     })