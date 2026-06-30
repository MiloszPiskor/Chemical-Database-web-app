import { OktaAuth } from '@okta/okta-auth-js';

export const oktaAuth = new OktaAuth({
    clientId: import.meta.env.VITE_OKTA_CLIENT_ID,
    issuer: import.meta.env.VITE_OKTA_ISSUER,
    redirectUri: window.location.origin + "/login/callback",
    scopes: ["openid", "profile", "email"],
    pkce: true,
    devMode: false
  });
  
  window.oktaAuth = oktaAuth; // for debugging
