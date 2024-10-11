import { TestBed } from '@angular/core/testing';

import { FullPageLoaderService } from './full-page-loader.service';

describe('FullPageLoaderService', () => {
  let service: FullPageLoaderService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FullPageLoaderService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
