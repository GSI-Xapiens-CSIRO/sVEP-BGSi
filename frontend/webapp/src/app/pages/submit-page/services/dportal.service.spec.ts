import { TestBed } from '@angular/core/testing';

import { DportalService } from './dportal.service';

describe('DportalService', () => {
  let service: DportalService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(DportalService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
