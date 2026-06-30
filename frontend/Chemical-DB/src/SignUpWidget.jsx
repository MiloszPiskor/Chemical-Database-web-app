// import React, { useEffect } from "react";
// import { SignInWidget } from "@okta/okta-signin-widget";
// import "@okta/okta-signin-widget/dist/css/okta-sign-in.min.css";
// import { OktaAuth } from "@okta/okta-auth-js";

// const SignUpWidget = () => {
//   useEffect(() => {
//     const oktaAuth = new OktaAuth({
//       clientId: import.meta.env.VITE_OKTA_CLIENT_ID,
//       issuer: import.meta.env.VITE_OKTA_ISSUER,
//       redirectUri: window.location.origin + "/login/callback",
//       scopes: ["openid", "profile", "email"],
//       pkce: true,
//     });

//     const widget = new SignInWidget({
//       baseUrl: "https://dev-70026886.okta.com", 
//       clientId: import.meta.env.VITE_OKTA_CLIENT_ID,
//       redirectUri: window.location.origin + "/login/callback",
//       authParams: {
//         pkce: true,
//         scopes: ["openid", "profile", "email"],
//       },
//       features: {
//         registration: true,  // enable self-registration
//       },
//     });

//     widget.renderEl(
//       { el: "#okta-sign-in-container" },
//       () => {
//         console.log("Widget rendered successfully");
//       },
//       (err) => {
//         console.error("Error rendering widget: ", err);
//       }
//     );
//   }, []);

//   return <div id="okta-sign-in-container"></div>;
// };

// export default SignUpWidget;
