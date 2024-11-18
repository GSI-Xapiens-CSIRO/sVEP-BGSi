import {
  AfterViewChecked,
  AfterViewInit,
  Component,
  ElementRef,
  HostListener,
  OnInit,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import {
  trigger,
  state,
  style,
  transition,
  animate,
} from '@angular/animations';
import { FullPageLoaderComponent } from './components/full-page-loader/full-page-loader.component';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    FullPageLoaderComponent,
  ],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss',
  animations: [
    trigger('collapse', [
      state(
        'open',
        style({
          height: '*',
          opacity: 1,
          visibility: 'visible',
        })
      ),
      state(
        'closed',
        style({
          height: '0',
          opacity: 0,
          visibility: 'hidden',
        })
      ),
      transition('open => closed', [animate('0.1s ease-out')]),
      transition('closed => open', [animate('0.1s ease-in')]),
    ]),
  ],
})
export class AppComponent implements OnInit {
  protected title = 'svep-ui';
  protected isCollapsed = false;

  constructor(private el: ElementRef, private auth: AuthService) {}

  ngOnInit(): void {
    this.isCollapsed = this.el.nativeElement.offsetWidth < 768;
  }

  @HostListener('window:resize', ['event'])
  onResize() {
    this.isCollapsed = this.el.nativeElement.offsetWidth < 768;
  }

  async openSbeacon() {
    const { idToken, accessToken, refreshToken } = await this.auth.getIdToken();
    window.open(
      `http://localhost:4200/login-redirect?idToken=${encodeURIComponent(
        idToken
      )}&accessToken=${encodeURIComponent(
        accessToken
      )}&refreshToken=${encodeURIComponent(refreshToken)}`,
      '_blank'
    );

    console.log(
      'Opening sbeacon',
      `http://localhost:4200/login-redirect?idToken=${encodeURIComponent(
        idToken
      )}&accessToken=${encodeURIComponent(
        accessToken
      )}&refreshToken=${encodeURIComponent(refreshToken)}`
    );
  }
}
