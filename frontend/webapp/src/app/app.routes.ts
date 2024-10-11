import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    loadComponent: () => import('./pages/home-page/home-page.component').then(c => c.HomePageComponent)
  },
  {
    path: 'submit',
    loadComponent: () => import('./pages/submit-page/submit-page.component').then(c => c.SubmitPageComponent)
  },
  {
    path: 'results',
    loadComponent: () => import('./pages/results-page/results-page.component').then(c => c.ResultsPageComponent)
  },
  {
    path: 'results/:url',
    loadComponent: () => import('./pages/results-page/results-page.component').then(c => c.ResultsPageComponent)
  },
  {
    path: 'about',
    loadComponent: () => import('./pages/about-page/about-page.component').then(c => c.AboutPageComponent)
  }
];
