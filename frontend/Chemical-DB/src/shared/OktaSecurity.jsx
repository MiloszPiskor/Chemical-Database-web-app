import React from 'react';
import { Security } from '@okta/okta-react';
import { useNavigate } from 'react-router-dom';
import { oktaAuth } from './oktaConfig';

const OktaSecurity = ({ children }) => {
  const navigate = useNavigate();

  const restoreOriginalUri = async (_oktaAuth, originalUri) => {
    console.log("Restore URI:", originalUri); 
    navigate(originalUri || '/', { replace: true });
  };

  return (
    <Security oktaAuth={oktaAuth} restoreOriginalUri={restoreOriginalUri}>
      {children}
    </Security>
  );
};

export default OktaSecurity;
