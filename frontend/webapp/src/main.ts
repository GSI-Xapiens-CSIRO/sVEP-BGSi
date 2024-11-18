/// <reference types="@angular/localize" />

import { Amplify, Auth } from 'aws-amplify';

import { environment } from './environments/environment';
import { enableProdMode } from '@angular/core';
import { AppComponent } from './app/app.component';

import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';

if (environment.production) {
  enableProdMode();
}

Amplify.configure({
  Auth: environment.auth,
  Storage: {
    AWSS3: {
      bucket: environment.storage.dataPortalBucket,
      region: environment.auth.region,
    },
  },
  API: {
    endpoints: [
      {
        ...environment.api_endpoint_sbeacon,
        // Amplify by default does not add ID TOKEN, it only adds ACCESS TOKEN
        // https://stackoverflow.com/questions/60263497/authenticating-a-rest-api-with-cognito-using-aws-amplify-android
        custom_header: async () => {
          try {
            return {
              Authorization: `Bearer ${(await Auth.currentSession())
                .getIdToken()
                .getJwtToken()}`,
            };
          } catch (error) {
            return {};
          }
        },
      },
    ],
  },
});

bootstrapApplication(AppComponent, appConfig).catch((err) =>
  console.error(err),
);
