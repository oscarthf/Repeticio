# OpenLanguageApp

### About
#### This project is an experimental language web app which utilizes an LLM (currently from OpenAI) to create an entire course in any language. The prompts need some work, both to improve the quality of exercises and to create more targeted exercises to test grammer or special concepts.

## Stack:

```
Django/Gunicorn server hosted using Digital Ocean App Platform
MongoDB Atlas as database
Google login
Stripe payments
OpenAI large language model API
```

## Environment variables needed:

```
LANGUAGE_APP_DB_CONNECTION_STRING=<LANGUAGE_APP_DB_CONNECTION_STRING from MongoDB deployment>
GOOGLE_AUTH_CLIENT_KEY=<GOOGLE_AUTH_CLIENT_KEY>
GOOGLE_AUTH_CLIENT_SECRET=<GOOGLE_AUTH_CLIENT_SECRET>
GOOGLE_AUTH_REDIRECT_URI=<"http://localhost:8000/accounts/google/login/callback/" or using your domain name or IP>
OPENAI_API_KEY=<OPENAI_API_KEY>
STRIPE_PUBLIC_KEY=<STRIPE_PUBLIC_KEY>
STRIPE_SECRET_KEY=<STRIPE_SECRET_KEY>
STRIPE_WEBHOOK_SECRET=<STRIPE_WEBHOOK_SECRET>
STRIPE_PRICE_ID=<STRIPE_PRICE_ID, not product id>
FRONTEND_URL=<STRIPE WEBHOOK FRONTEND_URL>
OPEN_LANGUAGE_APP_DEBUG=<"True" if local, "False" if deployment>
OPEN_LANGUAGE_APP_SECRET_KEY=<OPEN_LANGUAGE_APP_SECRET_KEY>
```

## For Digital Ocean App Platform deployment:

```
0. Clone this repo and generate your own django secret key for your .env file (create a blank text file next to manage.py called .env):
    from django.core.management.utils import get_random_secret_key  
    secret_key = get_random_secret_key()

1. Create app in app platform, link to github.
2. Choose repo and branch.
3. Choose hardware shape for BOTH instances.
4. Set app level env vars (from .env is convenient), not instance level.
5. Build for first time.
6. Set domain name (openlanguageapp.xyz in my case).
```

## To create Stripe Webhook (for subscription payments):

```
0. Create Product with a reacurring payment.
1. Create Webhook for product.
2. Choose the following event types:
    checkout.session.completed
    customer.subscription.deleted
    invoice.payment_failed
    invoice.payment_succeeded
3. Copy your secret key, public key, price id and webhook secret to your .env file
```

## To build with Docker Desktop:

```
0. Clone this repository with the command:
    git clone https://github.com/oscarthf/OpenLanguageApp
1. Follow the steps above to set up your .env file
2. Build the container using the command:
    docker build -t language_app:latest .
3. Run the container using the following command:
    docker run -p 8000:8000 language_app:latest
```