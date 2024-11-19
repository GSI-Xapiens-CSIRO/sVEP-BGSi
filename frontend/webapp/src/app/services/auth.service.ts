import { Injectable } from '@angular/core';
import { Auth } from 'aws-amplify';
import { CognitoUser } from 'amazon-cognito-identity-js';
import { BehaviorSubject } from 'rxjs';
import { Router } from '@angular/router';
import _ from 'lodash';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  public user = new BehaviorSubject<CognitoUser | null>(null);
  public userGroups = new BehaviorSubject<Set<string>>(new Set([]));
  private tempUser: any = null;

  constructor(private router: Router) {
    this.refresh();
  }

  async signIn(username: string, password: string) {
    try {
      const user = await Auth.signIn(username, password);

      if (_.get(user, 'challengeName', '') === 'NEW_PASSWORD_REQUIRED') {
        this.tempUser = user;
        return 'NEW_PASSWORD_REQUIRED';
      }
      console.log('Logged in as ', user);
      await this.refresh();
      return true;
    } catch (error) {
      console.log('error signing in', error);
      return false;
    }
  }

  async newPassword(newPassword: string) {
    await Auth.completeNewPassword(this.tempUser, newPassword);
    await this.refresh();
    return true;
  }

  async signOut() {
    await Auth.signOut();
    this.refresh();
    this.router.navigate(['/']);
  }

  async refresh() {
    try {
      const user = await Auth.currentAuthenticatedUser();
      this.userGroups.next(
        new Set(user.signInUserSession.idToken.payload['cognito:groups']),
      );
      this.user.next(user);
      return true;
    } catch (error) {
      this.userGroups.next(new Set([]));
      this.user.next(null);
      return false;
    }
  }

  async forgotPassword(username: string) {
    return await Auth.forgotPassword(username);
  }
}
