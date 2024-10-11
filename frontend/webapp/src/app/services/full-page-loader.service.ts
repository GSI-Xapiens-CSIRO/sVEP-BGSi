import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class FullPageLoaderService {
  public isLoading = false;

  constructor() { }

  start() {
    this.isLoading = true;
  }

  end() {
    this.isLoading = false;
  }
}
