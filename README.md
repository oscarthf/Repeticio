# Repeticio Open Source AI Language App

![screenshots](https://github.com/user-attachments/assets/bd443753-79e6-47b7-9e30-3c1b3ba0de75)

### About
#### This project is an experimental language web app which utilizes an LLM (currently from OpenAI) to create an entire course in any language. The prompts need some work, both to improve the quality of exercises and to create more targeted exercises to test grammer or special concepts.

## Stack:

```
Heroku style django/gunicorn/whitenoise server hosted using Digital Ocean App Platform
MongoDB Atlas as database
Google login
Stripe payments
Google Ads
OpenAI large language model API
```

## To do:

```
* Add AWS deployment instructions.
* Create translations for instructions in UI language.
* Test subscription logic.
* Test main server election logic.
* Improve prompting to reduce bad question generation.
* Allow LLM to check if answer to exercise is not correct (or multiple answers are correct).
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
GOOGLE_ADSENSE_CLIENT_ID=<GOOGLE_ADSENSE_CLIENT_ID>
DJANGO_SECRET_KEY=<DJANGO_SECRET_KEY>
ALLOWED_HOSTS=<leave blank if local, your_domain_name.xyz if deployment>

```

## To create .env file

```
0. Create a blank text file called ".env" with no other extension.
1. Copy the above environment variables and remove the place holders.
2. Follow the steps bellow to obtain the above environment variables.
```

## To create OpenAI API Key:

```
0. Create an OpenAI API account.
1. Load some money into your account, it will rate limit until 5$ have been spent.
2. Navigate to API Keys, create one and copy it into your .env file.
```

## To create Google Login API Credentials (REQUIRED):

```
0. Go to https://console.cloud.google.com/
1. Create a new project or select an existing one.
2. Navigate to APIs & Services > Credentials.
3. Click Create Credentials > OAuth Client.
4. Select Web Application
5. Add your domain name as an authorized origin.
6. Add the following Authorized redirect URIs:
    - http://localhost:8000/social-auth/complete/google-oauth2/
    - <your domain name (with http:// scheme)>/social-auth/complete/google-oauth2/
7. Click "Create" and copy the Client ID and Client Secret into your .env file:
    GOOGLE_AUTH_CLIENT_KEY=<Client ID>
    GOOGLE_AUTH_CLIENT_SECRET=<Client Secret>
```

## To create Google AdSense Credentials:

```
0. Go to https://www.google.com/adsense/start/
1. Sign in with your Google Account and apply for AdSense approval.
2. After approval, go to Ads > By site, and add your domain.
3. Follow instructions to verify site ownership and enable auto ads.
4. Once approved, go to Account > Account information to find your Google AdSense Publisher ID (format: ca-pub-XXXXXXXXXXXXXXXX)
5. Add it to your .env file.

```

## To create a MongoDB Atlas Database:

```
0. Go to cloud.mongodb.com and create a free account.
1. Create a new project.
2. Create a free cluster.
3. After cluster creation, click Connect > Drivers.
4. Choose "Python" and copy the connection string.
5. Add a new database user (username + password) and set permissions.
6. Copy the connection string to your .env file.
7. In Network Access, allow access from your local IP, or the static IP you purchased from DigitalOcean, or (not recomended) from all IP addresses.
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

## To create Django Secret Key:

```
0. Install django locally (many versions should work for this).
1. Generate your own django secret key for your .env file (create a blank text file next to manage.py called .env):
    from django.core.management.utils import get_random_secret_key  
    secret_key = get_random_secret_key()
```

## For Local Deployment (With Docker):

```
0. Clone this repo and enter the project folder using the command:
    git clone https://github.com/oscarthf/OpenLanguageApp
    cd <path/to/OpenLanguageApp>
1. Follow the steps above to set up your .env file
2. Build the container using the command:
    docker build -t language_app:latest .
3. Run the container using the following command:
    docker run -p 8000:8000 language_app:latest
```

## For Local Deployment (No Docker):

```
0. Clone this repo and enter the project folder using the command:
    git clone https://github.com/oscarthf/OpenLanguageApp
    cd <path/to/OpenLanguageApp>
1. Follow the steps above to set up your .env file.
2. Run the following commands to set up the server:
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py collectstatic --noinput
3. Run the following command to start the server:
    python manage.py runserver --insecure 0.0.0.0:8000
```

## For Digital Ocean App Platform deployment:

```
0. Create app in app platform, link to github.
1. Choose repo and branch.
2. Choose hardware shape and port for BOTH instances.
3. Set app level env vars (from .env is convenient), not instance level.
4. Build for first time.
5. Add domain name:
    Enter domain name
    Select "We manage your domain"
    Copy name servers into wherever you got the domain name
    Wait for update, could take a while but probably not hours (they say could take 72 hours)
6 (Recomended). Purchase a static IP and restrict MongoDB access to this IP.
```
