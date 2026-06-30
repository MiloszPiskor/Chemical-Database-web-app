import React, { createContext, useContext, useState, useEffect } from "react";
import { oktaAuth } from "./oktaConfig";

const UserContext = createContext();

export const useUser = () => useContext(UserContext);

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchUser = async () => {
      const isAuthenticated = await oktaAuth.isAuthenticated();

      if (!isAuthenticated) {
        setUser(null);
        return;
      }

      try {
        const accessToken = await oktaAuth.getAccessToken();
        const oktaUserInfo = await oktaAuth.getUser(); // From ID token

        setUser({ ...oktaUserInfo, accessToken });

      } catch (err) {
        console.error("Failed to load user", err);
        setUser(null);
      }
    };

    fetchUser();

    const unsubscribe = oktaAuth.authStateManager.subscribe(() => {
      fetchUser();
    });

    return () => unsubscribe();
  }, []);

  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
};
