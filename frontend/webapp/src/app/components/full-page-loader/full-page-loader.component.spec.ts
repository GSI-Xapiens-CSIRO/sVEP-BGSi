import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FullPageLoaderComponent } from './full-page-loader.component';

describe('FullPageLoaderComponent', () => {
  let component: FullPageLoaderComponent;
  let fixture: ComponentFixture<FullPageLoaderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FullPageLoaderComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(FullPageLoaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
