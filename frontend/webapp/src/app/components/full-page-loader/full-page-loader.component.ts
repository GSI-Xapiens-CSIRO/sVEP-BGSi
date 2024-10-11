import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FullPageLoaderService } from '../../services/full-page-loader.service';

@Component({
  selector: 'app-full-page-loader',
  standalone: true,
  imports: [
    CommonModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './full-page-loader.component.html',
  styleUrl: './full-page-loader.component.scss'
})
export class FullPageLoaderComponent {
  constructor(protected ls: FullPageLoaderService) {

  }
}
