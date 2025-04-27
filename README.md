# OpenLanguageApp

### About
#### This project is an experimental language web app which utilizes an LLM (currently from OpenAI) to create an entire course in any language.

## Events for Stripe Webhook (for subscription payments):

```
checkout.session.completed
customer.subscription.deleted
invoice.payment_failed
invoice.payment_succeeded
```

## For .env file:

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
```

## For digital ocean:

```
1. Create app in app platform, link to github.
2. Choose repo and branch.
3. Choose hardware shape for BOTH instances.
4. Set app level env vars, not instance level.
5. Build for first time.
6. Set domain name (openlanguageapp.xyz in my case).
7. Make sure the gunicorn run command is set for both instances (go to Settings, Run Command)
```