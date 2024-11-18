import { Component } from '@angular/core';
import {
  FormGroup,
  FormControl,
  Validators,
  ValidatorFn,
  AbstractControl,
  ValidationErrors,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../../src/app/services/auth.service';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';

const passwordsValidator = (): ValidatorFn => {
  return (control: AbstractControl): ValidationErrors | null => {
    const start = control.get('password')!.value;
    const end = control.get('newPassword')!.value;

    if (control.get('newPassword')?.enabled && start === end) {
      control
        .get('newPassword')
        ?.setErrors({ error: 'Password must be different' });
    }

    return null;
  };
};

enum StateTypes {
  ORDINARY_LOGIN = 1,
  FIRST_LOGIN = 2,
  PASSWORD_RESET = 3,
}

/*
 * This component is a state machine, it has states indicated in
 * StateTypes interface. Each UI elements is turned on or off using
 * these states of the state machine
 */
@Component({
  selector: 'app-login-page',
  templateUrl: './login-page.component.html',
  styleUrls: ['./login-page.component.scss'],
  standalone: true,
  imports: [
    MatCardModule,
    FormsModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    RouterLink,
    MatButtonModule,
  ],
})
export class LoginPageComponent {
  protected state = StateTypes.ORDINARY_LOGIN;
  protected StateTypes = StateTypes;
  protected loading = false;

  protected loginForm = new FormGroup(
    {
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [Validators.required]),
      newPassword: new FormControl(
        { value: '', disabled: this.state !== StateTypes.FIRST_LOGIN },
        [Validators.required, Validators.minLength(6)],
      ),
      resetCode: new FormControl(
        { value: '', disabled: this.state !== StateTypes.PASSWORD_RESET },
        [Validators.required],
      ),
    },
    { validators: passwordsValidator() },
  );

  constructor(
    private auth: AuthService,
    private router: Router,
    private sb: MatSnackBar,
  ) {}

  async login() {
    switch (this.state) {
      case StateTypes.FIRST_LOGIN: {
        const success = await this.auth.newPassword(
          this.loginForm.value.newPassword!,
        );
        if (success) {
          this.router.navigate(['/']);
        } else {
          this.sb.open('Something went wrong, please contact admin!', 'Okay', {
            duration: 60000,
          });
        }
        break;
      }
      case StateTypes.PASSWORD_RESET: {
        break;
      }
      case StateTypes.ORDINARY_LOGIN: {
        const success = await this.auth.signIn(
          this.loginForm.value.email!,
          this.loginForm.value.password!,
        );
        switch (success) {
          case true:
            this.router.navigate(['/']);
            break;
          case false:
            this.sb.open('Please recheck username and password!', 'Okay', {
              duration: 60000,
            });
            break;
          case 'NEW_PASSWORD_REQUIRED':
            this.state = StateTypes.FIRST_LOGIN;
            this.loginForm.controls.newPassword.enable();
            break;
        }
        break;
      }
    }
  }
}